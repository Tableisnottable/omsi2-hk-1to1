[CmdletBinding()]
param(
    [string]$OmsiPath = "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2\OpenOMSI.exe"
)

if (-not (Test-Path $OmsiPath -PathType Leaf)) {
    throw "OpenOMSI.exe was not found at '$OmsiPath'. Pass -OmsiPath to use another installation."
}
Start-Process -FilePath $OmsiPath -WorkingDirectory (Split-Path -Parent $OmsiPath)