"""Functional HTTP tests against a locally running DataPilot API.

Run from the project root after:
    docker compose up --build

Then:
    python tests/functional/routes.py

The test uses requests.Session so authentication cookies behave like a browser.
Only verification-code setup talks directly to Redis; all application behavior
is exercised through real HTTP routes.
"""

from __future__ import annotations

import io
import os
import time
import unittest
from uuid import uuid4

import requests
from redis import Redis


BASE_URL = os.getenv("FUNCTIONAL_BASE_URL", "http://localhost:8000").rstrip("/")
REDIS_HOST = os.getenv("FUNCTIONAL_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("FUNCTIONAL_REDIS_PORT", "6379"))
REQUEST_TIMEOUT = float(os.getenv("FUNCTIONAL_REQUEST_TIMEOUT", "30"))


class DataPilotFunctionalRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = requests.Session()
        cls.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        cls._wait_for_api()

        suffix = uuid4().hex[:10]
        cls.email = f"datapilot.functional.{suffix}@gmail.com"
        cls.username = f"functional_{suffix}"
        cls.password = "DataPilot123!"
        cls.code = "123456"

        cls.data_source_id: int | None = None
        cls.conversation_id: int | None = None
        cls.message_id: int | None = None
        cls.dashboard_id: int | None = None

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.redis.delete(f"create_account:{cls.email}")
            cls.redis.delete(f"auth2:{cls.email}")
        finally:
            cls.redis.close()
            cls.session.close()

    @classmethod
    def _wait_for_api(cls) -> None:
        deadline = time.time() + 90
        last_error: Exception | None = None

        while time.time() < deadline:
            try:
                response = cls.session.get(
                    f"{BASE_URL}/users/",
                    timeout=3,
                )
                if response.status_code in {200, 401}:
                    return
            except requests.RequestException as error:
                last_error = error

            time.sleep(1)

        raise RuntimeError(
            f"DataPilot API did not become ready at {BASE_URL}"
        ) from last_error

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        response = self.session.request(
            method,
            f"{BASE_URL}{path}",
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )

        if response.status_code >= 500:
            self.fail(
                f"{method} {path} returned {response.status_code}: "
                f"{response.text}"
            )

        return response

    def assert_status(
        self,
        response: requests.Response,
        expected: int | set[int],
    ) -> None:
        expected_set = {expected} if isinstance(expected, int) else expected
        self.assertIn(
            response.status_code,
            expected_set,
            msg=(
                f"Unexpected status {response.status_code}. "
                f"Body: {response.text}"
            ),
        )

    def test_01_private_route_requires_authentication(self) -> None:
        isolated = requests.Session()
        try:
            response = isolated.get(
                f"{BASE_URL}/users/",
                timeout=REQUEST_TIMEOUT,
            )
        finally:
            isolated.close()

        self.assert_status(response, 401)
        self.assertEqual(
            response.json()["detail"],
            "Authentication token required",
        )

    def test_02_invalid_login_is_rejected(self) -> None:
        response = self.request(
            "POST",
            "/auth/",
            json={
                "identifier": self.email,
                "password": "WrongPassword123!",
            },
        )
        self.assert_status(response, 401)

    def test_03_create_user_and_receive_http_only_session(self) -> None:
        self.redis.set(
            f"create_account:{self.email}",
            self.code,
            ex=60,
        )

        response = self.request(
            "POST",
            "/users/",
            json={
                "name": "Functional Test",
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "age": 18,
                "gender": "PREFIRO NÃO DIZER",
                "profile_image": None,
                "auth2": False,
                "code": self.code,
            },
        )

        self.assert_status(response, 201)
        payload = response.json()

        self.assertTrue(payload["authenticated"])
        self.assertFalse(payload["auth2_required"])
        self.assertIn("access_token", self.session.cookies)
        self.assertIn("refresh_token", self.session.cookies)

        set_cookie = response.headers.get("set-cookie", "").lower()
        self.assertIn("httponly", set_cookie)

    def test_04_get_and_update_current_user(self) -> None:
        response = self.request("GET", "/users/")
        self.assert_status(response, 200)

        user = response.json()
        self.assertEqual(user["email"], self.email)
        self.assertEqual(user["username"], self.username.lower())
        self.assertNotIn("password", user)

        response = self.request(
            "PATCH",
            "/users/",
            json={"name": "Functional Updated"},
        )
        self.assert_status(response, 200)
        self.assertEqual(response.json()["name"], "Functional Updated")

    def test_05_upload_and_read_file_data_source(self) -> None:
        csv_content = (
            "produto,valor,quantidade\n"
            "Notebook,5000,2\n"
            "Mouse,150,10\n"
            "Teclado,300,4\n"
        ).encode()

        response = self.request(
            "POST",
            "/data-sources/file",
            data={"name": "Functional CSV"},
            files={
                "file": (
                    "functional.csv",
                    io.BytesIO(csv_content),
                    "text/csv",
                )
            },
        )

        self.assert_status(response, 201)
        source = response.json()["data_source"]

        self.__class__.data_source_id = int(source["id"])
        self.assertEqual(source["row_count"], 3)
        self.assertEqual(source["column_count"], 3)
        self.assertEqual(source["source_type"], "file")

        response = self.request("GET", "/data-sources/")
        self.assert_status(response, 200)
        self.assertGreaterEqual(response.json()["count"], 1)

        response = self.request(
            "GET",
            f"/data-sources/{self.data_source_id}",
        )
        self.assert_status(response, 200)
        self.assertEqual(
            response.json()["data_source"]["id"],
            self.data_source_id,
        )

    def test_06_data_agent_uses_fake_openai_in_test_mode(self) -> None:
        self.assertIsNotNone(self.data_source_id)

        response = self.request(
            "POST",
            "/agents/data",
            json={
                "data_source_id": self.data_source_id,
                "question": "Qual produto tem maior valor?",
                "history": [],
            },
        )

        self.assert_status(response, 200)
        output = response.json()["output"]
        self.assertIn("Resposta de teste", output)

    def test_07_chat_agent_uses_fake_openai(self) -> None:
        response = self.request(
            "POST",
            "/agents/chat",
            json={
                "question": "Explique o DataPilot em uma frase.",
                "history": [],
            },
        )

        self.assert_status(response, 200)
        self.assertIn(
            "Nenhuma requisição foi enviada para a OpenAI",
            response.json()["output"],
        )

    def test_08_dashboard_handoff_and_analysis_by_id(self) -> None:
        csv_content = (
            "produto,valor\n"
            "Notebook,5000\n"
            "Mouse,150\n"
            "Teclado,300\n"
        ).encode()

        response = self.request(
            "POST",
            "/agents/dashboard",
            data={
                "prompt": "Crie um dashboard simples com os produtos.",
            },
            files={
                "file": (
                    "dashboard.csv",
                    io.BytesIO(csv_content),
                    "text/csv",
                )
            },
        )

        self.assert_status(response, 200)
        dashboard = response.json()

        self.assertIn("analysis_id", dashboard)
        self.assertEqual(
            dashboard["user_order"],
            "Crie um dashboard simples com os produtos.",
        )
        self.assertTrue(dashboard["charts"])
        self.assertIn(dashboard["engine"], {"polars", "spark"})

        response = self.request(
            "POST",
            "/agents/analysis",
            json={
                "analysis_id": dashboard["analysis_id"],
                "question": "Resuma o dashboard.",
                "history": [],
            },
        )

        self.assert_status(response, 200)
        analysis = response.json()

        self.assertEqual(
            analysis["analysis_id"],
            dashboard["analysis_id"],
        )
        self.assertIn("Resposta de teste", analysis["output"])

    def test_09_create_conversation_and_message(self) -> None:
        response = self.request(
            "POST",
            "/conversations/",
            json={"title": "Functional conversation"},
        )
        self.assert_status(response, 201)

        conversation = response.json()
        self.__class__.conversation_id = int(conversation["id"])

        response = self.request(
            "POST",
            "/messages/",
            json={
                "conversation_id": self.conversation_id,
                "role": "user",
                "content": "Mensagem funcional",
            },
        )
        self.assert_status(response, 201)

        message = response.json()
        self.__class__.message_id = int(message["id"])

        response = self.request(
            "GET",
            f"/messages/?conversation_id={self.conversation_id}",
        )
        self.assert_status(response, 200)

    def test_10_create_dashboard_record_linked_to_source(self) -> None:
        self.assertIsNotNone(self.data_source_id)

        response = self.request(
            "POST",
            "/dashboards/",
            json={
                "title": "Functional dashboard",
                "prompt": "Functional prompt",
                "data_source_id": self.data_source_id,
                "is_outdated": False,
            },
        )
        self.assert_status(response, 201)

        dashboard = response.json()
        self.__class__.dashboard_id = int(dashboard["id"])

        response = self.request(
            "GET",
            f"/dashboards/{self.dashboard_id}",
        )
        self.assert_status(response, 200)

    def test_11_refresh_rotates_session(self) -> None:
        old_access = self.session.cookies.get("access_token")
        old_refresh = self.session.cookies.get("refresh_token")

        response = self.request("POST", "/auth/refresh")
        self.assert_status(response, 200)
        self.assertTrue(response.json()["authenticated"])

        new_access = self.session.cookies.get("access_token")
        new_refresh = self.session.cookies.get("refresh_token")

        self.assertTrue(new_access)
        self.assertTrue(new_refresh)
        self.assertNotEqual(old_refresh, new_refresh)

        # Access tokens can be equal when rotation occurs inside the same second,
        # so only assert that a valid access cookie still exists.
        self.assertIsNotNone(old_access)

    def test_12_async_delete_routes_accept_work(self) -> None:
        if self.dashboard_id is not None:
            response = self.request(
                "DELETE",
                f"/dashboards/?dashboard_id={self.dashboard_id}",
            )
            self.assert_status(response, 202)
            self.assertTrue(response.json()["accepted"])

        if self.conversation_id is not None:
            response = self.request(
                "DELETE",
                f"/conversations/?conversation_id={self.conversation_id}",
            )
            self.assert_status(response, 202)
            self.assertTrue(response.json()["accepted"])

        if self.data_source_id is not None:
            response = self.request(
                "DELETE",
                f"/data-sources/?data_source_id={self.data_source_id}",
            )
            self.assert_status(response, 202)
            self.assertTrue(response.json()["accepted"])

    def test_13_logout_clears_session_and_private_routes_fail(self) -> None:
        response = self.request("POST", "/auth/logout")
        self.assert_status(response, 200)
        self.assertTrue(response.json()["logged_out"])

        self.assertIsNone(self.session.cookies.get("access_token"))
        self.assertIsNone(self.session.cookies.get("refresh_token"))

        response = self.request("GET", "/users/")
        self.assert_status(response, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
