<#
Deploys the backend as container-image Lambdas, following the production-backend pattern.
Creates what is missing (DynamoDB table, IAM role, ECR repository, HTTP API, daily schedule) and updates the rest.
Runtime secrets are read from Secrets Manager by the Lambdas; create the secret first (see README).

Usage: powershell -ExecutionPolicy Bypass -File deploy/deploy.ps1 -Environment dev
#>
param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$Registry = Get-Content -Raw -LiteralPath (Join-Path $ScriptDir "moduleRegistry.json") | ConvertFrom-Json
$Config = $Registry.environments.PSObject.Properties[$Environment].Value
$AwsArgs = @("--profile", $Registry.aws.profile, "--region", $Registry.aws.region)

function Test-AwsResource {
    param([string[]]$Arguments)
    $Saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & aws @Arguments @AwsArgs *> $null
    $Exists = $LASTEXITCODE -eq 0
    $ErrorActionPreference = $Saved
    return $Exists
}

function Invoke-Aws {
    param([string[]]$Arguments)
    $Output = & aws @Arguments @AwsArgs
    if ($LASTEXITCODE -ne 0) { throw "aws $($Arguments -join ' ') failed" }
    return $Output
}

function Write-TempJson {
    param([string]$Name, [object]$Value)
    $Path = Join-Path ([System.IO.Path]::GetTempPath()) "up4ds-$Name-$Environment.json"
    $Value | ConvertTo-Json -Compress -Depth 10 | Set-Content -LiteralPath $Path -Encoding ASCII
    return $Path
}

Set-Location $RootDir
$AccountId = Invoke-Aws @("sts", "get-caller-identity", "--query", "Account", "--output", "text")
$Region = $Registry.aws.region

# DynamoDB table
if (-not (Test-AwsResource @("dynamodb", "describe-table", "--table-name", $Config.tableName))) {
    $Definition = Get-Content -Raw (Join-Path $ScriptDir "tableDefinition.json") | ConvertFrom-Json
    $Definition.TableName = $Config.tableName
    Invoke-Aws @("dynamodb", "create-table", "--cli-input-json", "file://$(Write-TempJson 'table' $Definition)") | Out-Null
    Invoke-Aws @("dynamodb", "wait", "table-exists", "--table-name", $Config.tableName)
}

# IAM role
$RoleName = $Config.lambdaExecutionRoleName
if (-not (Test-AwsResource @("iam", "get-role", "--role-name", $RoleName))) {
    Invoke-Aws @("iam", "create-role", "--role-name", $RoleName,
        "--assume-role-policy-document", "file://$(Join-Path $ScriptDir 'iam/lambda-trust-policy.json')") | Out-Null
    Invoke-Aws @("iam", "put-role-policy", "--role-name", $RoleName, "--policy-name", "$RoleName-inline",
        "--policy-document", "file://$(Join-Path $ScriptDir 'iam/lambda-inline-policy.json')") | Out-Null
    Start-Sleep -Seconds 10
}
$RoleArn = Invoke-Aws @("iam", "get-role", "--role-name", $RoleName, "--query", "Role.Arn", "--output", "text")

# One image for both Lambdas
$RegistryHost = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$Repository = $Registry.ecrRepository
$ImageUri = "$RegistryHost/${Repository}:$($Config.imageTag)"
if (-not (Test-AwsResource @("ecr", "describe-repositories", "--repository-names", $Repository))) {
    Invoke-Aws @("ecr", "create-repository", "--repository-name", $Repository) | Out-Null
}
Invoke-Aws @("ecr", "get-login-password") | docker login --username AWS --password-stdin $RegistryHost
docker build --platform linux/amd64 --provenance=false -t $ImageUri .
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
docker push $ImageUri
if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }

$EnvFile = Write-TempJson "env" @{ Variables = @{
    appEnv = $Config.appEnv
    awsRegion = $Region
    configSecretName = $Config.secretName
    mainTableName = $Config.tableName
} }

foreach ($Module in $Registry.modules.PSObject.Properties) {
    $Spec = $Module.Value
    $FunctionName = "$($Config.lambdaNamePrefix)-$($Spec.lambdaNameSuffix)"
    $ImageConfig = "Command=$($Spec.command)"
    if (Test-AwsResource @("lambda", "get-function", "--function-name", $FunctionName)) {
        Invoke-Aws @("lambda", "update-function-code", "--function-name", $FunctionName, "--image-uri", $ImageUri) | Out-Null
        Invoke-Aws @("lambda", "wait", "function-updated", "--function-name", $FunctionName)
        Invoke-Aws @("lambda", "update-function-configuration", "--function-name", $FunctionName,
            "--memory-size", $Spec.memory, "--timeout", $Spec.timeout, "--image-config", $ImageConfig,
            "--environment", "file://$EnvFile") | Out-Null
    }
    else {
        Invoke-Aws @("lambda", "create-function", "--function-name", $FunctionName, "--package-type", "Image",
            "--code", "ImageUri=$ImageUri", "--image-config", $ImageConfig, "--role", $RoleArn,
            "--memory-size", $Spec.memory, "--timeout", $Spec.timeout, "--environment", "file://$EnvFile") | Out-Null
        Invoke-Aws @("lambda", "wait", "function-active", "--function-name", $FunctionName)
    }
    $FunctionArn = "arn:aws:lambda:${Region}:${AccountId}:function:$FunctionName"

    if ($Spec.trigger -eq "httpApi") {
        $ApiId = Invoke-Aws @("apigatewayv2", "get-apis", "--query", "Items[?Name=='$($Config.httpApiName)'].ApiId", "--output", "text")
        if (-not $ApiId -or $ApiId -eq "None") {
            $ApiId = Invoke-Aws @("apigatewayv2", "create-api", "--name", $Config.httpApiName, "--protocol-type", "HTTP",
                "--target", $FunctionArn, "--query", "ApiId", "--output", "text")
            Invoke-Aws @("lambda", "add-permission", "--function-name", $FunctionName, "--statement-id", "http-api-invoke",
                "--action", "lambda:InvokeFunction", "--principal", "apigateway.amazonaws.com",
                "--source-arn", "arn:aws:execute-api:${Region}:${AccountId}:$ApiId/*/*") | Out-Null
        }
        Write-Host "HTTP API: https://$ApiId.execute-api.$Region.amazonaws.com"
    }
    elseif ($Spec.trigger -eq "schedule") {
        $RuleName = "$FunctionName-daily"
        $RuleArn = Invoke-Aws @("events", "put-rule", "--name", $RuleName, "--schedule-expression", $Spec.scheduleExpression,
            "--query", "RuleArn", "--output", "text")
        Invoke-Aws @("events", "put-targets", "--rule", $RuleName, "--targets", "Id=followUpWorker,Arn=$FunctionArn") | Out-Null
        if (-not (Test-AwsResource @("lambda", "get-policy", "--function-name", $FunctionName))) {
            Invoke-Aws @("lambda", "add-permission", "--function-name", $FunctionName, "--statement-id", "daily-schedule",
                "--action", "lambda:InvokeFunction", "--principal", "events.amazonaws.com", "--source-arn", $RuleArn) | Out-Null
        }
    }
    Write-Host "Deployed $FunctionName from $ImageUri"
}
