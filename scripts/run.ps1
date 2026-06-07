param(
    [ValidateSet("train", "verify", "api", "full")]
    [string]$Command = "full"
)

$ProjectRoot = Split-Path $PSScriptRoot -Parent

function Build-Go {
    Write-Host "[BUILD] Building Go packet capture..." -ForegroundColor Green
    Push-Location "$ProjectRoot\go-pcap"
    go mod tidy; go build -o "$ProjectRoot\bin\ids-pcap.exe" .
    Pop-Location
}

function Train-ML {
    Write-Host "[TRAIN] Training ML models..." -ForegroundColor Green
    Push-Location "$ProjectRoot\python-ml"
    py main.py train
    Pop-Location
}

function Run-Verify {
    Write-Host "[VERIFY] Running verification script..." -ForegroundColor Green
    Push-Location "$ProjectRoot\python-ml"
    py verify.py
    Pop-Location
}

function Start-API {
    Write-Host "[API] Starting FastAPI server on port 8000..." -ForegroundColor Green
    Push-Location "$ProjectRoot\python-ml"
    py main.py api --host 0.0.0.0 --port 8000
    Pop-Location
}

switch ($Command) {
    "train" { Train-ML }
    "verify" { Run-Verify }
    "api" { Start-API }
    "full" { Train-ML; Run-Verify; Start-API }
}
