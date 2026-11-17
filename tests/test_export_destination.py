import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collections import namedtuple

from build_upload_package import output_directory, require_export_space


class ExportDestinationTests(unittest.TestCase):
    def test_default_boundary_is_retained(self):
        root=Path(tempfile.gettempdir())/'export-test-project'
        self.assertEqual(output_directory(root/'dist'/'fresh',None,root),(root/'dist'/'fresh').resolve())
        with self.assertRaisesRegex(ValueError,'dist/'):
            output_directory(root.parent/'elsewhere',None,root)

    def test_external_destination_is_fresh_absolute_and_nonoverlapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent=Path(temporary)
            root=parent/'input'
            target=parent/'new-export'
            self.assertEqual(output_directory(None,target,root),target.resolve())
            self.assertFalse(target.exists())
            with self.assertRaises(ValueError):output_directory(None,Path('relative'),root)
            with self.assertRaises(ValueError):output_directory(None,root/'child',root)
            with self.assertRaises(ValueError):output_directory(None,parent,root)
            target.mkdir()
            with self.assertRaisesRegex(ValueError,'fresh directory'):output_directory(None,target,root)

    def test_low_space_fails_before_creating_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'not-created'
            usage=namedtuple('Usage','total used free')
            with patch('build_upload_package.shutil.disk_usage',return_value=usage(100,99,1)):
                with self.assertRaisesRegex(OSError,'No export files'):
                    require_export_space(target,{'files':[{'path':'index.html','size_bytes':1000}]})
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
