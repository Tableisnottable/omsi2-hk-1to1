"""Read the packaged vehicle definitions, expand includes, and check SII structure/references.

This preflight is deliberately separate from the generator. It is not an ETS2 runtime test.
"""
from pathlib import Path, PurePosixPath
import json, re, struct, zipfile

from settings import ROOT, VERSION
PACKAGE=ROOT/'outputs/E6M_ETS2/ADL_E6M_ETS2_Test_v0.1.scs'
STOCK=ROOT/'work/ets2_def'
BUS_DLC=ROOT/'work/coach_dlc_extract'
LEX=re.compile(r'"(?:\\.|[^"\\])*"|\#[^\n]*|[{}:\[\](),]|[^\s{}:\[\](),"#]+')

def compiled_locators(blob):
    """Read PMG v0x15 locator tokens as emitted by the installed SCS compiler.

    Checked against the installed stock Scania coach, rather than guessing
    locator names from the wheel accessory definitions.
    """
    assert blob[:4]==b'\x15gmP', 'Unsupported PMG version'
    count=struct.unpack_from('<I',blob,20)[0]
    offset=struct.unpack_from('<I',blob,80)[0]
    assert offset+count*44<=len(blob), 'Truncated PMG locator table'
    alphabet='\0'+'0123456789abcdefghijklmnopqrstuvwxyz_'
    locators={}
    for i in range(count):
        pos=offset+i*44
        token=struct.unpack_from('<Q',blob,pos)[0]
        name=''
        while token:
            name+=alphabet[token%38]
            token//=38
        assert name not in locators, f'Duplicate compiled locator: {name}'
        locators[name]=struct.unpack_from('<3f',blob,pos+8)
    return locators

class Parser:
    def __init__(self,text,label):
        self.tokens=[m[0] for m in LEX.finditer(text) if not m[0].startswith('#')]
        self.i=0
        self.label=label
    def take(self,expected=None):
        assert self.i<len(self.tokens), f'{self.label}: unexpected end; expected {expected}'
        token=self.tokens[self.i]
        self.i+=1
        assert expected is None or token==expected, f'{self.label}: expected {expected}, found {token}'
        return token
    def peek(self):
        return self.tokens[self.i] if self.i<len(self.tokens) else None
    def value(self):
        if self.peek()=='(':
            self.take('(')
            values=[self.value()]
            while self.peek()==',':
                self.take(',')
                values.append(self.value())
            self.take(')')
            return values
        value=self.take()
        assert value not in '{}:[]),(' and not value.startswith('@'), f'{self.label}: invalid value {value}'
        return value[1:-1] if value.startswith('"') else value
    def units(self):
        self.take('SiiNunit')
        self.take('{')
        units={}
        while self.peek()!='}':
            kind=self.take()
            self.take(':')
            name=self.take()
            assert name not in units, f'{self.label}: duplicate unit {name}'
            self.take('{')
            attrs={}
            while self.peek()!='}':
                key=self.take()
                assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',key), f'{self.label}: invalid attribute {key}'
                suffix=''
                if self.peek()=='[':
                    self.take('[')
                    suffix='['+(self.take() if self.peek()!=']' else '')+']'
                    self.take(']')
                self.take(':')
                attrs.setdefault(key+suffix,[]).append(self.value())
            self.take('}')
            for key,values in attrs.items():
                assert key.endswith('[]') or len(values)==1, f'{self.label}: repeated scalar {key}'
                if key+'[]' in attrs:
                    assert int(values[0])==len(attrs[key+'[]']), f'{self.label}: wrong {key} array count'
            units[name]={'type':kind,'attrs':attrs}
        self.take('}')
        assert self.peek() is None, f'{self.label}: trailing tokens'
        return units

def main():
    with zipfile.ZipFile(PACKAGE) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        includes=set()
        def read(path):
            if path in names: return z.read(path).decode('utf-8-sig')
            if (STOCK/path).is_file(): return (STOCK/path).read_text(encoding='utf-8-sig')
            return (BUS_DLC/path).read_text(encoding='utf-8-sig')
        def expand(path,stack=()):
            assert path not in stack, f'Cyclic include: {stack} -> {path}'
            output=[]
            for line in read(path).splitlines():
                if line.lstrip().startswith('@include'):
                    assert line.startswith('@include'), f'Indented include in {path}: {line}'
                    m=re.fullmatch(r'@include\s+"([^"]+)"\s*(?:#.*)?',line)
                    assert m, f'Invalid directive: {line}'
                    target=m[1]
                    rel=target.lstrip('/') if target.startswith('/') else str(PurePosixPath(path).parent/target)
                    includes.add((path,rel))
                    output.append(expand(rel,stack+(path,)))
                else:
                    output.append(line)
            return '\n'.join(output)
        parsed={path:Parser(expand(path),path).units() for path in sorted(names) if path.endswith('.sii')}
        assert parsed['manifest.sii']['.e6m_package']['attrs']['package_version'][0]==VERSION
        assert parsed['manifest.sii']['.e6m_package']['attrs']['category[]']==['truck'], 'Manifest contains an ETS2-unknown category'
        global_owners={}
        for path,defs in parsed.items():
            for name in defs:
                if name.startswith('.'): continue
                assert name not in global_owners, f'Global unit {name} duplicated in {path} and {global_owners.get(name)}'
                global_owners[name]=path
        stock_parsed={}
        def units(path):
            if path in parsed: return parsed[path]
            if path not in stock_parsed: stock_parsed[path]=Parser(expand(path),path).units()
            return stock_parsed[path]
        chassis=parsed['def/vehicle/truck/adl.e6m/chassis/6x2.sii']['6x2.adl.e6m.chassis']['attrs']
        axle_count=len(chassis['residual_travel[]'])
        steerable=chassis['steerable_axle[]']
        assert len(steerable)==axle_count
        expected_wheels={}
        for ax in ('f','r'):
            count=sum(v==('true' if ax=='f' else 'false') for v in steerable)
            for category in ('tire','disc','hub','nuts'):
                expected_wheels[ax+'_'+category]=list(range(0,count*2,2))
        dealer_count=0
        bus_config_count=0
        accessory_count=0
        for path,defs in list(parsed.items()):
            if any(x in path for x in ('/truck_dealer/','/truck_dealer_uk/','/truck_desktop/','/truck_desktop_uk/')):
                dealer_count+=1
                vehicle=defs['.truck']
                assert vehicle['type']=='vehicle'
                assert len(vehicle['attrs']['accessories[]'])==20
                wheel_offsets={}
                for ref in vehicle['attrs']['accessories[]']:
                    item=defs[ref]
                    target=item['attrs']['data_path'][0].lstrip('/')
                    target_defs=units(target)
                    assert len(target_defs)==1, f'Ambiguous vehicle accessory {target}'
                    if item['type']=='vehicle_wheel_accessory':
                        category=PurePosixPath(target).parts[2]
                        wheel_offsets.setdefault(category,[]).append(int(item['attrs']['offset'][0]))
                    accessory_count+=1
                assert {k:sorted(v) for k,v in wheel_offsets.items()}==expected_wheels, f'{path}: incomplete axle wheel coverage {wheel_offsets}'
            elif any(x in path for x in ('/bus_dealer/','/bus_desktop/','/bus_line/')):
                bus_config_count+=1
                vehicle=defs['.bus']
                assert vehicle['type']=='vehicle'
                assert len(vehicle['attrs']['accessories[]'])==20
                wheel_offsets={}
                for ref in vehicle['attrs']['accessories[]']:
                    item=defs[ref]
                    target=item['attrs']['data_path'][0].lstrip('/')
                    target_defs=units(target)
                    assert len(target_defs)==1, f'Ambiguous bus accessory {target}'
                    if item['type']=='vehicle_wheel_accessory':
                        category=PurePosixPath(target).parts[2]
                        wheel_offsets.setdefault(category,[]).append(int(item['attrs']['offset'][0]))
                    accessory_count+=1
                expected_bus={'a_tire':[0,2],'a_disc':[0,2],'a_hub':[0,2],'a_nuts':[0,2], 'b_tire':[0],'b_disc':[0],'b_hub':[0],'b_nuts':[0]}
                assert {k:sorted(v) for k,v in wheel_offsets.items()}==expected_bus, f'{path}: incomplete coach axle wheel coverage {wheel_offsets}'
        # Verify the two custom cameras actually exist in the camera registry files.
        for suffix in ('',' .oculus'):
            name='camera.interior.adl.e6m'+suffix.replace(' ','')
            assert any(name in defs for path,defs in parsed.items() if path.startswith('def/camera/camera_storage'))
        required=['chassis','cabin','interior','engine','transmission','paint_job','head_light','f_tire','r_tire']
        data=parsed['def/vehicle/truck/adl.e6m/data.sii']['vehicle.adl.e6m']['attrs']
        fallbacks={value.split('|',1)[0]:value.split('|',1)[1] for value in data['fallback[]']}
        for category in required:
            assert category in fallbacks, f'Missing fallback {category}'
            path='def/vehicle/'+category+'/'+fallbacks[category] if category in ('f_tire','r_tire') else 'def/vehicle/truck/adl.e6m/'+category+'/'+fallbacks[category]
            units(path)
        bus_data=parsed['def/vehicle/bus/adl.e6m.coach/data.sii']['vehicle.adl.e6m.coach']['attrs']
        bus_fallbacks={value.split('|',1)[0]:value.split('|',1)[1] for value in bus_data['fallback[]']}
        for category in ('chassis','cabin','interior','engine','transmission','paint_job','head_light','a_tire','a_disc','a_hub','a_nuts','b_tire','b_disc','b_hub','b_nuts'):
            assert category in bus_fallbacks, f'Missing coach fallback {category}'
            target='def/vehicle/'+category+'/'+bus_fallbacks[category] if category.startswith(('a_','b_')) else 'def/vehicle/bus/adl.e6m.coach/'+category+'/'+bus_fallbacks[category]
            units(target)
        bus_chassis=parsed['def/vehicle/bus/adl.e6m.coach/chassis/6x2.sii']['6x2.adl.e6m.coach.chassis']['attrs']
        assert bus_chassis['suspension_class'][0]=='bus'
        assert int(bus_chassis['passenger_capacity'][0])==80
        assert len(bus_chassis['residual_travel[]'])==3
        assert bus_config_count==2, 'Expected coach dealer and browser registrations'
        assert 'def/vehicle/bus_line/adl_e6m.sii' not in names, 'Quick jobs must wait for door/boarding runtime validation'
        model_checks={}
        for kind,expected in [('truck',{'wheel_f_0_0','wheel_f_1_0','wheel_r_0_0','wheel_r_1_0','wheel_r_2_0','wheel_r_3_0'}),
                              ('coach',{'wheel_a_0','wheel_a_1','wheel_a_2','wheel_a_3','wheel_b_0','wheel_b_1'})]:
            path='vehicle/truck/adl_e6m/'+kind+'.pmg'
            locators=compiled_locators(z.read(path))
            actual={name for name in locators if name.startswith('wheel_')}
            assert actual==expected, f'{kind}: compiled wheel locators {actual} differ from {expected}'
            positions=[locators[name] for name in sorted(actual)]
            assert len({round(p[2],3) for p in positions})==3, f'{kind}: wheels do not cover three longitudinal axle positions'
            assert sum(p[0]<0 for p in positions)==3 and sum(p[0]>0 for p in positions)==3
            model_checks[kind]=sorted(actual)
        dds_count=0
        for path in sorted(names):
            if not path.endswith('.dds'): continue
            blob=z.read(path)
            assert blob[:4]==b'DDS ', f'{path}: invalid DDS magic'
            h,w=struct.unpack_from('<II',blob,12)
            mips=struct.unpack_from('<I',blob,28)[0] or 1
            assert w>=4 and h>=4 and w%4==0 and h%4==0, f'{path}: invalid BC top-level dimensions {w}x{h}'
            assert w&(w-1)==0 and h&(h-1)==0, f'{path}: non power-of-two DDS'
            assert blob[84:88]==b'DX10', f'{path}: unexpected DDS format'
            fmt,dimension,array_size=struct.unpack_from('<II4xI',blob,128)
            assert fmt in (77,78) and dimension==3 and array_size==1, f'{path}: unexpected BC3 texture header'
            size=sum(max(1,(max(1,w>>i)+3)//4)*max(1,(max(1,h>>i)+3)//4)*16 for i in range(mips))
            assert len(blob)==148+size, f'{path}: truncated DDS ({len(blob)} vs {148+size})'
            dds_count+=1
        for kind,folder in (('truck','truck/adl.e6m'),('coach','bus/adl.e6m.coach')):
            for category in ('chassis/6x2.sii','cabin/e6m.sii'):
                attrs=next(iter(parsed['def/vehicle/'+folder+'/'+category].values()))['attrs']
                assert attrs['model'][0]=='/vehicle/truck/adl_e6m/'+kind+'.pmd'
                assert attrs['model'][0].lstrip('/') in names
        report={'version':VERSION,'archive_crc':'passed','definition_syntax':'passed','global_unit_ids_unique':'passed','sii_files':len(parsed),'include_edges':len(includes),'truck_dealer_and_browser_presets':dealer_count,'native_coach_presets':bus_config_count,'preset_accessory_references':accessory_count,'truck_fallbacks':len(required),'camera_registrations':2,'truck_axles':axle_count,'truck_wheel_pair_offsets':expected_wheels,'native_coach_suspension':'bus','coach_passenger_capacity':80,'coach_axle_wheel_coverage':'passed','compiled_model_wheel_locators':model_checks,'compiled_dds_textures':dds_count,'dds_dimensions_and_payloads':'passed','single_lod_model_paths':'passed','game_runtime_verified':False}
        (ROOT/'outputs/E6M_ETS2/DEFINITION_CHECK.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps(report,indent=2))

if __name__=='__main__': main()
