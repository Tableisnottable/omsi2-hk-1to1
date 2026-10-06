param (
    [string]$SheetNo = "11-SE-1D"
)

$ErrorActionPreference = "Continue"
$RepoPath   = "C:\Users\Table\Documents\GitHub\omsi2-hk-1to1"
$GisPath    = Join-Path $RepoPath "src\gis\$SheetNo"
$ZipPath    = Join-Path $RepoPath "src\gis\$SheetNo.zip"
$ModelPath  = Join-Path $RepoPath "Sceneryobjects\HK_Objects\model"

if (-not (Test-Path $GisPath)) { New-Item -Path $GisPath -ItemType Directory -Force | Out-Null }
if (-not (Test-Path $ModelPath)) { New-Item -Path $ModelPath -ItemType Directory -Force | Out-Null }

# 1. 下載 CSDI 3D-BIT00 數據包
$DownloadUrl = "https://download.map.gov.hk/so/3d-zip/3D-BIT00_${SheetNo}_FBX.zip"
Write-Host "Downloading 3D-BIT00 FBX tile: $SheetNo..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -ErrorAction Stop
    Expand-Archive -Path $ZipPath -DestinationPath $GisPath -Force
    Remove-Item $ZipPath -Force
    Write-Host "Successfully downloaded and extracted tile to $GisPath" -ForegroundColor Green
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
}

# 2. 自動搜尋電腦中的 Blender 執行檔
$BlenderExe = Get-Command "blender.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $BlenderExe) {
    $PossiblePaths = @(
        "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
    )
    foreach ($p in $PossiblePaths) {
        if (Test-Path $p) { $BlenderExe = $p; break }
    }
}

# 3. 建立 Blender Python 轉換腳本
$PyScript = Join-Path $RepoPath "src\scripts\convert.py"
$PyContent = @"
import bpy, os
in_dir = r'$GisPath'
out_dir = r'$ModelPath'
for root, dirs, files in os.walk(in_dir):
    for f in files:
        if f.lower().endswith('.fbx'):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=os.path.join(root, f))
            obj_name = os.path.splitext(f)[0] + '.obj'
            bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, obj_name))
"@
[System.IO.File]::WriteAllText($PyScript, $PyContent, [System.Text.Encoding]::UTF8)

# 4. 執行 Blender 後台轉換
if ($BlenderExe) {
    Write-Host "Found Blender at: $BlenderExe" -ForegroundColor Cyan
    Write-Host "Converting FBX to OBJ..." -ForegroundColor Cyan
    & $BlenderExe -b --python $PyScript
} else {
    Write-Host "Blender not found. Please install Blender or convert FBX manually." -ForegroundColor Yellow
}

# 5. 生成 OMSI .sco 定義檔
& (Join-Path $RepoPath "src\scripts\Generate-Sco.ps1")

Write-Host "Pipeline finished for $SheetNo!" -ForegroundColor Green