import base64
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import unittest
from unittest import mock

from workshop.errors import WorkshopError
from workshop.runtime.browser_login import (
    DEFAULT_CREDENTIAL_EXCHANGE_URL,
    DEFAULT_INVENTOR_LOGIN_URL,
    FactoryBrowserLogin,
    INVENTOR_LOGIN_URL_ENV,
    BrowserLoginCredential,
    _exchange_authorization_code,
)


class _Response:
    def __init__(self, body, status=200):
        self.status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def read(self, _maximum):
        return self._body


class FactoryBrowserLoginTest(unittest.TestCase):
    @staticmethod
    def _callback_url(callback_url, state, code="a" * 43):
        return callback_url + "?" + urllib.parse.urlencode(
            {"code": code, "state": state}
        )

    @classmethod
    def _get(cls, callback_url, state, code="a" * 43):
        return urllib.request.urlopen(
            cls._callback_url(callback_url, state, code),
            timeout=2,
        )

    def test_browser_redirect_returns_code_and_cli_exchanges_with_pkce(self):
        opened = []
        exchanged = []

        def exchange(code, verifier):
            exchanged.append((code, verifier))
            return BrowserLoginCredential(
                username="khoa",
                password="long-lived-agent-password",
            )

        login_url = "http://127.0.0.1:3000/toys/inventor/login"
        with FactoryBrowserLogin(
            inventor_id="pico-press",
            login_url=login_url,
            opener=lambda url: opened.append(url) or True,
            exchanger=exchange,
        ) as login:
            authorization_url = login.authorization_url
            parsed = urllib.parse.urlsplit(authorization_url)
            query = urllib.parse.parse_qs(parsed.query)
            callback_url = query["callback_url"][0]
            state = query["state"][0]
            challenge = query["code_challenge"][0]

            self.assertEqual(parsed.path, "/toys/inventor/login")
            self.assertEqual(query["inventor_id"], ["pico-press"])
            self.assertEqual(query["code_challenge_method"], ["S256"])
            self.assertEqual(len(challenge), 43)
            self.assertNotIn("code_verifier", query)
            self.assertTrue(callback_url.startswith("http://127.0.0.1:"))
            self.assertTrue(login.open_browser())
            self.assertEqual(opened, [authorization_url])

            code = "b" * 43
            with self._get(callback_url, state, code) as response:
                self.assertEqual(response.status, 200)
                body = response.read().decode("utf-8")
                self.assertIn("Inventor connected", body)
                self.assertNotIn(code, body)
                self.assertNotIn("long-lived-agent-password", body)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
            credential = login.wait(timeout_seconds=1)

        self.assertEqual(credential.username, "khoa")
        self.assertEqual(credential.password, "long-lived-agent-password")
        self.assertNotIn("long-lived-agent-password", repr(credential))
        self.assertEqual(exchanged[0][0], code)
        verifier = exchanged[0][1]
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(expected, challenge)
        self.assertNotIn(verifier, authorization_url)

    def test_wrong_state_and_malformed_code_do_not_consume_callback(self):
        exchanged = []
        login_url = "http://127.0.0.1:3000/toys/inventor/login"
        with FactoryBrowserLogin(
            inventor_id="pico-press",
            login_url=login_url,
            exchanger=lambda code, verifier: exchanged.append((code, verifier))
            or BrowserLoginCredential("khoa", "valid-password"),
        ) as login:
            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(login.authorization_url).query
            )
            callback_url = query["callback_url"][0]
            state = query["state"][0]
            with self.assertRaises(urllib.error.HTTPError) as wrong_state:
                self._get(callback_url, "wrong-state")
            self.assertEqual(wrong_state.exception.code, 400)
            with self.assertRaises(urllib.error.HTTPError) as malformed_code:
                self._get(callback_url, state, "not-a-valid-code")
            self.assertEqual(malformed_code.exception.code, 400)
            self.assertEqual(exchanged, [])

            with self._get(callback_url, state):
                pass
            self.assertEqual(login.wait(timeout_seconds=1).username, "khoa")
        self.assertEqual(len(exchanged), 1)

    def test_post_and_wrong_path_do_not_consume_callback(self):
        exchanged = []
        with FactoryBrowserLogin(
            inventor_id="pico-press",
            login_url="http://127.0.0.1:3000/toys/inventor/login",
            exchanger=lambda code, verifier: exchanged.append((code, verifier))
            or BrowserLoginCredential("khoa", "valid-password"),
        ) as login:
            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(login.authorization_url).query
            )
            callback_url = query["callback_url"][0]
            state = query["state"][0]
            with self.assertRaises(urllib.error.HTTPError) as wrong_path:
                urllib.request.urlopen(
                    self._callback_url(
                        callback_url.replace("/callback", "/wrong"), state
                    ),
                    timeout=2,
                )
            self.assertEqual(wrong_path.exception.code, 404)
            with self.assertRaises(urllib.error.HTTPError) as post:
                urllib.request.urlopen(
                    urllib.request.Request(
                        callback_url,
                        data=b"credential=must-not-be-accepted",
                        method="POST",
                    ),
                    timeout=2,
                )
            self.assertEqual(post.exception.code, 405)
            self.assertEqual(exchanged, [])
            with self._get(callback_url, state):
                pass
            self.assertEqual(login.wait(timeout_seconds=1).username, "khoa")

    def test_exchange_failure_is_reported_without_secret_response(self):
        secret = "server-secret-must-not-render"

        def rejected(_code, _verifier):
            raise WorkshopError(secret)

        with FactoryBrowserLogin(
            inventor_id="pico-press",
            login_url="http://127.0.0.1:3000/toys/inventor/login",
            exchanger=rejected,
        ) as login:
            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(login.authorization_url).query
            )
            with self.assertRaises(urllib.error.HTTPError) as callback:
                self._get(query["callback_url"][0], query["state"][0])
            self.assertEqual(callback.exception.code, 502)
            self.assertNotIn(secret, callback.exception.read().decode("utf-8"))
            with self.assertRaisesRegex(WorkshopError, secret):
                login.wait(timeout_seconds=1)

    def test_default_exchange_posts_code_and_verifier_to_factory_api(self):
        sent = {}

        def fake_urlopen(request, timeout):
            sent["url"] = request.full_url
            sent["body"] = request.data
            sent["timeout"] = timeout
            return _Response(
                json.dumps(
                    {"username": "khoa", "password": "generated-password"}
                ).encode("utf-8")
            )

        with mock.patch(
            "workshop.runtime.browser_login.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            credential = _exchange_authorization_code("c" * 43, "d" * 43)

        self.assertEqual(sent["url"], DEFAULT_CREDENTIAL_EXCHANGE_URL)
        self.assertNotIn("c" * 43, sent["url"])
        self.assertEqual(
            json.loads(sent["body"]),
            {"code": "c" * 43, "code_verifier": "d" * 43},
        )
        self.assertEqual(credential.username, "khoa")
        self.assertEqual(credential.password, "generated-password")

    def test_malformed_exchange_response_fails_closed(self):
        with mock.patch(
            "workshop.runtime.browser_login.urllib.request.urlopen",
            return_value=_Response(b'{"username":"khoa"}'),
        ):
            with self.assertRaisesRegex(WorkshopError, "password"):
                _exchange_authorization_code("c" * 43, "d" * 43)

    def test_default_authorization_page_is_production_autonomous(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with FactoryBrowserLogin(
                inventor_id="pico-press",
                exchanger=lambda _code, _verifier: BrowserLoginCredential(
                    "khoa", "password"
                ),
            ) as login:
                parsed = urllib.parse.urlsplit(login.authorization_url)
        production = urllib.parse.urlsplit(DEFAULT_INVENTOR_LOGIN_URL)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, production.netloc)
        self.assertEqual(parsed.path, "/toys/inventor/login")

    def test_environment_can_override_login_page_for_local_development(self):
        local_url = "http://localhost:3000/de-DE/toys/inventor/login"
        with mock.patch.dict(os.environ, {INVENTOR_LOGIN_URL_ENV: local_url}):
            with FactoryBrowserLogin(
                inventor_id="pico-press",
                opener=lambda _url: False,
            ) as login:
                self.assertTrue(login.authorization_url.startswith(local_url + "?"))

    def test_environment_cannot_override_login_page_with_remote_host(self):
        with mock.patch.dict(
            os.environ,
            {INVENTOR_LOGIN_URL_ENV: "https://attacker.example/login"},
        ):
            with self.assertRaisesRegex(WorkshopError, "may only target localhost"):
                FactoryBrowserLogin(inventor_id="pico-press")

    def test_rejects_noncanonical_inventor_id(self):
        with self.assertRaisesRegex(WorkshopError, "canonical slug"):
            FactoryBrowserLogin(inventor_id="Pico Press")


if __name__ == "__main__":
    unittest.main()
