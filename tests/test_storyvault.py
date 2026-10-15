"""
Automated Unit Tests for StoryVault Core Components.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from storyvault.utils.url_parser import parse_url, URLType, decode_short_highlight_token
from storyvault.utils.file_namer import sanitize_filename, format_media_filename, get_unique_path
from storyvault.core.quality import is_video_format, is_audio_only, short_side, quality_key, build_format_selector
from storyvault.cookies.manual_importer import parse_netscape_file, validate_instagram_cookies
from storyvault.cookies.secure_store import save_encrypted_cookies, load_encrypted_cookies

class TestStoryVault(unittest.TestCase):

    def test_url_parser_canonical_highlight(self):
        url = "https://www.instagram.com/stories/highlights/17864939061644584/"
        res = parse_url(url)
        self.assertEqual(res.url_type, URLType.SINGLE_HIGHLIGHT)
        self.assertEqual(res.media_id, "17864939061644584")

    def test_url_parser_short_link(self):
        # Base64 for "highlight:17864939061644584"
        token = "aGlnaGxpZ2h0OjE3ODY0OTM5MDYxNjQ0NTg0"
        url = f"https://www.instagram.com/s/{token}"
        res = parse_url(url)
        self.assertEqual(res.url_type, URLType.SINGLE_HIGHLIGHT)
        self.assertEqual(res.media_id, "17864939061644584")

    def test_url_parser_single_story(self):
        url = "https://www.instagram.com/stories/johndoe/3216549871234567890/"
        res = parse_url(url)
        self.assertEqual(res.url_type, URLType.SINGLE_STORY)
        self.assertEqual(res.username, "johndoe")
        self.assertEqual(res.media_id, "3216549871234567890")

    def test_url_parser_user_stories(self):
        url = "https://www.instagram.com/stories/johndoe/"
        res = parse_url(url)
        self.assertEqual(res.url_type, URLType.USER_STORIES)
        self.assertEqual(res.username, "johndoe")

    def test_url_parser_username(self):
        res = parse_url("@johndoe")
        self.assertEqual(res.url_type, URLType.PROFILE_HIGHLIGHTS)
        self.assertEqual(res.username, "johndoe")

    def test_file_namer_sanitization(self):
        raw = "Şirin & Çiçekli / Fotoğraf: <Tatil> 2024?"
        cleaned = sanitize_filename(raw)
        self.assertNotIn(":", cleaned)
        self.assertNotIn("<", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertTrue(cleaned.startswith("Sirin"))

    def test_file_namer_formatting(self):
        name = format_media_filename("johndoe", "HL", 1, "ABC12345", "1080x1920", "mkv")
        self.assertEqual(name, "johndoe_HL_001_ABC12345_1080x1920.mkv")

    def test_quality_key_and_short_side(self):
        # 1080x1920 (Vertical 1080p)
        fmt_vertical = {"width": 1080, "height": 1920, "vcodec": "h264", "tbr": 4500}
        self.assertEqual(short_side(fmt_vertical), 1080)
        self.assertTrue(is_video_format(fmt_vertical))

        # 720x1280
        fmt_720 = {"width": 720, "height": 1280, "vcodec": "h264", "tbr": 2500}
        self.assertGreater(quality_key(fmt_vertical), quality_key(fmt_720))

    def test_format_selector_builder(self):
        s_max = build_format_selector("max")
        self.assertIn("1080", s_max)
        s_fast = build_format_selector("fast")
        self.assertIn("720", s_fast)

    def test_cookie_secure_store_roundtrip(self):
        dummy_cookies = [
            {"name": "sessionid", "value": "test_session_12345", "domain": ".instagram.com", "expires": 1999999999},
            {"name": "ds_user_id", "value": "987654321", "domain": ".instagram.com"}
        ]
        test_enc = Path("tests/test_session.enc")
        try:
            save_encrypted_cookies(dummy_cookies, custom_path=test_enc)
            loaded = load_encrypted_cookies(custom_path=test_enc)
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["value"], "test_session_12345")
        finally:
            if test_enc.exists():
                test_enc.unlink()

    def test_url_parser_single_story_with_query(self):
        url = "https://www.instagram.com/stories/alinaa.vslnk/4007756251391006478?utm_source=ig_story_item_share&mdxt=MTRtZnE0cmJ0bXd5dA=="
        res = parse_url(url)
        self.assertEqual(res.url_type, URLType.SINGLE_STORY)
        self.assertEqual(res.username, "alinaa.vslnk")
        self.assertEqual(res.media_id, "4007756251391006478")

    def test_parse_existing_cookies_txt(self):
        local_txt = Path("instagram_cookies.txt")
        if local_txt.exists():
            cookies = parse_netscape_file(local_txt)
            val = validate_instagram_cookies(cookies)
            self.assertTrue(val.is_valid, f"Cookie validation error: {val.error_message}")
            self.assertIsNotNone(val.user_id)

if __name__ == "__main__":
    unittest.main()
