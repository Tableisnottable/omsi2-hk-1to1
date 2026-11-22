"""Package only compiled SCS assets; keep OMSI sources and player saves untouched."""
from pathlib import Path
import hashlib, json, re, shutil, zipfile

from settings import ROOT, GAME_HOME, VERSION
CACHE = ROOT/'work/tools/conversion/rsrc/e6m/@cache'
OUT = ROOT/'outputs/E6M_ETS2'
MODNAME = 'ADL_E6M_ETS2_Test_v0.1.scs'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for model_key,names in (('adl_e6m',('truck.pmd','truck.pmg','truck.pmc','coach.pmd','coach.pmg','coach.pmc','interior.pmd','interior.pmg')),
                            ('adl_atenu',('coach.pmd','coach.pmg','coach.pmc','interior.pmd','interior.pmg'))):
        for name in names:
            path=CACHE/'vehicle/truck'/model_key/name
            minimum=500 if name.endswith('.pmc') else 1000
            assert path.is_file() and path.stat().st_size > minimum, str(path)
    log=(ROOT/'work/compile_final.log').read_text(errors='replace')
    assert '*** ERROR ***' not in log, 'Compiler reported errors'
    assert 'Conversion finished' in log, 'Compiler did not finish'
    files=sorted(p for p in CACHE.rglob('*') if p.is_file()
                 and not p.relative_to(CACHE).as_posix().startswith('def/vehicle/bus/adl.e6m/'))
    include_count=0
    definition_count=0
    for p in files:
        if p.suffix not in ('.sii','.sui'):
            continue
        definition_count+=1
        content=p.read_text(encoding='utf-8-sig')
        assert not re.search(r'(?m)^[ \t]+@include\b',content), f'Indented include: {p}'
        for match in re.finditer(r'(?m)^@include\s+"([^"]+)"',content):
            include_count+=1
            target=match[1]
            rel=target.lstrip('/') if target.startswith('/') else (p.parent/CACHE.relative_to(CACHE)/target).relative_to(CACHE).as_posix()
            assert (CACHE/rel).is_file() or (ROOT/'work/ets2_def'/rel).is_file() or (ROOT/'work/coach_dlc_extract'/rel).is_file(), f'Missing include: {target} in {p}'
    with zipfile.ZipFile(OUT/MODNAME,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:
            z.write(p,p.relative_to(CACHE).as_posix())
    with zipfile.ZipFile(OUT/MODNAME) as z:
        assert z.testzip() is None
        assert 'manifest.sii' in z.namelist()
    version=re.search(r'package_version:\s*"([^"]+)"',(CACHE/'manifest.sii').read_text())[1]
    assert version==VERSION, f'Stale compiled manifest: {version} vs {VERSION}'
    report={'package':MODNAME,'version':version,'files':len(files),'bytes':(OUT/MODNAME).stat().st_size,'sha256':hashlib.sha256((OUT/MODNAME).read_bytes()).hexdigest(),'compiler_errors':0,'definitions_checked':definition_count,'includes_checked':include_count,'invalid_indented_includes':0}
    (OUT/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    # -homedir appends the game directory. Use only its actual mod directory.
    test=ROOT/'work/ets2_test/Euro Truck Simulator 2'
    (test/'mod').mkdir(parents=True,exist_ok=True)
    cfg=(GAME_HOME/'config.cfg').read_text(encoding='utf8')
    for key,val in {'r_fullscreen':'0','r_fullscreen_borderless':'0','r_mode_width':'1280','r_mode_height':'720','g_lang_init':'en_gb','g_console':'1','g_developer':'1','g_save_format':'2','g_console_state':'0'}.items():
        cfg=re.sub(r'uset '+key+r' "[^"]*"',f'uset {key} "{val}"',cfg)
    if not (test/'config.cfg').exists():
        (test/'config.cfg').write_text(cfg,encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
