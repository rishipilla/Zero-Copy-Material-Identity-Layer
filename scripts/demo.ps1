param(
    [switch]$SkipSampleImport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendRoot = Join-Path $repoRoot 'backend'
$frontendRoot = Join-Path $repoRoot 'frontend'

$backendUrl = 'http://127.0.0.1:8000'
$frontendUrl = 'http://127.0.0.1:5173'
$swaggerUrl = 'http://127.0.0.1:8000/docs'
$neo4jBrowserUrl = 'http://127.0.0.1:7474'

function Write-Info([string]$msg) {
    Write-Host "[demo] $msg" -ForegroundColor Cyan
}

function Write-Success([string]$msg) {
    Write-Host "[demo] $msg" -ForegroundColor Green
}

function Fail([string]$msg) {
    Write-Host "[demo] ERROR: $msg" -ForegroundColor Red
    exit 1
}

function Check-Command([string]$name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Fail "Required command '$name' was not found on PATH. Install it or activate the existing environment before running this demo."
    }
}

function Test-Port([string]$serverHost, [int]$serverPort) {
    try {
        $connection = Test-NetConnection -ComputerName $serverHost -Port $serverPort -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Wait-Port([string]$serverHost, [int]$serverPort, [string]$name, [int]$timeoutSeconds = 90) {
    Write-Info ("Waiting for " + $name + " on " + $serverHost + ":" + $serverPort + "...")
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $timeoutSeconds) {
        if (Test-Port -serverHost $serverHost -serverPort $serverPort) {
            Write-Success ($name + " is reachable on " + $serverHost + ":" + $serverPort + ".")
            return
        }
        Start-Sleep -Seconds 2
    }
    Fail ($name + " did not become reachable at " + $serverHost + ":" + $serverPort + " within " + $timeoutSeconds + " seconds.")
}

function Wait-HTTP([string]$url, [string]$name, [int]$timeoutSeconds = 90) {
    Write-Info ("Waiting for " + $name + " at " + $url + "...")
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $timeoutSeconds) {
        try {
            $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.status -eq 'ok') {
                Write-Success ($name + " responded successfully.")
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    Fail ($name + " did not report health at " + $url + " within " + $timeoutSeconds + " seconds.")
}

Write-Info ("Repository root: " + $repoRoot)

Check-Command 'docker'
Check-Command 'python'
Check-Command 'npm'

$dockerComposeWorks = $false
try {
    & docker compose version *> $null
    if ($LASTEXITCODE -eq 0) { $dockerComposeWorks = $true }
} catch {
    $dockerComposeWorks = $false
}

if (-not $dockerComposeWorks) {
    Fail 'Docker Compose v2 is required. Please install/start Docker Desktop (or enable the compose plugin) and rerun this script.'
}

if (-not (Test-Path (Join-Path $backendRoot 'requirements.txt'))) {
    Fail "Backend requirements file was not found at $backendRoot. This demo expects the repository's current backend layout."
}

if (-not (Test-Path (Join-Path $frontendRoot 'package.json'))) {
    Fail "Frontend package.json was not found at $frontendRoot."
}

$postgresRunning = Test-Port -serverHost '127.0.0.1' -serverPort 5432
$neo4jBrowserRunning = Test-Port -serverHost '127.0.0.1' -serverPort 7474
$neo4jBoltRunning = Test-Port -serverHost '127.0.0.1' -serverPort 7687

if ($postgresRunning -and $neo4jBrowserRunning -and $neo4jBoltRunning) {
    Write-Info 'PostgreSQL and Neo4j ports are already occupied. The demo will assume existing infrastructure is already running there and will not run docker compose up again.'
} else {
    Write-Info 'Starting PostgreSQL and Neo4j from docker-compose.yml...'
    Push-Location $repoRoot
    try {
        & docker compose up -d postgres neo4j
        if ($LASTEXITCODE -ne 0) {
            Fail 'Docker Compose could not start the required PostgreSQL and Neo4j services. Check Docker Desktop and the repository compose file.'
        }
    } finally {
        Pop-Location
    }
}

Wait-Port -serverHost '127.0.0.1' -serverPort 5432 -name 'PostgreSQL'
Wait-Port -serverHost '127.0.0.1' -serverPort 7474 -name 'Neo4j Browser'
Wait-Port -serverHost '127.0.0.1' -serverPort 7687 -name 'Neo4j Bolt'

if (Test-Port -serverHost '127.0.0.1' -serverPort 8000) {
    Write-Info 'Backend port 8000 is already occupied. The script will assume a backend may already be running there and will not start a duplicate uvicorn process.'
} else {
    Write-Info 'Starting the backend locally with uvicorn app.main:app on http://127.0.0.1:8000...'
    Push-Location $backendRoot
    try {
        $backendProcess = Start-Process -FilePath 'python' -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backendRoot -PassThru -NoNewWindow
        Write-Success ("Backend process started with PID " + $backendProcess.Id + ".")
    } catch {
        Fail 'Backend failed to start. Check the existing Python environment, backend dependencies, and the uvicorn command defined in the repository.'
    } finally {
        Pop-Location
    }
}

Wait-HTTP -url ($backendUrl + '/api/health') -name 'Backend health'

if (-not $SkipSampleImport) {
    Write-Info 'Preparing the safe, idempotent demo sample import via the existing API endpoint...'
    try {
        $sampleResponse = Invoke-RestMethod -Uri ($backendUrl + '/api/materials/import-sample') -Method Post -ContentType 'application/json' -ErrorAction Stop
        Write-Success ("Sample import endpoint returned " + $sampleResponse.Count + " import summary objects.")
    } catch {
        Write-Info 'The sample import endpoint could not be reached automatically yet. It is safe and idempotent by design, but the backend may still be warming up. Invoke POST /api/materials/import-sample manually after health is green.'
    }
} else {
    Write-Info 'Skipping automatic sample import because -SkipSampleImport was requested.'
}

if (Test-Port -serverHost '127.0.0.1' -serverPort 5173) {
    Write-Info 'Frontend port 5173 is already occupied. The script will assume a frontend may already be running there and will not start another Vite process.'
} else {
    Write-Info 'Starting the frontend locally with npm run dev from the frontend workspace...'
    Push-Location $frontendRoot
    try {
        $frontendProcess = Start-Process -FilePath 'npm.cmd' -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1') -WorkingDirectory $frontendRoot -PassThru -NoNewWindow
        Write-Success ("Frontend process started with PID " + $frontendProcess.Id + ".")
    } catch {
        Fail 'Frontend failed to start. Check that npm and the frontend dependencies are installed for package.json existing dev command.'
    } finally {
        Pop-Location
    }
}

Wait-Port -serverHost '127.0.0.1' -serverPort 5173 -name 'Frontend Vite dev server'

Write-Host ''
Write-Success 'Demo stack is ready.'
Write-Host 'URLs:' -ForegroundColor Yellow
Write-Host ("  Frontend:       " + $frontendUrl) -ForegroundColor Yellow
Write-Host ("  Backend:        " + $backendUrl) -ForegroundColor Yellow
Write-Host ("  API docs:      " + $swaggerUrl) -ForegroundColor Yellow
Write-Host ("  Neo4j browser: " + $neo4jBrowserUrl) -ForegroundColor Yellow
Write-Host ''
Write-Host 'Stop the demo by closing the backend/frontend shell windows or stopping the uvicorn and npm processes in Task Manager.' -ForegroundColor DarkGray
Write-Host 'This script never resets the database or deletes materials, matches, or identities. It only starts the existing docker services and optionally calls the repository-safe sample import API.' -ForegroundColor DarkGray
