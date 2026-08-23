#!/usr/bin/env python3
"""Focused tests for Telegram video delivery."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import telegram


class TelegramMediaTests(unittest.TestCase):
    def test_video_uses_send_video_with_caption(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            video = Path(raw) / "rules.mp4"
            video.write_bytes(b"video")
            completed = subprocess.CompletedProcess(
                [], 0, json.dumps({"ok": True, "result": {"message_id": 42}}), "")
            with patch.dict(os.environ, {
                "TELEGRAM_BOT_TOKEN": "token",
                "TELEGRAM_CHAT_DM": "default-chat",
            }, clear=False), patch.object(
                telegram.subprocess, "run", return_value=completed
            ) as run:
                message_id = telegram.send(
                    "<b>Overcap rules</b>", video=video, chat="journal-chat",
                    parse_mode="HTML")
            self.assertEqual(message_id, 42)
            command = run.call_args.args[0]
            self.assertIn("sendVideo", command[2])
            self.assertIn("chat_id=journal-chat", command)
            upload_arg = next(value for value in command if value.startswith("video=@"))
            self.assertFalse(Path(upload_arg[7:]).exists())
            self.assertIn("caption=<b>Overcap rules</b>", command)
            caption_index = command.index("caption=<b>Overcap rules</b>")
            self.assertEqual(command[caption_index - 1], "--form-string")

    def test_video_failure_is_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            video = Path(raw) / "rules.mp4"
            video.write_bytes(b"video")
            completed = subprocess.CompletedProcess(
                [], 0, json.dumps({"ok": False, "description": "bad video"}), "")
            with patch.dict(os.environ, {
                "TELEGRAM_BOT_TOKEN": "token",
                "TELEGRAM_CHAT_DM": "default-chat",
            }, clear=False), patch.object(
                telegram.subprocess, "run", return_value=completed
            ):
                with self.assertRaisesRegex(RuntimeError, "bad video"):
                    telegram.send("Overcap", video=video)

    def test_photo_and_video_are_mutually_exclusive(self) -> None:
        path = Path("media")
        with self.assertRaisesRegex(ValueError, "either photo or video"):
            telegram.send("invalid", photo=path, video=path)


if __name__ == "__main__":
    unittest.main()
