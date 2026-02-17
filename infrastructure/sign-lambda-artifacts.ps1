param(
    [Parameter(Mandatory = $true)]
    [string]$ArtifactsBucket,

    [Parameter(Mandatory = $true)]
    [string]$SigningProfileName,

    [string]$Region = "us-east-1",

    [string]$UnsignedPrefix = "unsigned",

    [string]$SignedPrefix = "signed",

    [string]$HandlersPath = "backend/src/handlers",

    [string]$OutputTfvarsJsonPath = "infrastructure/lambda-artifacts.auto.tfvars.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path "."
$handlersFullPath = Join-Path $repoRoot $HandlersPath

if (-not (Test-Path $handlersFullPath)) {
    throw "Handlers path not found: $handlersFullPath"
}

$functions = @(
    "upload",
    "download",
    "list",
    "upload_complete",
    "delete",
    "trash",
    "hard_delete",
    "patch_photo",
    "search",
    "get_photo"
)

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$tempDir = Join-Path $env:TEMP "millerpic-signing-$timestamp"
New-Item -ItemType Directory -Path $tempDir | Out-Null

$artifactVersions = @{}
$artifactKeys = @{}

try {
    foreach ($fn in $functions) {
        $sourceFile = Join-Path $handlersFullPath "$fn.py"
        if (-not (Test-Path $sourceFile)) {
            throw "Missing handler source file: $sourceFile"
        }

        $stagingDir = Join-Path $tempDir "$fn-stage"
        New-Item -ItemType Directory -Path $stagingDir | Out-Null

        Copy-Item -Path $sourceFile -Destination (Join-Path $stagingDir "$fn.py") -Force

        $zipPath = Join-Path $tempDir "$fn.zip"
        if (Test-Path $zipPath) {
            Remove-Item $zipPath -Force
        }

        Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal

        $unsignedKey = "$UnsignedPrefix/$timestamp/$fn.zip"

        aws s3 cp $zipPath "s3://$ArtifactsBucket/$unsignedKey" --region $Region | Out-Null

        $startJobJson = aws signer start-signing-job --source "s3={bucketName=$ArtifactsBucket,key=$unsignedKey}" --destination "s3={bucketName=$ArtifactsBucket,prefix=$SignedPrefix/}" --profile-name $SigningProfileName --region $Region
        $startJob = $startJobJson | ConvertFrom-Json

        aws signer wait successful-signing-job --job-id $startJob.jobId --region $Region

        $jobDetailsJson = aws signer describe-signing-job --job-id $startJob.jobId --region $Region
        $jobDetails = $jobDetailsJson | ConvertFrom-Json

        $signedKey = $jobDetails.signedObject.s3.key
        $artifactKeys[$fn] = $signedKey

        $headJson = aws s3api head-object --bucket $ArtifactsBucket --key $signedKey --region $Region
        $head = $headJson | ConvertFrom-Json

        if (-not $head.VersionId) {
            throw "Signed object version ID not found for $fn at key $signedKey"
        }

        $artifactVersions[$fn] = $head.VersionId

        Remove-Item -Path $stagingDir -Recurse -Force
    }

    $tfvars = [ordered]@{
        lambda_artifacts_bucket_name   = $ArtifactsBucket
        lambda_signing_profile_name    = $SigningProfileName
        lambda_artifact_object_keys    = $artifactKeys
        lambda_artifact_object_versions = $artifactVersions
    }

    $outputPath = Join-Path $repoRoot $OutputTfvarsJsonPath
    $outputDir = Split-Path $outputPath -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }

    $tfvars | ConvertTo-Json -Depth 6 | Set-Content -Path $outputPath -Encoding UTF8

    Write-Host "Signed Lambda artifacts complete."
    Write-Host "Generated Terraform vars: $outputPath"
}
finally {
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
}
