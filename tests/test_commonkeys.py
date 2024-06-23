# "test_commonkeys.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import unittest

from libWiiPy import title


class TestCommonKeys(unittest.TestCase):
    def test_common(self):
        self.assertEqual(title.get_common_key(0), b'\xeb\xe4*"^\x85\x93\xe4H\xd9\xc5Es\x81\xaa\xf7')

    def test_korean(self):
        self.assertEqual(title.get_common_key(1), b'c\xb8+\xb4\xf4aN.\x13\xf2\xfe\xfb\xbaL\x9b~')

    def test_vwii(self):
        self.assertEqual(title.get_common_key(2), b'0\xbf\xc7n|\x19\xaf\xbb#\x1630\xce\xd7\xc2\x8d')


if __name__ == '__main__':
    unittest.main()
