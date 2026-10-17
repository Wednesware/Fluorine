import json
from pathlib import Path
import runpy
import unittest
import zipfile


class ReleaseTests(unittest.TestCase):
    def test_nitrogen_archive_layout_and_version(self):
        root = Path(__file__).resolve().parents[1]
        runpy.run_path(str(root / 'tools' / 'build_release.py'))
        version = (root / 'VERSION').read_text().strip()
        prefix = f'Fluorine-{version}/fluorine/'
        with zipfile.ZipFile(root / 'dist' / 'fluorine.zip') as archive:
            self.assertIn(prefix + '__init__.py', archive.namelist())
            metadata = json.loads(archive.read(prefix + '.nitropkg'))
            self.assertEqual(metadata['version'], version)
            self.assertEqual(metadata['name'], 'fluorine')
            self.assertFalse(any('__pycache__' in name for name in archive.namelist()))
            self.assertIn(f"__version__ = '{version}'", archive.read(prefix + '__init__.py').decode())
