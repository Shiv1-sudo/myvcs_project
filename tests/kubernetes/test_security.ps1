$ErrorActionPreference = "Stop"

$Namespace = "myvcs"
$Deployment = "myvcs"
$Container = "myvcs"

Write-Host "========================================="
Write-Host "MyVCS Kubernetes Security Test"
Write-Host "========================================="

Write-Host ""
Write-Host "[1/7] Waiting for MyVCS deployment..."

kubectl rollout status "deployment/$Deployment" `
    -n $Namespace `
    --timeout=180s

if ($LASTEXITCODE -ne 0) {
    throw "MyVCS deployment did not become ready."
}

Write-Host "Deployment successfully rolled out."

Write-Host ""
Write-Host "[2/7] Verifying ServiceAccount..."

$ServiceAccount = kubectl get deployment $Deployment `
    -n $Namespace `
    -o "jsonpath={.spec.template.spec.serviceAccountName}"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to query deployment ServiceAccount."
}

$ServiceAccount = $ServiceAccount.Trim()

if ($ServiceAccount -ne "myvcs") {
    throw "Expected ServiceAccount 'myvcs', found '$ServiceAccount'."
}

Write-Host "ServiceAccount: $ServiceAccount"

Write-Host ""
Write-Host "[3/7] Verifying ServiceAccount token automount is disabled..."

$Automount = kubectl get deployment $Deployment `
    -n $Namespace `
    -o "jsonpath={.spec.template.spec.automountServiceAccountToken}"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to query automountServiceAccountToken."
}

$Automount = $Automount.Trim()

if ($Automount -ne "false") {
    throw "Expected automountServiceAccountToken=false, found '$Automount'."
}

Write-Host "automountServiceAccountToken: false"

Write-Host ""
Write-Host "[4/7] Verifying container runs as non-root..."

$UID = kubectl exec `
    -n $Namespace `
    "deploy/$Deployment" `
    -c $Container `
    -- id -u

if ($LASTEXITCODE -ne 0) {
    throw "Unable to determine container UID."
}

$UID = $UID.Trim()

if ($UID -ne "1000") {
    throw "Expected container UID 1000, found '$UID'."
}

Write-Host "Container UID: $UID"

Write-Host ""
Write-Host "[5/7] Verifying container GID..."

$GID = kubectl exec `
    -n $Namespace `
    "deploy/$Deployment" `
    -c $Container `
    -- id -g

if ($LASTEXITCODE -ne 0) {
    throw "Unable to determine container GID."
}

$GID = $GID.Trim()

if ($GID -ne "1000") {
    throw "Expected container GID 1000, found '$GID'."
}

Write-Host "Container GID: $GID"

Write-Host ""
Write-Host "[6/7] Verifying pod security configuration..."

$DeploymentJson = kubectl get deployment $Deployment `
    -n $Namespace `
    -o json

if ($LASTEXITCODE -ne 0) {
    throw "Unable to retrieve deployment configuration."
}

$SecurityJson = $DeploymentJson | ConvertFrom-Json

$PodSpec = $SecurityJson.spec.template.spec
$PodSecurity = $PodSpec.securityContext
$ContainerSecurity = $PodSpec.containers[0].securityContext

if ($null -eq $PodSecurity) {
    throw "Pod securityContext is missing."
}

if ($PodSecurity.runAsNonRoot -ne $true) {
    throw "runAsNonRoot is not enabled."
}

if ([int]$PodSecurity.runAsUser -ne 1000) {
    throw "runAsUser is not 1000."
}

if ([int]$PodSecurity.runAsGroup -ne 1000) {
    throw "runAsGroup is not 1000."
}

if ($null -eq $ContainerSecurity) {
    throw "Container securityContext is missing."
}

if ($ContainerSecurity.allowPrivilegeEscalation -ne $false) {
    throw "allowPrivilegeEscalation is not disabled."
}

$DroppedCapabilities = @(
    $ContainerSecurity.capabilities.drop
)

if ($DroppedCapabilities -notcontains "ALL") {
    throw "Container does not drop ALL Linux capabilities."
}

$SeccompType = $PodSecurity.seccompProfile.type

if ($SeccompType -ne "RuntimeDefault") {
    throw "Expected seccompProfile.type=RuntimeDefault, found '$SeccompType'."
}

Write-Host "runAsNonRoot: true"
Write-Host "runAsUser: 1000"
Write-Host "runAsGroup: 1000"
Write-Host "allowPrivilegeEscalation: false"
Write-Host "capabilities.drop: ALL"
Write-Host "seccompProfile: RuntimeDefault"

Write-Host ""
Write-Host "[7/7] Verifying ServiceAccount token is not mounted..."

$TokenCheck = kubectl exec `
    -n $Namespace `
    "deploy/$Deployment" `
    -c $Container `
    -- sh -c "if [ -d /var/run/secrets/kubernetes.io/serviceaccount ]; then echo mounted; else echo not-mounted; fi"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect ServiceAccount token mount."
}

$TokenCheck = $TokenCheck.Trim()

if ($TokenCheck -ne "not-mounted") {
    throw "ServiceAccount token appears to be mounted."
}

Write-Host "ServiceAccount token: not mounted"

Write-Host ""
Write-Host "========================================="
Write-Host "SECURITY TEST PASSED"
Write-Host "========================================="
Write-Host ""
Write-Host "ServiceAccount : $ServiceAccount"
Write-Host "Token automount : false"
Write-Host "Container UID : $UID"
Write-Host "Container GID : $GID"
Write-Host "Non-root : verified"
Write-Host "Privilege escalation : disabled"
Write-Host "Capabilities : ALL dropped"
Write-Host "Seccomp : RuntimeDefault"
Write-Host "ServiceAccount token mount : not mounted"
Write-Host ""