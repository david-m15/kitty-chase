import json
import unittest
from pathlib import Path


class PlatformManifestTests(unittest.TestCase):
    def test_all_requested_platforms_exist(self):
        manifest = json.loads(Path("platform_capabilities.json").read_text("utf-8"))
        platforms = manifest["platforms"]
        expected = {
            "Windows",
            "Ubuntu",
            "Fedora",
            "Debian",
            "CentOS",
            "Android",
            "iOS",
            "iPadOS",
            "watchOS",
            "tvOS",
            "FreeBSD",
            "Solaris",
            "BOSS Linux",
            "HarmonyOS",
            "Fuchsia",
            "QNX",
            "AIX (IBM)",
            "HP-UX (Hewlett Packard)",
            "IRIX (SGI)",
            "ReactOS",
            "OpenVMS",
            "macOS",
        }
        self.assertTrue(expected.issubset(set(platforms.keys())))

    def test_wave_assignments(self):
        manifest = json.loads(Path("platform_capabilities.json").read_text("utf-8"))
        platforms = manifest["platforms"]
        self.assertEqual(platforms["watchOS"]["wave"], 2)
        self.assertEqual(platforms["IRIX (SGI)"]["wave"], 4)
        for distro in ["Ubuntu", "Fedora", "Debian", "CentOS", "BOSS Linux"]:
            self.assertEqual(platforms[distro]["wave"], 1)


if __name__ == "__main__":
    unittest.main()

