$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$flet = Join-Path $projectRoot ".venv\Scripts\flet.exe"

$requiredVariables = @(
    "FLET_ANDROID_SIGNING_KEY_STORE",
    "FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD",
    "FLET_ANDROID_SIGNING_KEY_PASSWORD"
)

foreach ($variable in $requiredVariables) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($variable))) {
        throw "Defina a variável $variable antes de gerar o pacote da Play Store."
    }
}

if (-not (Test-Path -LiteralPath $env:FLET_ANDROID_SIGNING_KEY_STORE -PathType Leaf)) {
    throw "A chave de upload informada não foi encontrada."
}

if ([string]::IsNullOrWhiteSpace($env:FLET_ANDROID_SIGNING_KEY_ALIAS)) {
    $env:FLET_ANDROID_SIGNING_KEY_ALIAS = "upload"
}

if (-not (Test-Path -LiteralPath $flet -PathType Leaf)) {
    throw "O ambiente do projeto não foi encontrado. Execute a instalação das dependências primeiro."
}

$env:PYTHONUTF8 = "1"
$env:JAVA_HOME = "C:\Users\Admin\java\17.0.13+11"
$env:ANDROID_HOME = "C:\Users\Admin\Android\sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:PATH = "C:\Users\Admin\flutter\3.44.8\bin;$env:JAVA_HOME\bin;$env:PATH"

Push-Location $projectRoot
try {
    & $flet build aab
    if ($LASTEXITCODE -ne 0) {
        throw "A compilação do AAB falhou."
    }

    $source = Join-Path $projectRoot "build\aab\rank-everything.aab"
    $destinationDirectory = Join-Path $projectRoot "dist\playstore"
    $destination = Join-Path $destinationDirectory "rank-everything-0.5.0.aab"
    New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    Write-Host "AAB assinado criado em: $destination"
}
finally {
    Pop-Location
}
