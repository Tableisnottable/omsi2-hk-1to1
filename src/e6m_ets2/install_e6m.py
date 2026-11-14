"""Install a validated package only while ETS2 is closed, preserving the old one."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

from settings import ROOT, GAME_HOME, VERSION
from validate_e6m_defs import PACKAGE, main as validate

def main():
    validate()
    running=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',
                            'if (Get-Process eurotrucks2 -ErrorAction SilentlyContinue) { exit 10 }'],
                           capture_output=True,text=True,check=False)
    assert running.returncode==0, 'Close ETS2 before installing; the existing file has not been changed.'
    destination=GAME_HOME/'mod'/PACKAGE.name
    assert destination.parent.is_dir(), f'ETS2 mod folder not found: {destination.parent}'
    old_hash=None
    if destination.exists():
        old_hash=hashlib.sha256(destination.read_bytes()).hexdigest()
        backup=ROOT/'work/install_backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup.mkdir(parents=True,exist_ok=False)
        shutil.copy2(destination,backup/destination.name)
    digest=hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    temporary=destination.with_suffix('.installing')
    shutil.copy2(PACKAGE,temporary)
    assert hashlib.sha256(temporary.read_bytes()).hexdigest()==digest, 'Installation staging checksum mismatch'
    os.replace(temporary,destination)
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==digest
    report={'version':VERSION,'installed_sha256':digest,'previous_sha256':old_hash,
            'installed_package':str(destination),'runtime_retest_pending':True}
    (ROOT/'outputs/E6M_ETS2/INSTALL_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
