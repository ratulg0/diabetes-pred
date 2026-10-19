$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'start-api-server.ps1')
& (Join-Path $PSScriptRoot 'start-dev-server.ps1')
