# Abre Blender 5.3 con el puente de supervisión y el archivo del proyecto.
# Uso:  powershell -ExecutionPolicy Bypass -File launch.ps1
$ErrorActionPreference = 'Stop'

$root   = Split-Path $PSScriptRoot -Parent
$bridge = Join-Path $PSScriptRoot 'bridge_addon.py'
$blend  = Join-Path $PSScriptRoot 'cedi360.blend'

$candidates = @(
  $env:BLENDER_EXE,
  'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe',
  'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
)

$blender = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $blender) { throw 'No se encontró blender.exe. Define BLENDER_EXE.' }

if (Test-Path $blend) {
  Write-Host "Abriendo $blend con puente en 127.0.0.1:9876"
  Start-Process -FilePath $blender -ArgumentList @("`"$blend`"", '--python', "`"$bridge`"")
} else {
  Write-Host "No existe el .blend; se abre Blender limpio con el puente."
  Start-Process -FilePath $blender -ArgumentList @('--factory-startup', '--python', "`"$bridge`"")
}
