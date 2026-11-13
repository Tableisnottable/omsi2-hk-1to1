#!/usr/bin/env python3
"""Validate and package only Tsing Yi; generate a self-contained local map preview."""
import argparse
import importlib.util
import json
import zipfile
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path,required=True,help='Deliverable folder (ZIP, preview and check report)')
    args=parser.parse_args(); root=args.root.resolve(); out=args.output.resolve()
    spec=importlib.util.spec_from_file_location('validator',Path(__file__).with_name('Validate-TsingYi.py'))
    validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    report=validator.validate(root)
    if not report['passed']: raise RuntimeError(json.dumps(report,indent=2))
    out.mkdir(parents=True,exist_ok=True)
    (out/'TsingYi-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (out/'TsingYi-README.md').write_text((root/'TSING_YI.md').read_text(encoding='utf-8'),encoding='utf-8')
    data=(root/'maps'/'HK_TsingYi'/'preview_data.json').read_text(encoding='utf-8')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tsing Yi 1:1 — Geographic review</title><style>
*{box-sizing:border-box}body{margin:0;background:#102b39;color:#edf5f3;font:15px system-ui}canvas{display:block;width:100vw;height:100vh;touch-action:none}
aside{position:absolute;left:24px;top:24px;width:290px;padding:22px;background:#10212aed;border:1px solid #42606c;border-radius:12px;box-shadow:0 8px 40px #0005}h1{font-size:26px;margin:0 0 8px}p{line-height:1.5;color:#b8cbd0}label{display:block;margin:12px 0}button{background:#90dac1;border:0;border-radius:6px;padding:9px 15px;font:inherit;cursor:pointer}small{line-height:1.5;color:#a9bdc5}#tip{position:absolute;right:24px;bottom:24px;background:#10212ae8;padding:12px 18px;border-radius:8px;max-width:420px}
</style><canvas id="map"></canvas><aside><small>HONG KONG / FIRST AREA</small><h1>Tsing Yi 青衣</h1><p id="counts"></p>
<label><input id="bridges" type="checkbox" checked> Estimated bridge alignments</label><label><input id="stops" type="checkbox" checked> Bus stops</label><button id="reset">Reset view</button><p><small>Drag to pan · Scroll to zoom · Hover to inspect</small></p>
<small>Geographic build preview. Runtime testing, junction authoring, bridge profiles and passenger services remain in progress.<br><br>© OpenStreetMap contributors · ODbL<br>DEM: AWS Skadi / Tilezen elevation tiles</small></aside><div id="tip">Local preview · no external requests</div>
<script>const DATA=__DATA__;
const c=document.getElementById('map'),ctx=c.getContext('2d'),tip=document.getElementById('tip');let scale=1,ox=0,oy=0,drag=null;
document.getElementById('counts').textContent=`${DATA.manifest.tiles} tiles · ${DATA.manifest.road_splines.toLocaleString()} road segments · ${DATA.manifest.buildings.toLocaleString()} buildings · ${DATA.manifest.bus_stops} stops`;
function xy(p){return [p[0]*scale+ox,c.height-p[1]*scale-oy]}
function resize(){c.width=innerWidth*devicePixelRatio;c.height=innerHeight*devicePixelRatio;reset()}
function reset(){let xs=DATA.coast.map(p=>p[0]),ys=DATA.coast.map(p=>p[1]);let x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);scale=Math.min((c.width-430*devicePixelRatio)/(x1-x0),(c.height-100*devicePixelRatio)/(y1-y0));ox=(c.width+330*devicePixelRatio-(x1+x0)*scale)/2;oy=(c.height-(y1+y0)*scale)/2;draw()}
function draw(){ctx.fillStyle='#173746';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#2d554e';ctx.strokeStyle='#638c76';ctx.lineWidth=1.5*devicePixelRatio;ctx.beginPath();DATA.coast.forEach((p,i)=>{let q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.closePath();ctx.fill();ctx.stroke();
for(let bridge of [false,true]){if(bridge&&!document.getElementById('bridges').checked)continue;ctx.strokeStyle=bridge?'#e8b97c':'#cad9c8';ctx.lineWidth=(bridge?1.4:1)*devicePixelRatio;ctx.beginPath();for(let r of DATA.roads){if(r.bridge!==bridge)continue;ctx.moveTo(...xy(r.start));ctx.lineTo(...xy(r.end))}ctx.stroke()}
if(document.getElementById('stops').checked){ctx.fillStyle='#79e4c3';for(let s of DATA.stops){ctx.beginPath();ctx.arc(...xy([s.x,s.y]),2.7*devicePixelRatio,0,Math.PI*2);ctx.fill()}}}
c.onpointerdown=e=>{drag=[e.clientX,e.clientY,ox,oy];c.setPointerCapture(e.pointerId)};c.onpointerup=()=>drag=null;
c.onpointermove=e=>{if(drag){ox=drag[2]+(e.clientX-drag[0])*devicePixelRatio;oy=drag[3]-(e.clientY-drag[1])*devicePixelRatio;draw();return}let p=[e.clientX*devicePixelRatio,e.clientY*devicePixelRatio],best=15*devicePixelRatio,name='Local preview · no external requests';for(let s of DATA.stops){let q=xy([s.x,s.y]),d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<best){best=d;name=s.name}}tip.textContent=name};
c.onwheel=e=>{e.preventDefault();let x=e.clientX*devicePixelRatio,y=c.height-e.clientY*devicePixelRatio,k=Math.exp(-e.deltaY*.001);ox=x-(x-ox)*k;oy=y-(y-oy)*k;scale*=k;draw()};
document.getElementById('reset').onclick=reset;for(let id of ['stops','bridges'])document.getElementById(id).onchange=draw;onresize=resize;resize();</script></html>'''
    (out/'TsingYi-preview.html').write_text(html.replace('__DATA__',data.replace('</','<\\/')),encoding='utf-8')
    archive=out/'OMSI2-TsingYi-development.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for category in ('maps','Splines','Sceneryobjects'):
            for path in sorted((root/category/'HK_TsingYi').rglob('*')):
                if path.is_file(): z.write(path,path.relative_to(root))
        for name in ('TSING_YI.md','ATTRIBUTION.md'):
            z.write(root/name,name)
        hof=root/'maps'/'HK_TsingYi'/'TsingYi_Test.hof'
        if hof.exists():
            z.write(hof,'HOFs/TsingYi_Test.hof')
            z.write(hof,'Vehicles/MAN_NL_NG/TsingYi_Test.hof')
        z.write(out/'TsingYi-validation.json','TsingYi-validation.json')
    with zipfile.ZipFile(archive) as z:
        if bad:=z.testzip(): raise RuntimeError(f'ZIP verification failed: {bad}')
    print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'validation':report},indent=2))


if __name__=='__main__': main()
