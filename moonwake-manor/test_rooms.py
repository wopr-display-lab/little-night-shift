"""Regression checks for room-wide masks and a shared light state."""
import json, unittest
from pathlib import Path
import pygame
from timeline import Timeline
A=Path(__file__).resolve().parent/'assets'
class RoomTests(unittest.TestCase):
    def setUp(self): self.rooms=json.loads((A/'scene.json').read_text())['rooms']
    def test_every_aperture_lights_and_assets_fit(self):
        self.assertEqual(len(self.rooms),7)
        for i,r in enumerate(self.rooms):
            mask=pygame.image.load(str(A/f'room-mask_{i}.png'))
            for name in ('mask','light','ghost','figure','curtain'):
                s=pygame.image.load(str(A/f'room-{name}_{i}.png'))
                self.assertEqual(s.get_size(),tuple(r['size']))
            for x,y in r['seeds']:
                self.assertEqual(mask.get_at((x-r['pos'][0],y-r['pos'][1])).a,255,(r['name'],x,y))
    def test_original_stone_frames_remain_unlit(self):
        for i,points in ((1,[(398,226),(421,225)]),(2,[(518,244)]),(3,[(611,240),(626,239)]),(5,[(523,348)]),(6,[(630,344)])):
            r=self.rooms[i]; mask=pygame.image.load(str(A/f'room-mask_{i}.png'))
            for x,y in points: self.assertEqual(mask.get_at((x-r['pos'][0],y-r['pos'][1])).a,0,(i,x,y))
    def test_one_timer_per_room_not_per_aperture(self):
        m=Timeline(10); m.next_haunt=10000
        for _ in range(2000): m.update(.2,len(self.rooms))
        self.assertEqual(len(m.rooms),7); self.assertEqual(len(m.flickers),7)
        self.assertEqual(len(m.room_due),7)
        self.assertGreater(sum(len(r['seeds']) for r in self.rooms),len(m.rooms))
        self.assertEqual(set(m.rooms),set(range(7)))
if __name__=='__main__': unittest.main()

