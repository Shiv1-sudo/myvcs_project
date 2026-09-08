$ErrorActionPreference = "Stop"

$Namespace = "myvcs"
$Deployment = "myvcs"
$Container = "myvcs"

Write-Host "========================================="
Write-Host "MyVCS Kubernetes Persistence Test"
Write-Host "========================================="

function Get-MyVCSPod {
    $pod = kubectl get pods `
        -n $Namespace `
        -l "app.kubernetes.io/name=myvcs,app.kubernetes.io/component=application" `
        --field-selector="status.phase=Running" `
        -o "jsonpath={.items[0].metadata.name}"

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to query MyVCS pods."
    }

    if (-not $pod) {
        throw "Unable to find a running MyVCS application pod."
    }

    return $pod.Trim()
}

function Invoke-MyVCS {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Pod,

        [Parameter(Mandatory = $true)]
        [string[]]$CommandArguments
    )

    $kubectlArguments = @(
        "exec"
        "-n"
        $Namespace
        $Pod
        "-c"
        $Container
        "--"
    )

    $kubectlArguments += $CommandArguments

    $output = & kubectl @kubectlArguments

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed in pod '$Pod': $($CommandArguments -join ' ')"
    }

    return $output
}

Write-Host ""
Write-Host "[1/8] Waiting for MyVCS deployment..."

kubectl rollout status "deployment/$Deployment" `
    -n $Namespace `
    --timeout=180s

if ($LASTEXITCODE -ne 0) {
    throw "MyVCS deployment did not become ready."
}

Write-Host "Deployment successfully rolled out."

Write-Host ""
Write-Host "[2/8] Finding initial pod..."

$PodA = Get-MyVCSPod

Write-Host "Initial pod: $PodA"

Write-Host ""
Write-Host "[3/8] Initializing repository..."

Invoke-MyVCS $PodA @(
    "sh"
    "-c"
    "rm -rf /workspace/.myvcs /workspace/hello.txt"
) | ForEach-Object {
    Write-Host $_
}

Invoke-MyVCS $PodA @(
    "myvcs"
    "init"
) | ForEach-Object {
    Write-Host $_
}

Write-Host ""
Write-Host "[4/8] Creating test commit..."

Invoke-MyVCS $PodA @(
    "sh"
    "-c"
    "printf 'persistence-test' > /workspace/hello.txt"
) | ForEach-Object {
    Write-Host $_
}

Invoke-MyVCS $PodA @(
    "myvcs"
    "add"
    "hello.txt"
) | ForEach-Object {
    Write-Host $_
}

$CommitOutput = Invoke-MyVCS $PodA @(
    "myvcs"
    "commit"
    "-m"
    "Kubernetes persistence test"
)

$CommitOutputText = $CommitOutput -join "`n"
$CommitSha = $null

if ($CommitOutputText -match "\[([0-9a-f]{64})\]") {
    $CommitSha = $Matches[1]
}
else {
    throw "Unable to extract commit SHA from myvcs commit output. Output was: $CommitOutputText"
}

Write-Host "Captured commit SHA: $CommitSha"

Write-Host ""
Write-Host "[5/8] Verifying commit before pod deletion..."

$LogBefore = Invoke-MyVCS $PodA @(
    "myvcs"
    "log"
)

$LogBeforeText = $LogBefore -join "`n"

if ($LogBeforeText -notmatch [regex]::Escape($CommitSha)) {
    throw "Test commit was not found before pod deletion. Expected commit: $CommitSha"
}

Write-Host "Commit verified before deletion: $CommitSha"

Write-Host ""
Write-Host "[6/8] Deleting application pod..."

kubectl delete pod `
    -n $Namespace `
    $PodA `
    --wait=true

if ($LASTEXITCODE -ne 0) {
    throw "Unable to delete application pod."
}

Write-Host "Pod deleted: $PodA"

Write-Host ""
Write-Host "[7/8] Waiting for replacement pod..."

$NewPod = $null

for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2

    try {
        $Candidate = Get-MyVCSPod

        if ($Candidate -and $Candidate -ne $PodA) {
            $NewPod = $Candidate
            break
        }
    }
    catch {
    }
}

if (-not $NewPod) {
    throw "Replacement MyVCS pod was not created."
}

Write-Host "Replacement pod: $NewPod"

kubectl wait `
    --for=condition=Ready `
    "pod/$NewPod" `
    -n $Namespace `
    --timeout=180s

if ($LASTEXITCODE -ne 0) {
    throw "Replacement pod did not become ready."
}

Write-Host "Replacement pod is Ready."

Write-Host ""
Write-Host "[8/8] Verifying repository persistence..."

$LogAfter = Invoke-MyVCS $NewPod @(
    "myvcs"
    "log"
)

$LogAfterText = $LogAfter -join "`n"

if ($LogAfterText -notmatch [regex]::Escape($CommitSha)) {
    throw "Persistence test FAILED: commit $CommitSha was not found after pod replacement."
}

Write-Host "Commit persisted successfully: $CommitSha"

$FileContent = Invoke-MyVCS $NewPod @(
    "sh"
    "-c"
    "cat /workspace/hello.txt"
)

$FileContentText = $FileContent -join "`n"

if ($FileContentText.Trim() -ne "persistence-test") {
    throw "Persistence test FAILED: hello.txt content is incorrect. Actual content: '$FileContentText'"
}

Write-Host "File persisted successfully: hello.txt"

Write-Host ""
Write-Host "========================================="
Write-Host "PERSISTENCE TEST PASSED"
Write-Host "========================================="
Write-Host ""
Write-Host "Original pod : $PodA"
Write-Host "Replacement  : $NewPod"
Write-Host "Commit       : $CommitSha"
Write-Host "File         : verified"
Write-Host "PVC          : verified indirectly"
Write-Host ""
