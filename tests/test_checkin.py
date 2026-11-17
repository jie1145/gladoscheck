import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import checkin
from browser_checkin import checkin_in_page, is_checkin_response


def response(data=None, status=200):
    result = Mock(status_code=status)
    result.json.return_value = data
    return result


class ResultTests(unittest.TestCase):
    def test_errors_with_logged_or_already_are_not_success(self):
        for message in ("not logged in", "already failed", "repeat verification failed", "return tomorrow"):
            with self.subTest(message=message):
                self.assertEqual(checkin.checkin_outcome({"code": 1, "message": message}), "失败")

    def test_explicit_success_and_repeat(self):
        self.assertEqual(checkin.checkin_outcome({"code": 0}), "成功")
        self.assertEqual(checkin.checkin_outcome({"code": 0, "repeated": True}), "已签到")
        for result in (None, [], {}, {"code": False}, {"code": "0"}, {"code": 1, "repeated": True}):
            self.assertEqual(checkin.checkin_outcome(result), "失败")


class ChallengeTests(unittest.TestCase):
    def setUp(self):
        self.client = checkin.GLaDOS()
        self.client.s = Mock()

    def test_browser_challenge_does_not_send_invalid_checkin(self):
        for challenge in ({"code": 0, "nonce": "fake-nonce", "turnstile": "fake-sitekey"},
                          {"code": 0, "nonce": "fake-nonce"}):
            self.client.s.get.return_value = response(challenge)
            result = self.client.checkin()
            self.assertEqual(result["reason"], "browser-required")
            self.client.s.post.assert_not_called()

    def test_bad_or_unavailable_challenge_fails_closed(self):
        for challenge_response in (response({}, 503), response([]), response({"code": 0}),
                                   response({"code": -2, "message": "not logged in"})):
            self.client.s.get.return_value = challenge_response
            self.assertEqual(checkin.checkin_outcome(self.client.checkin()), "失败")
            self.client.s.post.assert_not_called()

    def test_non_json_challenge_is_not_submitted(self):
        self.client.s.get.return_value = response()
        self.client.s.get.return_value.json.side_effect = ValueError("invalid JSON")
        self.assertNotEqual(self.client.checkin()["code"], 0)
        self.client.s.post.assert_not_called()

    def test_legacy_without_challenge_preserves_server_result(self):
        self.client.s.get.return_value = response(status=404)
        self.client.s.post.return_value = response({"code": 0, "repeated": True})
        self.assertEqual(checkin.checkin_outcome(self.client.checkin()), "已签到")
        self.client.s.post.assert_called_once()

    def test_http_status_retries_do_not_include_post(self):
        client = checkin.GLaDOS()
        self.assertNotIn("POST", client.s.get_adapter("https://").max_retries.allowed_methods)

    def test_invalid_status_response_is_reported_without_crashing(self):
        for data in ([], {"code": 0}, {"code": 0, "data": []},
                     {"code": 0, "data": {"leftDays": "NaN"}}, {"code": -2, "message": None}):
            self.client.s.get.return_value = response(data)
            status, error = self.client.get_status()
            self.assertIsNone(status)
            self.assertTrue(error)


class MainTests(unittest.TestCase):
    def run_main(self, result, status_error=None):
        client = Mock()
        client.get_status.return_value = ({"email": "private@example.invalid", "vip": 0,
                                          "leftDays": 3, "traffic": 0, "cakeCount": 0}, status_error)
        client.checkin.return_value = result
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "summary.md"
            with patch.object(checkin, "load_accounts", return_value=([
                    {"name": "private@example.invalid", "cookie": "fake=fixture"}], "fixture")), \
                 patch.object(checkin, "GLaDOS", return_value=client), \
                 patch.object(checkin, "notify"), patch.object(checkin.time, "sleep"), \
                 patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}), \
                 contextlib.redirect_stdout(output):
                code = checkin.main()
            summary = summary_path.read_text(encoding="utf-8")
        self.assertNotIn("private@example.invalid", output.getvalue() + summary)
        return code, output.getvalue(), summary

    def test_failed_account_has_nonzero_exit_and_visible_summary(self):
        code, output, summary = self.run_main({"code": 1, "message": "Cloudflare verification failed"})
        self.assertEqual(code, 1)
        self.assertIn("0/1", output)
        self.assertIn("Cloudflare verification failed", summary)

    def test_status_failure_is_not_a_success(self):
        code, _, summary = self.run_main({}, "not logged in")
        self.assertEqual(code, 1)
        self.assertIn("0/1", summary)

    def test_success_and_repeat_have_zero_exit(self):
        for result in ({"code": 0, "message": "recorded", "points": 1},
                       {"code": 0, "message": "already checked in", "repeated": True}):
            code, _, summary = self.run_main(result)
            self.assertEqual(code, 0)
            self.assertIn("1/1", summary)

    def test_compatibility_entry_points_report_configuration_errors(self):
        environment = dict(os.environ, GLaDOS_COOKIES_JSON="invalid-json", GLADOS_COOKIES_JSON="")
        environment.pop("GITHUB_STEP_SUMMARY", None)
        for name in ("checkin.py", "glados.py", "test_local.py"):
            result = subprocess.run([sys.executable, name], cwd=Path(checkin.__file__).parent,
                                    env=environment, capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("配置错误", result.stdout)
            self.assertNotIn("ImportError", result.stderr)


class BrowserTests(unittest.TestCase):
    def test_only_first_party_checkin_post_is_a_result(self):
        for url, method, expected in (
            ("https://glados.cloud/api/user/checkin", "POST", True),
            ("https://glados.cloud/api/user/checkin", "GET", False),
            ("https://glados.cloud/api/user/checkin/challenge", "POST", False),
            ("https://example.invalid/api/user/checkin", "POST", False),
            ("http://glados.cloud/api/user/checkin", "POST", False),
        ):
            self.assertEqual(is_checkin_response(Mock(url=url, request=Mock(method=method))), expected)

    def test_browser_result_excludes_unnecessary_private_fields(self):
        page = Mock()
        api_response = Mock(status=200)
        api_response.json.return_value = {"code": 0, "points": 1, "email": "private@example.invalid",
                                          "nonce": "fixture", "turnstile": "fixture"}
        page.expect_response.return_value.__enter__ = Mock(return_value=Mock(value=api_response))
        page.expect_response.return_value.__exit__ = Mock(return_value=False)
        result = checkin_in_page(page, 1000)
        self.assertEqual(checkin.checkin_outcome(result), "成功")
        self.assertFalse({"email", "nonce", "turnstile"} & result.keys())


if __name__ == "__main__":
    unittest.main()
