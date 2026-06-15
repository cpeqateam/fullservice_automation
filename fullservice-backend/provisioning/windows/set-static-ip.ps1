<#
  Windows — bir dugume config.json'daki statik IP'yi atar.

  Kullanim (Yonetici PowerShell):
    .\set-static-ip.ps1 -NodeId win_wifi

  config.json "network" bolumunden ip / subnet_mask / gateway / dns ve
  assignments[NodeId].interface (Windows arayuz adi, or. "Wi-Fi" / "Ethernet") okunur.
  Arayuz adlarini gormek icin:  Get-NetAdapter | Select Name,InterfaceDescription
#>
param(
  [Parameter(Mandatory = $true)][string]$NodeId,
  [string]$ConfigPath
)
$ErrorActionPreference = "Stop"

if (-not $ConfigPath) {
  $ConfigPath = Join-Path $PSScriptRoot "..\..\config.json"
}
$cfg  = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
$net  = $cfg.network
$a    = $net.assignments.$NodeId
if (-not $a) { throw "config.json network.assignments icinde '$NodeId' yok." }

$iface = $a.interface
$ip    = $a.ip
$gw    = $net.gateway
$dns   = $net.dns

# Subnet mask → prefix uzunlugu (255.255.255.0 → 24)
$prefix = ($net.subnet_mask -split '\.' | ForEach-Object {
  [Convert]::ToString([int]$_, 2)
}) -join '' -replace '0', '' | ForEach-Object { $_.Length }

Write-Host "[Windows] $NodeId -> arayuz='$iface' ip=$ip /$prefix gw=$gw dns=$($dns -join ',')"

# Eski IP/route'lari temizle (varsa) ve yeniden ata
Get-NetIPAddress -InterfaceAlias $iface -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
Remove-NetRoute -InterfaceAlias $iface -DestinationPrefix "0.0.0.0/0" -Confirm:$false -ErrorAction SilentlyContinue

New-NetIPAddress -InterfaceAlias $iface -IPAddress $ip -PrefixLength $prefix -DefaultGateway $gw | Out-Null
Set-DnsClientServerAddress -InterfaceAlias $iface -ServerAddresses $dns

Write-Host "[Windows] Statik IP atandi. Kontrol: Get-NetIPConfiguration -InterfaceAlias '$iface'"
