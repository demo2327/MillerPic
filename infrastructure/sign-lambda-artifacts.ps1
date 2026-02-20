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
    "get_photo",
    "albums_create",
    "albums_list",
    "albums_photos",
    "albums_apply_labels",
    "albums_remove_labels"
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

        if ($fn -like "albums_*") {
            $sharedModule = Join-Path $handlersFullPath "albums_common.py"
            if (-not (Test-Path $sharedModule)) {
                throw "Missing shared module for album handlers: $sharedModule"
            }
            Copy-Item -Path $sharedModule -Destination (Join-Path $stagingDir "albums_common.py") -Force
        }

        $zipPath = Join-Path $tempDir "$fn.zip"
        if (Test-Path $zipPath) {
            Remove-Item $zipPath -Force
        }

        Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal

        $unsignedKey = "$UnsignedPrefix/$timestamp/$fn.zip"

        aws s3 cp $zipPath "s3://$ArtifactsBucket/$unsignedKey" --region $Region | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upload unsigned artifact for $fn to s3://$ArtifactsBucket/$unsignedKey"
        }

        $unsignedHeadJson = aws s3api head-object --bucket $ArtifactsBucket --key $unsignedKey --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to read unsigned artifact metadata for $fn"
        }
        $unsignedHead = $unsignedHeadJson | ConvertFrom-Json

        if (-not $unsignedHead.VersionId) {
            throw "Unsigned object version ID not found for $fn at key $unsignedKey"
        }

        $startJobJson = aws signer start-signing-job --source "s3={bucketName=$ArtifactsBucket,key=$unsignedKey,version=$($unsignedHead.VersionId)}" --destination "s3={bucketName=$ArtifactsBucket,prefix=$SignedPrefix/}" --profile-name $SigningProfileName --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start signing job for $fn"
        }

        $startJob = $startJobJson | ConvertFrom-Json

        if (-not $startJob.jobId) {
            throw "Signer did not return a job ID for $fn"
        }

        aws signer wait successful-signing-job --job-id $startJob.jobId --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Signing job failed for $fn (jobId=$($startJob.jobId))"
        }

        $jobDetailsJson = aws signer describe-signing-job --job-id $startJob.jobId --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to describe signing job for $fn (jobId=$($startJob.jobId))"
        }
        $jobDetails = $jobDetailsJson | ConvertFrom-Json

        $signedKey = $jobDetails.signedObject.s3.key
        if (-not $signedKey) {
            throw "Signer response missing signed object key for $fn (jobId=$($startJob.jobId))"
        }
        $artifactKeys[$fn] = $signedKey

        $headJson = aws s3api head-object --bucket $ArtifactsBucket --key $signedKey --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to read signed object metadata for $fn at key $signedKey"
        }
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

    $tfvarsJson = $tfvars | ConvertTo-Json -Depth 6
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($outputPath, $tfvarsJson, $utf8NoBom)

    Write-Host "Signed Lambda artifacts complete."
    Write-Host "Generated Terraform vars: $outputPath"
}
finally {
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
}
