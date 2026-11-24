"""Run under a display, for example the GTK Broadway backend."""

import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from worklock.app import Gdk, WorkLock


def png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


PNG = (b"\x89PNG\r\n\x1a\n"
       + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
       + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
       + png_chunk(b"IEND", b""))


class GuiTests(unittest.TestCase):
    def test_curtain_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(PNG)
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
                app = WorkLock()
                self.assertTrue(app.register(None))
                app.activate()
                app.image_path = str(image) + ".missing"
                app.password.set_text("секрет")
                app.confirm.set_text("секрет")
                app.start_curtain()
                self.assertIsNone(app.verifier)
                self.assertEqual(app.message.get_text(), "Не удалось открыть изображение")
                app.image_path = str(image)
                app.start_curtain()
                self.assertIsNotNone(app.verifier, app.message.get_text())
                self.assertGreaterEqual(len(app.curtains), 1)
                app.activate()
                self.assertFalse(app.settings.get_visible())
                window = app.curtains[0]
                self.assertFalse(window.panel.get_visible())
                window.on_key(None, ord("a"), 0, 0)
                self.assertTrue(window.panel.get_visible())
                self.assertEqual(window.entry.get_text(), "")
                self.assertTrue(window.on_close())
                self.assertTrue(window.on_key(None, Gdk.KEY_Escape, 0, 0))
                self.assertFalse(window.panel.get_visible())
                window.show_prompt()
                window.entry.set_text("неверно")
                window.try_unlock()
                self.assertIsNotNone(app.verifier)
                window.entry.set_text("секрет")
                window.try_unlock()
                self.assertIsNone(app.verifier)
                self.assertEqual(len(app.curtains), 0)
                self.assertEqual(app.password.get_text(), "")
                app.settings.destroy()


if __name__ == "__main__":
    unittest.main()
