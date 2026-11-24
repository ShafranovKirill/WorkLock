import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from worklock import config
from worklock.password import PasswordVerifier


class PasswordConfigTests(unittest.TestCase):
    def test_password_verifier(self):
        verifier = PasswordVerifier("длинный пароль")
        self.assertTrue(verifier.verify("длинный пароль"))
        self.assertFalse(verifier.verify("другой пароль"))
        with self.assertRaises(ValueError):
            PasswordVerifier("")

    def test_config_contains_no_password_and_is_private(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                config.save("/tmp/photo.png", True)
                path = Path(directory) / "worklock" / "settings.json"
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(config.load(), {"image_path": "/tmp/photo.png", "keep_awake": True})
                self.assertEqual(set(json.loads(path.read_text())), {"image_path", "keep_awake"})


if __name__ == "__main__":
    unittest.main()
