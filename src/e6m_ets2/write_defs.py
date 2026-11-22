from pathlib import Path
import re,json
from build_e6m import ROOT, BASE, put
from settings import VERSION

DEF=ROOT/'work/ets2_def/def'
TRUCK='adl.e6m'
PREFIX='def/vehicle/truck/'+TRUCK+'/'

def unit(path,typ,name,body):
    # SII preprocessor directives must begin at column zero.
    body=re.sub(r'(?m)^[ \t]+(?=@include\b)','',body)
    put(PREFIX+path,f'SiiNunit\n{{\n{typ} : {name}\n{{\n{body}\n}}\n}}\n')

def read(path):
    return (DEF/path).read_text(encoding='utf-8-sig')

def main():
    data=read('vehicle/truck/scania.streamline/data.sii')
    data=data.replace('vehicle.scania.streamline','vehicle.adl.e6m')
    data=data.replace('"@@brand_scania@@"','"ADL"').replace('"@@series_scania_streamline@@"','"Enviro500 MMC E6M"')
    data=data.replace('camera.interior.scania.streamline.oculus','camera.interior.adl.e6m.oculus').replace('camera.interior.scania.streamline','camera.interior.adl.e6m')
    data=re.sub(r'\s*require\[\]:[^\n]+','',data)
    data=re.sub(r'\s*fallback\[\]: "(?:mirror|accessory)\|[^\n]+','',data)
    for a,b in [('chassis|4x2','chassis|6x2'),('cabin|normal','cabin|e6m'),('interior|normal','interior|rhd'),('engine|dc13_360','engine|isl9'),('transmission|12_speed','transmission|ecolife'),('paint_job|color7','paint_job|kmb')]: data=data.replace(a,b)
    put(PREFIX+'data.sii',data)
    unit('chassis/6x2.sii','accessory_chassis_data','6x2.adl.e6m.chassis','''
 name: "E6M 6x2 bus chassis"
 price: 40000
 unlock: 0
 icon: "chassis_scania_r_6x2"
 part_type: factory
 model: "/vehicle/truck/adl_e6m/truck.pmd"
 collision: "/vehicle/truck/adl_e6m/truck.pmc"
 variant: chs_6x2
 look: default
 tank_size: 350
 adblue_tank_size: 40
 residual_travel[]: 0.08
 residual_travel[]: 0.08
 residual_travel[]: 0.08
 powered_axle[]: false
 powered_axle[]: true
 powered_axle[]: false
 steerable_axle[]: true
 steerable_axle[]: false
 steerable_axle[]: false
 liftable_axle[]: false
 liftable_axle[]: false
 liftable_axle[]: false
 kerb_weight[]: 5000
 kerb_weight[]: 6600
 kerb_weight[]: 3200
 defaults[]: "/def/vehicle/truck/adl.e6m/cabin/e6m.sii"
 defaults[]: "/def/vehicle/truck/adl.e6m/engine/isl9.sii"
 defaults[]: "/def/vehicle/truck/adl.e6m/paint_job/kmb.sii"
 @include "/def/vehicle/truck/scania.streamline/chassis/sound.sui"
''')
    unit('cabin/e6m.sii','accessory_cabin_data','e6m.adl.e6m.cabin','''
 name: "Enviro500 MMC E6M - KMB"
 price: 100000
 unlock: 0
 icon: "cab_scania_r_c"
 part_type: factory
 model: "/vehicle/truck/adl_e6m/truck.pmd"
 variant: e6m_cab
 variant_uk: e6m_cab
 look: default
 defaults[]: "/def/vehicle/truck/adl.e6m/interior/rhd.sii"
 defaults[]: "/def/vehicle/truck/adl.e6m/head_light/standard.sii"
 suitable_for[]: "6x2.adl.e6m.chassis"
 @include "/def/vehicle/truck/scania.streamline/cabin/sound.sui"
''')
    unit('interior/rhd.sii','accessory_interior_data','rhd.adl.e6m.interior','''
 name: "E6M right-hand-drive cab"
 price: 10000
 unlock: 0
 icon: "interior_streamline_std_uk"
 part_type: factory
 model: "/vehicle/truck/adl_e6m/interior.pmd"
 look: default
 variant: default
 left_hand_traffic: true
 suitable_for[]: "e6m.adl.e6m.cabin"
 seat_left_limit: -0.15
 seat_right_limit: 0.15
 seat_up_limit: 0.15
 seat_down_limit: -0.15
 seat_front_limit: -0.15
 seat_back_limit: 0.3
 @include "/def/vehicle/truck/scania.streamline/interior/sound.sui"
''')
    unit('engine/isl9.sii','accessory_engine_data','isl9.adl.e6m.engine','''
 name: "Cummins ISL9 Euro VI 340"
 price: 10000
 unlock: 0
 icon: "engine_01"
 part_type: factory
 info[]: "340 hp (250 kW)"
 info[]: "1500 Nm at 1200-1400 rpm"
 torque: 1500
 volume: 8.9
 rpm_idle: 700
 rpm_limit: 2350
 rpm_range_low_gear: (900, 1600)
 rpm_range_high_gear: (1000, 1800)
 torque_curve[]: (300, 0.2)
 torque_curve[]: (700, 0.6)
 torque_curve[]: (1200, 1.0)
 torque_curve[]: (1400, 1.0)
 torque_curve[]: (1600, 0.953333)
 torque_curve[]: (1700, 0.866667)
 torque_curve[]: (1800, 0.82)
 torque_curve[]: (2100, 0.757333)
 torque_curve[]: (2350, 0.0)
 @include "/def/vehicle/truck/scania.streamline/engine/sound_lo.sui"
''')
    unit('transmission/ecolife.sii','accessory_transmission_data','ecolife.adl.e6m.transmission','''
 name: "ZF EcoLife 6AP1700 - 6 speed automatic"
 price: 5000
 unlock: 0
 icon: "transmission_generic"
 differential_ratio: 6.20
 shift_time: 0.35
 retarder: 3
 ratios_reverse[0]: -4.235
 ratios_forward[0]: 3.364
 ratios_forward[1]: 1.909
 ratios_forward[2]: 1.421
 ratios_forward[3]: 1.0
 ratios_forward[4]: 0.72
 ratios_forward[5]: 0.615
 @include "/def/vehicle/truck/scania.streamline/transmission/sound.sui"
''')
    unit('paint_job/kmb.sii','accessory_paint_job_data','kmb.adl.e6m.paint_job','''
 name: "KMB E6M original livery"
 price: 1000
 unlock: 0
 base_color: (1.0, 1.0, 1.0)
 base_color_locked: true
 stock: true
 part_type: factory
 suitable_for[]: "e6m.adl.e6m.cabin"
''')
    light=read('vehicle/truck/scania.streamline/head_light/standard.sii')
    light=light.replace('std.scania.streamline.head_light','std.adl.e6m.head_light').replace('(0.000000, 0.869423, -3.28791)','(0.000000, 0.830000, -5.020000)')
    put(PREFIX+'head_light/standard.sii',light)
    for suffix in ('','_oculus'):
        cam=read('camera/units/interior_scania_streamline'+suffix+'.sui').replace('scania.streamline','adl.e6m')
        cam=cam.replace('camera_fov: 77','camera_fov: 70').replace('head_offset: (0.0, -0.02, 0.14)','head_offset: (0.0, 0.0, 0.0)').replace('near_plane: 0.2','near_plane: 0.05')
        put('def/camera/units/interior_adl_e6m'+suffix+'.sui',cam)
        put('def/camera/camera_storage'+('.oculus' if suffix else '')+'.e6m.sii',f'SiiNunit\n{{\n@include "units/interior_adl_e6m{suffix}.sui"\n}}\n')
    # Standalone truck preset, available through Access Mod Dealer, without replacing stock trucks.
    acc=[('data','vehicle_accessory','data.sii'),('chassis','vehicle_accessory','chassis/6x2.sii'),('cabin','vehicle_accessory','cabin/e6m.sii'),('interior','vehicle_accessory','interior/rhd.sii'),('engine','vehicle_accessory','engine/isl9.sii'),('transm','vehicle_accessory','transmission/ecolife.sii'),('headl','vehicle_accessory','head_light/standard.sii'),('paint','vehicle_paint_job_accessory','paint_job/kmb.sii')]
    wheels={'f_tire':'1','f_disc':'front_disc_02_matt_gray','f_hub':'front_hub_01','f_nuts':'front_nuts_01_steel','r_tire':'1','r_disc':'rear_disc_01_matt_gray','r_hub':'rear_hub_01','r_nuts':'rear_nuts_01_steel'}
    wheel_offsets={}
    for cat,name in wheels.items():
        # Each wheel accessory covers a left/right pair. A three-axle 6x2
        # needs both rear pairs, matching the stock ETS2 6x2 presets.
        for offset in ((0,2) if cat.startswith('r_') else (0,)):
            key=cat+('2' if offset else '')
            acc.append((key,'vehicle_wheel_accessory',f'/def/vehicle/{cat}/{name}.sii'))
            wheel_offsets[key]=offset
    preset='SiiNunit\n{\nvehicle : .truck {\n'+''.join(f' accessories[]: .{n}\n' for n,_,_ in acc)+'}\n'
    for name,typ,path in acc:
        full=path if path.startswith('/') else '/'+PREFIX+path
        preset+=f'{typ} : .{name} {{\n data_path: "{full}"\n'+(f' offset: {wheel_offsets[name]}\n' if typ=='vehicle_wheel_accessory' else '')+'}\n'
    preset+='}\n'
    for where in ('truck_dealer/scania/adl_e6m.sii','truck_dealer_uk/scania/adl_e6m.sii','truck_desktop/adl.e6m.sii','truck_desktop_uk/adl.e6m.sii'):
        put('def/vehicle/'+where,preset)
    bus_prefix='def/vehicle/bus/adl.e6m.coach/'
    def bus_unit(path,typ,name,body):
        name=name.replace('adl.e6m','adl.e6m.coach')
        body=body.replace('/bus/adl.e6m/','/bus/adl.e6m.coach/')
        for category in ('chassis','cabin','interior','engine','transmission','paint_job','head_light'):
            body=body.replace('adl.e6m.'+category,'adl.e6m.coach.'+category)
        body=body.replace('/adl_e6m/truck.pm','/adl_e6m/coach.pm')
        body=re.sub(r'(?m)^[ \t]+(?=@include\b)','',body)
        put(bus_prefix+path,f'SiiNunit\n{{\n{typ} : {name}\n{{\n{body}\n}}\n}}\n')
    bus_unit('data.sii','accessory_truck_data','vehicle.adl.e6m','''
 info[]: "ADL"
 info[]: "Enviro500 MMC E6M"
 driver_model: "/asset/character/human/driver_bus/$driver_type$/driver.pmd"
 driver_animation: "/asset/character/human/driver_bus/$driver_type$/scania_touring_2023_ani.pma"
 behind_camera: camera.behind.bus
 interior_camera: camera.interior.adl.e6m
 interior_camera_oculus: camera.interior.adl.e6m.oculus
 bumper_camera: camera.bumper.scania.touring_23
 window_camera: camera.window.basic
 cabin_camera: camera.cabin.basic
 wheel_camera: camera.wheel.basic
 top_camera: camera.top.basic
 tv_camera: camera.tv.basic
 wander_camera: camera.wander
 debug_camera: camera.debug
 fallback[]: "chassis|6x2.sii"
 fallback[]: "cabin|e6m.sii"
 fallback[]: "interior|rhd.sii"
 fallback[]: "engine|isl9.sii"
 fallback[]: "transmission|ecolife.sii"
 fallback[]: "paint_job|kmb.sii"
 fallback[]: "head_light|standard.sii"
 fallback[]: "a_tire|1.sii"
 fallback[]: "a_disc|front_disc_02_matt_gray.sii"
 fallback[]: "a_hub|front_hub_01.sii"
 fallback[]: "a_nuts|front_nuts_01_steel.sii"
 fallback[]: "b_tire|1.sii"
 fallback[]: "b_disc|rear_disc_01_matt_gray.sii"
 fallback[]: "b_hub|rear_hub_01.sii"
 fallback[]: "b_nuts|rear_nuts_01_steel.sii"
 @include "/def/vehicle/bus/common_bus_data.sui"
''')
    bus_unit('chassis/6x2.sii','accessory_chassis_data','6x2.adl.e6m.chassis','''
 name: "E6M 6x2 Coach Chassis"
 price: 40000
 unlock: 0
 icon: "bus/share/chassis/chassis_6x24"
 part_type: factory
 model: "/vehicle/truck/adl_e6m/truck.pmd"
 collision: "/vehicle/truck/adl_e6m/truck.pmc"
 variant: chs_6x2
 look: default
 tank_size: 350
 adblue_tank_size: 40
 residual_travel[]: 0.08
 residual_travel[]: 0.08
 residual_travel[]: 0.08
 powered_axle[]: false
 powered_axle[]: true
 powered_axle[]: false
 steerable_axle[]: true
 steerable_axle[]: false
 steerable_axle[]: true
 liftable_axle[]: false
 liftable_axle[]: false
 liftable_axle[]: false
 suspension_class: bus
 passenger_capacity: 80
 max_steering_angle: 51
 kerb_weight[0]: 5000
 kerb_weight[1]: 6600
 kerb_weight[2]: 3200
 cog_height: 1.5
 suitable_for[]: "e6m.adl.e6m.cabin"
 @include "/def/vehicle/bus/scania.touring_23/chassis/sound.sui"
''')
    bus_unit('cabin/e6m.sii','accessory_cabin_data','e6m.adl.e6m.cabin','''
 name: "Enviro500 MMC E6M Coach"
 price: 100000
 unlock: 0
 part_type: factory
 model: "/vehicle/truck/adl_e6m/truck.pmd"
 variant: e6m_cab
 look: default
 doors: 3
 suspension: false
 defaults[]: "/def/vehicle/bus/adl.e6m/chassis/6x2.sii"
 defaults[]: "/def/vehicle/bus/adl.e6m/interior/rhd.sii"
 suitable_for[]: "6x2.adl.e6m.chassis"
 @include "/def/vehicle/bus/scania.touring_23/cabin/sound.sui"
''')
    bus_unit('interior/rhd.sii','accessory_interior_data','rhd.adl.e6m.interior','''
 name: "E6M right-hand-drive interior"
 price: 10000
 unlock: 0
 part_type: factory
 model: "/vehicle/truck/adl_e6m/interior.pmd"
 look: default
 variant: default
 suitable_for[]: "e6m.adl.e6m.cabin"
 seat_left_limit: -0.15
 seat_right_limit: 0.15
 seat_up_limit: 0.15
 seat_down_limit: -0.15
 seat_front_limit: -0.15
 seat_back_limit: 0.3
 @include "/def/vehicle/bus/scania.touring_23/interior/sound.sui"
''')
    bus_unit('engine/isl9.sii','accessory_engine_data','isl9.adl.e6m.engine','''
 name: "Cummins ISL9 Euro VI 340"
 price: 10000
 unlock: 0
 info[]: "340 hp (250 kW)"
 info[]: "1500 Nm at 1200-1400 rpm"
 icon: "engine_scania_dc13"
 part_type: factory
 torque: 1500
 volume: 8.9
 rpm_idle: 700
 rpm_limit: 2350
 rpm_range_low_gear: (900, 1600)
 rpm_range_high_gear: (1000, 1800)
 torque_curve[]: (300, 0.2)
 torque_curve[]: (700, 0.6)
 torque_curve[]: (1200, 1.0)
 torque_curve[]: (1400, 1.0)
 torque_curve[]: (1600, 0.953333)
 torque_curve[]: (1700, 0.866667)
 torque_curve[]: (1800, 0.82)
 torque_curve[]: (2100, 0.757333)
 torque_curve[]: (2350, 0.0)
 @include "/def/vehicle/bus/scania.touring_23/engine/sound.sui"
''')
    bus_unit('transmission/ecolife.sii','accessory_transmission_data','ecolife.adl.e6m.transmission','''
 name: "ZF EcoLife 6AP1700 - 6 speed automatic"
 price: 5000
 unlock: 0
 icon: "transmission/ecolife_2"
 part_type: factory
 differential_ratio: 6.20
 shift_time: 0.35
 retarder: 3
 ratios_reverse[0]: -4.235
 ratios_forward[0]: 3.364
 ratios_forward[1]: 1.909
 ratios_forward[2]: 1.421
 ratios_forward[3]: 1.0
 ratios_forward[4]: 0.72
 ratios_forward[5]: 0.615
 @include "/def/vehicle/bus/scania.touring_23/transmission/sound.sui"
''')
    bus_unit('paint_job/kmb.sii','accessory_paint_job_data','kmb.adl.e6m.paint_job','''
 name: "KMB E6M original livery"
 price: 1000
 unlock: 0
 base_color: (1.0, 1.0, 1.0)
 base_color_locked: true
 stock: true
 part_type: factory
 suitable_for[]: "e6m.adl.e6m.cabin"
''')
    bus_light=light.replace('std.adl.e6m.head_light','std.adl.e6m.coach.head_light')
    put(bus_prefix+'head_light/standard.sii',bus_light)
    bus_acc=[('data','vehicle_accessory','data.sii'),('chassis','vehicle_accessory','chassis/6x2.sii'),('cabin','vehicle_accessory','cabin/e6m.sii'),('engine','vehicle_accessory','engine/isl9.sii'),('transm','vehicle_accessory','transmission/ecolife.sii'),('interior','vehicle_accessory','interior/rhd.sii'),('headl','vehicle_accessory','head_light/standard.sii'),('paint','vehicle_paint_job_accessory','paint_job/kmb.sii')]
    bus_wheels={'a_tire':('1',0),'a_tire2':('1',2),'a_disc':('front_disc_02_matt_gray',0),'a_disc2':('front_disc_02_matt_gray',2),'a_hub':('front_hub_01',0),'a_hub2':('front_hub_01',2),'a_nuts':('front_nuts_01_steel',0),'a_nuts2':('front_nuts_01_steel',2),'b_tire':('1',0),'b_disc':('rear_disc_01_matt_gray',0),'b_hub':('rear_hub_01',0),'b_nuts':('rear_nuts_01_steel',0)}
    for cat,(name,offset) in bus_wheels.items():
        target=cat[:-1] if cat.endswith('2') else cat
        bus_acc.append((cat,'vehicle_wheel_accessory',f'/def/vehicle/{target}/{name}.sii',offset))
    bus_preset='SiiNunit\n{\nvehicle : .bus {\n'+''.join(f' accessories[]: .{n}\n' for n,*_ in bus_acc)+'}\n'
    for item in bus_acc:
        name,typ,path,*offset=item
        bus_preset+=f'{typ} : .{name} {{\n data_path: "{path if path.startswith("/") else "/"+bus_prefix+path}"\n'+(f' offset: {offset[0]}\n' if offset else '')+'}\n'
    bus_preset+='}\n'
    # Keep quick jobs disabled until boarding and animated doors are verified.
    for where in ('bus_dealer/adl/adl_e6m.sii','bus_desktop/adl.e6m.sii'):
        put('def/vehicle/'+where,bus_preset)
    for old_root in (BASE,ROOT/'work/tools/conversion/rsrc/e6m/@cache'):
        obsolete=old_root/'def/vehicle/bus_line/adl_e6m.sii'
        obsolete.unlink(missing_ok=True)
    put('manifest.sii','''SiiNunit
{
mod_package : .e6m_package {
 package_version: "VERSION_PLACEHOLDER"
 display_name: "KMB ADL Enviro500 MMC E6M - conversion prototype"
 author: "Original OMSI asset authors; local ETS2 conversion"
 category[]: "truck"
 description_file: "mod_description.txt"
}
}
'''.replace('VERSION_PLACEHOLDER',VERSION))
    put('mod_description.txt','''KMB ADL Enviro500 MMC E6M - local conversion prototype.
Right-hand-drive bus, original body and interior. 14.8 t, three axles,
Cummins ISL9 torque curve and ZF EcoLife ratios from the installed OMSI package.
Uses stock ETS2 wheel accessories and temporary Scania/default sounds.
Cab switches, destination displays, doors, mirrors and dashboard animations
are not yet ported. Use the route advisor for speed and gear information.
Truck prototype: Access Mod Dealer > Scania > ADL E6M.
Coach mode: select Coaches mode and look in the ADL bus dealer for E6M.
Original model and texture authors retain their rights.
''')
    print('Vehicle definitions written',BASE)

if __name__=='__main__': main()
