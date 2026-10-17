import unittest
from timeline import Timeline

class EventTests(unittest.TestCase):
    def test_blackout_reveal_remove_recover(self):
        m=Timeline(4); m.haunt('windows')
        self.assertEqual(m.house_light,1)
        m.now=1.2; self.assertAlmostEqual(m.house_light,.5)
        m.now=2.4; self.assertEqual(m.house_light,0)
        m.now=2.4; self.assertEqual(m.flash,1)
        self.assertTrue(all(m.ghost_strength(i)==1 for i in range(7)))
        m.now=7.8; self.assertEqual(m.flash,1); self.assertEqual(m.ghost_strength(0),0)
        m.now=14.5; self.assertAlmostEqual(m.house_light,.5)
        m.now=19; self.assertEqual(m.house_light,1)
    def test_door_open_pause_close_and_lock(self):
        m=Timeline(2); m.haunt('door')
        self.assertFalse(m.haunt('shadow'))
        for t,expected in ((0,0),(2.5,.5),(5,1),(8,1),(10.5,.5),(12,0)):
            m.now=t; self.assertAlmostEqual(m.door_open,expected)
        m.update(5,7); self.assertIsNone(m.event)
        self.assertGreaterEqual(m.next_haunt-m.now,180)
    def test_demo_all_variants(self):
        m=Timeline(1,True)
        for _ in range(2700): m.update(1/15,7)
        for k in m.durations: self.assertGreater(m.counts[k],0)
    def test_two_hours_recovery_and_coverage(self):
        m=Timeline(42); seen=set(); transitions=0; previous=None; candle_pairs=set()
        for _ in range(108000):
            m.update(1/15,7)
            self.assertTrue(0<=m.house_light<=1); self.assertTrue(0<=m.flash<=1)
            self.assertTrue(0<=m.door_open<=1)
            self.assertLessEqual(sum(k!='bats' for k in m.minor),1)
            if m.event and m.event!=previous:
                if previous: self.assertNotEqual(m.event[0],previous[0])
                previous=m.event
            seen.update(i for i in range(7) if m.room_light(i)>0)
            candle_pairs.add(tuple(round(x,1) for x in m.candles))
        self.assertEqual(len(seen),7); self.assertGreater(len(candle_pairs),15)
        for k,v in m.counts.items(): self.assertGreater(v,0,k)
    def test_seed_reproducibility(self):
        a,b=Timeline(7),Timeline(7)
        for _ in range(1000): a.update(.1,7); b.update(.1,7)
        self.assertEqual(a.counts,b.counts); self.assertEqual(a.rooms,b.rooms)

if __name__=='__main__': unittest.main()
