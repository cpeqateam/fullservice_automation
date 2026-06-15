<#
  Windows — FULL Servis agent'ini (listener) boot'ta otomatik baslatan
  Gorev Zamanlayici (Task Scheduler) gorevi kurar. Ekstra bagimlilik gerekmez.

  Kullanim (Yonetici PowerShell):
    .\install-agent-task.ps1 -NodeId win_wifi -ServerUrl http://192.168.1.10:8770 -Port 7531

  Gorev "AtStartup" tetikleyici ile, SYSTEM hesabinda calisir; makine acilir
  acilmaz run_agent.py'yi baslatir.
#>
param(
  [Parameter(Mandatory = $true)][string]$NodeId,
  [Parameter(Mandatory = $true)][string]$ServerUrl,
  [int]$Port = 7531,
  [string]$Python
)
$ErrorActionPreference = "Stop"

$workDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path   # fullservice-backend
if (-not $Python) {
  $venvPy = Join-Path $workDir "venv\Scripts\python.exe"
  $Python = if (Test-Path $venvPy) { $venvPy } else { (Get-Command python).Source }
}

$taskName = "FullServiceAgent_$NodeId"
$runAgent = Join-Path $workDir "run_agent.py"
$arguments = "`"$runAgent`" $NodeId $ServerUrl $Port"

Write-Host "[Windows] Gorev: $taskName"
Write-Host "          $Python $arguments  (cwd=$workDir)"

$action    = New-ScheduledTaskAction -Execute $Python -Argument $arguments -WorkingDirectory $workDir
$trigger   = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
  -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "[Windows] Gorev kuruldu. Simdi baslat: Start-ScheduledTask -TaskName $taskName"
Write-Host "          Kaldir: Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"
