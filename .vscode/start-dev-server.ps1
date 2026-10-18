$ErrorActionPreference = 'Stop'

$frontendDirectory = Join-Path $PSScriptRoot '..\frontend'
$url = 'http://127.0.0.1:5173'

function Test-FrontendServer {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -eq 200 -and $response.Content -match '/src/main.tsx'
    } catch {
        return $false
    }
}

if (Test-FrontendServer) {
    exit 0
}

$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$viteProcess = Start-Process -FilePath $npm -ArgumentList 'run', 'dev' -WorkingDirectory $frontendDirectory -WindowStyle Hidden -PassThru

for ($attempt = 0; $attempt -lt 40; $attempt++) {
    if (Test-FrontendServer) {
        exit 0
    }

    if ($viteProcess.HasExited) {
        throw "Vite stopped before it was ready (exit code $($viteProcess.ExitCode)). Run 'npm run dev' from frontend to see its output."
    }

    Start-Sleep -Milliseconds 500
}

throw 'Vite did not become available at http://127.0.0.1:5173 within 20 seconds.'
