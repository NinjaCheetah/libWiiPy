# "nus_test.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import hashlib
import unittest

import libWiiPy


class TestNUSDownloads(unittest.TestCase):
    def test_download_title(self):
        title = libWiiPy.title.download_title("0000000100000002", 513)
        title_hash = hashlib.sha1(title.dump_wad()).hexdigest()
        self.assertEqual(title_hash, "c5e25fdb1ae6921597058b9f07045be0b003c550")
        title = libWiiPy.title.download_title("0000000100000002", 513, wiiu_endpoint=True)
        title_hash = hashlib.sha1(title.dump_wad()).hexdigest()
        self.assertEqual(title_hash, "c5e25fdb1ae6921597058b9f07045be0b003c550")

    def test_download_tmd(self):
        tmd = libWiiPy.title.download_tmd("0000000100000002", 513)
        tmd_hash = hashlib.sha1(tmd).hexdigest()
        self.assertEqual(tmd_hash, "e8f9657d591b305e300c109b5641630aa4e2318b")
        tmd = libWiiPy.title.download_tmd("0000000100000002", 513, wiiu_endpoint=True)
        tmd_hash = hashlib.sha1(tmd).hexdigest()
        self.assertEqual(tmd_hash, "e8f9657d591b305e300c109b5641630aa4e2318b")
        with self.assertRaises(ValueError):
            libWiiPy.title.download_tmd("TEST_STRING")

    def test_download_ticket(self):
        ticket = libWiiPy.title.download_ticket("0000000100000002")
        ticket_hash = hashlib.sha1(ticket).hexdigest()
        self.assertEqual(ticket_hash, "7076891f96ad3e4a6148a4a308e4a12fc72cc4b5")
        ticket = libWiiPy.title.download_ticket("0000000100000002", wiiu_endpoint=True)
        ticket_hash = hashlib.sha1(ticket).hexdigest()
        self.assertEqual(ticket_hash, "7076891f96ad3e4a6148a4a308e4a12fc72cc4b5")
        with self.assertRaises(ValueError):
            libWiiPy.title.download_ticket("TEST_STRING")

    def test_download_cert(self):
        cert = libWiiPy.title.download_cert()
        self.assertIsNotNone(cert)
        cert = libWiiPy.title.download_cert(wiiu_endpoint=True)
        self.assertIsNotNone(cert)

    def test_download_content(self):
        content = libWiiPy.title.download_content("0000000100000002", 150)
        content_hash = hashlib.sha1(content).hexdigest()
        self.assertEqual(content_hash, "1f10abe6517d29950aa04c71b264c18d204ed363")
        content = libWiiPy.title.download_content("0000000100000002", 150, wiiu_endpoint=True)
        content_hash = hashlib.sha1(content).hexdigest()
        self.assertEqual(content_hash, "1f10abe6517d29950aa04c71b264c18d204ed363")
        with self.assertRaises(ValueError):
            libWiiPy.title.download_content("TEST_STRING", 150)
        with self.assertRaises(ValueError):
            libWiiPy.title.download_content("0000000100000002", -1)

    def test_download_contents(self):
        tmd = libWiiPy.title.TMD()
        tmd.load(libWiiPy.title.download_tmd("0000000100000002"))
        contents = libWiiPy.title.download_contents("0000000100000002", tmd)
        self.assertIsNotNone(contents)
        contents = libWiiPy.title.download_contents("0000000100000002", tmd, wiiu_endpoint=True)
        self.assertIsNotNone(contents)


if __name__ == '__main__':
    unittest.main()
