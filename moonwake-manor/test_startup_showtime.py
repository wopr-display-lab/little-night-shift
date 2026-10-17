import unittest
from timeline import Timeline
class StartupTests(unittest.TestCase):
 def test_once_then_calm(self):
  m=Timeline(42,startup_showtime=True)
  m.update(14.9,8)
  self.assertIsNone(m.event)
  m.update(.2,8)
  self.assertEqual(m.event[0],"windows")
  self.assertFalse(m.startup_showtime)
  m.update(3,8)
  self.assertEqual(m.house_light,0)
  self.assertEqual(m.ghost_strength(0),1)
  m.update(17,8)
  self.assertIsNone(m.event)
  self.assertEqual(m.house_light,1)
  self.assertGreaterEqual(m.next_haunt,m.now+180)
  m.update(100,8)
  self.assertEqual(m.counts["windows"],1)
 def test_opt_out_and_demo(self):
  m=Timeline(42)
  self.assertGreaterEqual(m.next_haunt,180)
  m=Timeline(42,True,startup_showtime=True)
  self.assertEqual(m.next_haunt,12)
if __name__=="__main__":unittest.main()
