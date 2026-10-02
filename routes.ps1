param(
    [Parameter(Mandatory=$true)][ValidateSet('Snapshot','Add','Remove')][string]$Action,
    [string]$Prefix,
    [string]$Gateway,
    [int]$InterfaceIndex,
    [string]$InterfaceGuid,
    [int]$Metric = 42
)
$ErrorActionPreference = 'Stop'

if ($Action -eq 'Snapshot') {
    $physical = @(Get-NetAdapter -Physical | Where-Object Status -eq 'Up')
    $defaults = @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
        Where-Object { $_.InterfaceIndex -in $physical.ifIndex -and $_.NextHop -ne '0.0.0.0' } |
        Sort-Object InterfaceIndex,NextHop -Unique)
    if ($defaults.Count -ne 1) { throw 'Expected exactly one active physical internet gateway.' }
    $default = $defaults[0]
    $adapter = Get-NetAdapter -InterfaceIndex $default.InterfaceIndex
    $routes = @(Get-NetRoute -AddressFamily IPv4 -PolicyStore ActiveStore | ForEach-Object {
        [ordered]@{
            prefix=[string]$_.DestinationPrefix
            gateway=[string]$_.NextHop
            interface_index=[int]$_.InterfaceIndex
            metric=[int]$_.RouteMetric
        }
    })
    [ordered]@{
        gateway=[string]$default.NextHop
        interface_index=[int]$default.InterfaceIndex
        interface_guid=[string]$adapter.InterfaceGuid
        interface_name=[string]$adapter.Name
        routes=$routes
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
}

if ($Prefix -notmatch '^([0-9]{1,3}\.){3}[0-9]{1,3}/32$') { throw 'Only individual IPv4 addresses are accepted.' }
$ip = $Prefix.Split('/')[0]
$parsed = $null
if (-not [Net.IPAddress]::TryParse($ip,[ref]$parsed) -or $parsed.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'Invalid IPv4 address.'
}
if ($Metric -ne 42) { throw 'Unexpected route metric.' }

if ($Action -eq 'Add') {
    $adapter = Get-NetAdapter -InterfaceIndex $InterfaceIndex
    if ([string]$adapter.InterfaceGuid -ne $InterfaceGuid) { throw 'Network adapter changed.' }
    $default = @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
        Where-Object { $_.InterfaceIndex -eq $InterfaceIndex -and $_.NextHop -eq $Gateway })
    if ($default.Count -ne 1) { throw 'Internet gateway changed.' }
    $existing = @(Get-NetRoute -AddressFamily IPv4 -PolicyStore ActiveStore |
        Where-Object DestinationPrefix -eq $Prefix)
    if ($existing.Count) { throw 'A route for this address already exists. Refresh the list.' }
    New-NetRoute -AddressFamily IPv4 -DestinationPrefix $Prefix -InterfaceIndex $InterfaceIndex -NextHop $Gateway -RouteMetric $Metric | Out-Null
    'OK'
    exit 0
}

$adapter = @(Get-NetAdapter -IncludeHidden | Where-Object { [string]$_.InterfaceGuid -eq $InterfaceGuid })
if ($adapter.Count -ne 1) { throw 'Original network adapter is unavailable.' }
foreach ($store in @('PersistentStore','ActiveStore')) {
    $matches = @(Get-NetRoute -PolicyStore $store | Where-Object {
        $_.DestinationPrefix -eq $Prefix -and
        $_.InterfaceIndex -eq $adapter[0].ifIndex -and
        $_.NextHop -eq $Gateway -and
        $_.RouteMetric -eq $Metric
    })
    foreach ($route in $matches) { $route | Remove-NetRoute -Confirm:$false }
}
'OK'
