$ErrorActionPreference = 'Stop'

$backendDirectory = Join-Path $PSScriptRoot '..\backend'
$projectDirectory = Join-Path $PSScriptRoot '..'
$artifactPath = Join-Path $projectDirectory 'models\active-model.joblib'
$healthUrl = 'http://127.0.0.1:8000/api/v1/health'

function Test-ApiServer {
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (Test-ApiServer) { exit 0 }
if (-not (Test-Path -LiteralPath $artifactPath)) {
    throw "No trained model artifact exists. Run 'python -m app.ml.train' from the backend directory before starting GlucoCare."
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
$apiProcess = Start-Process -FilePath $python -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' -WorkingDirectory $backendDirectory -WindowStyle Hidden -PassThru

for ($attempt = 0; $attempt -lt 40; $attempt++) {
    if (Test-ApiServer) { exit 0 }
    if ($apiProcess.HasExited) {
        throw "The API stopped before it was ready (exit code $($apiProcess.ExitCode)). Run 'python -m uvicorn app.main:app --reload' from backend to see its output."
    }
    Start-Sleep -Milliseconds 500
}

throw 'The API did not become available at http://127.0.0.1:8000 within 20 seconds.'
