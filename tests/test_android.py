import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'profiles/android'


class AndroidContract(unittest.TestCase):
    def test_compose_mapping(self):
        src = ANDROID / 'sample/app/src/main/java/labs/gnuin/gnosixds'
        self.assertIn('GnosixColors.', (src / 'ReferenceScreen.kt').read_text())
        self.assertIn('stateDescription', (src / 'ReferenceScreen.kt').read_text())
        self.assertIn('R.font.space_grotesk', (src / 'GnosixTheme.kt').read_text())
        self.assertIn('pending', (src / 'StateProjection.kt').read_text())
        self.assertIn('2026.09.00', (ANDROID / 'sample/app/build.gradle.kts').read_text())
        self.assertEqual(json.loads((ANDROID / 'status.json').read_text())['status'], 'mapped')
        self.assertTrue((ANDROID / 'sample/app/src/main/res/font/space_grotesk.ttf').is_file())

    def test_no_unbacked_verification(self):
        from tools.contract import validate_package
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'manifest.json').write_text(json.dumps({'version':'3.0.0','contract_digest':'','files':[]}))
            p = root / 'profiles/android/status.json'
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'profile':'android','status':'verified','evidence':[]}))
            self.assertTrue(any('verified requires evidence' in e for e in validate_package(root)))
