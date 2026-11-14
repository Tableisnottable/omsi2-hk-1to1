"""Regression checks for road/terrain contact; no game or downloaded inputs."""
import importlib.util
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('road_repair', Path(__file__).parents[1]/'Repair-TsingYi-Roads.py')
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class RoadContactTests(unittest.TestCase):
    def fixture(self, root, second_height=4.75):
        folder = root/'maps/HK_TsingYi'; folder.mkdir(parents=True)
        (folder/'build_manifest.json').write_text('{}',encoding='utf-8')
        (folder/'global.cfg').write_text('[NextIDCode]\n3\n[map]\n0\n0\ntile_0_0.map\n[map]\n1\n0\ntile_1_0.map\n',encoding='utf-16')
        profile = root/'Splines/HK_TsingYi/road.sli'; profile.parent.mkdir(parents=True)
        profile.write_text('[heightprofile]\n-3\n3\n0.08\n0.08\n',encoding='ascii')
        (profile.parent/'texture').mkdir()
        (profile.parent/'texture/asphalt.bmp').write_bytes(b'test-texture')
        for tx, oid, x, y, z, heading, length, grade in (
                (0,1,285,100,4,90,15,5), (1,2,0,100,second_height,0,20,-2)):
            rows = ['[version]',14,'[spline]',0,'Splines\\HK_TsingYi\\road.sli',
                    oid,0,0,x,z,y,heading,length,0,grade,grade,0,0,0,0,0,'']
            (folder/f'tile_{tx}_0.map').write_text('\n'.join(map(str,rows)),encoding='utf-16')
            (folder/f'tile_{tx}_0.map.terrain').write_bytes(struct.pack('<I3721f',60,*([50.]*3721)))

    def terrain(self, root, x, y):
        tx,ty=math.floor(x/300),math.floor(y/300)
        raw=(root/f'maps/HK_TsingYi/tile_{tx}_{ty}.map.terrain').read_bytes()
        data=struct.unpack('<3721f',raw[4:])
        u,v=(x-tx*300)/5,(y-ty*300)/5
        i,j=int(u),int(v); u-=i; v-=j
        z00,z10,z01,z11=[data[(j+dy)*61+i+dx] for dx,dy in ((0,0),(1,0),(0,1),(1,1))]
        # Independently evaluate BOTH possible terrain triangle diagonals.
        first=z00+(z10-z00)*u+(z11-z10)*v if u>=v else z00+(z11-z01)*u+(z01-z00)*v
        second=z00+(z10-z00)*u+(z01-z00)*v if u+v<=1 else z11+(z01-z11)*(1-u)+(z10-z11)*(1-v)
        return max(first,second)

    def test_sloped_road_and_bend_stay_above_terrain_including_tile_seam(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root)
            result=repair.repair(root)
            self.assertGreater(result['terrain_vertices_lowered'],0)
            self.assertGreater(result['uncovered_join_polygons'],0)
            for i in range(60):
                x=285.1+i*.24
                for y in (97.1,99.3,102.9):
                    self.assertLessEqual(self.terrain(root,x,y),4+(x-285)*.05+.08-.249)
            for y in (100.1,106.7,119.9):
                for x in (297.1,299.8,302.9):
                    self.assertLessEqual(self.terrain(root,x,y),4.75-(y-100)*.02+.08-.249)
            self.assertLessEqual(self.terrain(root,301,98.5),4.75+.08-.249)
            a=struct.unpack('<3721f',(root/'maps/HK_TsingYi/tile_0_0.map.terrain').read_bytes()[4:])
            b=struct.unpack('<3721f',(root/'maps/HK_TsingYi/tile_1_0.map.terrain').read_bytes()[4:])
            self.assertEqual([a[j*61+60] for j in range(61)],[b[j*61] for j in range(61)])

    def test_fill_only_uncovered_gap_and_never_join_different_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root)
            _,_,roads,nodes=repair.inventory(root,repair.load_helper())
            patches=repair.connectors(nodes)
            self.assertAlmostEqual(sum(repair.area(p) for p,_ in patches),4.5,places=5)
            for poly,_ in patches:
                x=sum(p[0] for p in poly)/len(poly); y=sum(p[1] for p in poly)/len(poly)
                for road in roads:
                    along=(x-road['a'][0])*road['dx']+(y-road['a'][1])*road['dy']
                    side=(x-road['a'][0])*road['dy']-(y-road['a'][1])*road['dx']
                    self.assertFalse(.0001<along<road['length']-.0001 and road['left']+.0001<side<road['right']-.0001)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root,second_height=20)
            _,_,_,nodes=repair.inventory(root,repair.load_helper())
            self.assertEqual(repair.connectors(nodes),[])

    def test_rerun_keeps_road_ids_surfaces_and_clearance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root)
            first=repair.repair(root); second=repair.repair(root)
            self.assertEqual(second['terrain_vertices_lowered'],0)
            self.assertEqual(first['surface_object_ids'],second['surface_object_ids'])
            helper=repair.load_helper()
            self.assertEqual(sum(helper.read(p).count('[object]') for p in (root/'maps/HK_TsingYi').glob('*.map')),len(first['surface_object_ids']))
            self.assertEqual([r['id'] for r in repair.inventory(root,helper)[2]],[1,2])
            for key in first['surface_object_ids']:
                self.assertIn('[surface]',helper.read(root/f'Sceneryobjects/HK_TsingYi/road_join_{key}.sco'))


if __name__=='__main__':
    unittest.main()
