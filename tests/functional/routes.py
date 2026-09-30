"""HTTP-only functional checks for DataPilot."""

from __future__ import annotations

import io
import os
import time
from uuid import uuid4

import requests


BASE_URL = os.getenv("FUNCTIONAL_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.getenv("FUNCTIONAL_REQUEST_TIMEOUT", "30"))


def fail(method: str, path: str, response: requests.Response) -> None:
    raise RuntimeError(
        f"{method} {path} -> {response.status_code}: {response.text}"
    )


def call(
    session: requests.Session,
    method: str,
    path: str,
    expected: int | set[int],
    **kwargs,
) -> requests.Response:
    try:
        response = session.request(
            method,
            f"{BASE_URL}{path}",
            timeout=TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as error:
        raise RuntimeError(f"{method} {path} -> request failed: {error}") from error

    allowed = {expected} if isinstance(expected, int) else expected
    if response.status_code not in allowed:
        fail(method, path, response)

    if response.status_code >= 400:
        print(
            f"OK {method} {path} -> {response.status_code}: {response.text}",
            flush=True,
        )
    else:
        print(f"OK {method} {path} -> {response.status_code}", flush=True)
    return response


def wait_api(session: requests.Session) -> None:
    deadline = time.time() + 120
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = session.get(f"{BASE_URL}/users/", timeout=3)
            if response.status_code in {200, 401}:
                return
        except requests.RequestException as error:
            last_error = error
        time.sleep(1)
    raise RuntimeError(f"API unavailable at {BASE_URL}") from last_error


def create_user(
    session: requests.Session,
    *,
    email: str,
    username: str,
    password: str,
) -> dict:
    sender = call(
        session,
        "POST",
        "/sender/create-account",
        202,
        json={"email": email},
    ).json()
    code = sender.get("code")
    if not code:
        raise RuntimeError(
            "sender/create-account did not return code; ENVIROIMENT must be test"
        )

    payload = call(
        session,
        "POST",
        "/users/",
        201,
        json={
            "name": "Functional User",
            "username": username,
            "email": email,
            "password": password,
            "age": 18,
            "gender": "PREFIRO NÃO DIZER",
            "profile_image": None,
            "auth2": False,
            "code": code,
        },
    ).json()

    if "X-token_user" not in session.cookies:
        raise RuntimeError("missing X-token_user cookie")
    if "X-refresh_user" not in session.cookies:
        raise RuntimeError("missing X-refresh_user cookie")

    return payload["user"]


def main() -> None:
    session = requests.Session()
    collaborator_session = requests.Session()
    suffix = uuid4().hex[:10]
    email = f"functional-{suffix}@example.com"
    username = f"functional_{suffix}"
    collaborator_email = f"collaborator-{suffix}@example.com"
    collaborator_username = f"collaborator_{suffix}"
    password = f"T-{uuid4().hex}aA1!"

    wait_api(session)

    call(requests.Session(), "GET", "/users/", 401)

    user = create_user(
        session,
        email=email,
        username=username,
        password=password,
    )
    collaborator = create_user(
        collaborator_session,
        email=collaborator_email,
        username=collaborator_username,
        password=password,
    )

    call(session, "GET", "/users/", 200)
    call(
        session,
        "PATCH",
        "/users/",
        200,
        json={"name": "Functional Updated"},
    )
    change_password = call(
        session,
        "POST",
        "/sender/change-password",
        202,
        json={"email": email},
    ).json()
    if not change_password.get("code"):
        raise RuntimeError(
            "sender/change-password did not return code in test mode"
        )

    csv_data = (
        "produto,valor,quantidade\n"
        "Notebook,5000,2\n"
        "Mouse,150,10\n"
        "Teclado,300,4\n"
    ).encode()

    source = call(
        session,
        "POST",
        "/data-sources/file",
        201,
        data={"name": "Functional CSV"},
        files={"file": ("functional.csv", io.BytesIO(csv_data), "text/csv")},
    ).json()["data_source"]
    source_id = int(source["id"])

    call(session, "GET", "/data-sources/", 200)
    call(session, "GET", f"/data-sources/{source_id}", 200)
    call(
        session,
        "PATCH",
        f"/data-sources/?data_source_id={source_id}",
        200,
        json={"name": "Functional CSV Updated"},
    )
    call(
        session,
        "PATCH",
        f"/data-sources/file?data_source_id={source_id}",
        200,
        data={"name": "Functional CSV Replaced"},
        files={"file": ("functional.csv", io.BytesIO(csv_data), "text/csv")},
    )
    call(
        session,
        "POST",
        "/data-sources/sql",
        400,
        json={
            "name": "Invalid SQL source",
            "database_url": "sqlite+aiosqlite:///tmp/test.db",
            "query": "SELECT 1",
        },
    )
    call(
        session,
        "PATCH",
        f"/data-sources/sql?data_source_id={source_id}",
        400,
        json={
            "database_url": "sqlite+aiosqlite:///tmp/test.db",
            "query": "SELECT 1",
        },
    )
    call(
        session,
        "POST",
        f"/data-sources/sql/execute?data_source_id={source_id}",
        400,
        json={"query": "SELECT 1", "save_query": False},
    )

    call(
        session,
        "POST",
        "/agents/chat",
        200,
        json={"question": "Explique o DataPilot.", "history": []},
    )
    call(
        session,
        "POST",
        "/agents/chat-intent",
        200,
        json={"question": "Quero analisar dados.", "history": []},
    )
    call(
        session,
        "POST",
        "/agents/data",
        200,
        json={
            "data_source_id": source_id,
            "question": "Qual produto tem maior valor?",
            "history": [],
        },
    )

    agent_dashboard = call(
        session,
        "POST",
        "/agents/dashboard",
        200,
        data={"prompt": "Crie um dashboard simples."},
        files={"file": ("dashboard.csv", io.BytesIO(csv_data), "text/csv")},
    ).json()

    call(
        session,
        "POST",
        "/agents/analysis",
        200,
        json={
            "analysis_id": agent_dashboard["analysis_id"],
            "question": "Resuma o dashboard.",
            "history": [],
        },
    )
    call(
        session,
        "POST",
        "/agents/multi-analysis",
        200,
        json={
            "question": "Resuma os gráficos.",
            "charts": [{"type": "bar", "title": "Functional"}],
            "history": [],
        },
    )
    call(
        session,
        "POST",
        "/agents/dashboard-planner",
        200,
        json={
            "user_prompt": "Planeje um dashboard.",
            "schema": {"produto": "string", "valor": "number"},
        },
    )
    call(
        session,
        "POST",
        "/agents/dashboard-general",
        200,
        json={
            "plan": {"goal": "overview"},
            "schema": {"produto": "string", "valor": "number"},
            "metrics": [{"name": "valor"}],
        },
    )
    call(
        session,
        "POST",
        "/agents/dashboard-specific",
        200,
        json={
            "user_prompt": "Foque em valor.",
            "plan": {"goal": "overview"},
            "schema": {"produto": "string", "valor": "number"},
            "metrics": [{"name": "valor"}],
        },
    )
    call(
        session,
        "POST",
        "/agents/dashboard-multi-general",
        200,
        json={
            "plan": {"goal": "overview"},
            "schema": {"produto": "string", "valor": "number"},
            "charts": [{"type": "bar"}],
        },
    )
    call(
        session,
        "POST",
        "/agents/dashboard-multi-specific",
        200,
        json={
            "user_prompt": "Compare os gráficos.",
            "plan": {"goal": "overview"},
            "schema": {"produto": "string", "valor": "number"},
            "charts": [{"type": "bar"}],
        },
    )

    conversation = call(
        session,
        "POST",
        "/conversations/",
        201,
        json={"title": "Functional conversation"},
    ).json()
    conversation_id = int(conversation["id"])
    call(session, "GET", "/conversations/", 200)
    call(session, "GET", f"/conversations/{conversation_id}", 200)
    call(
        session,
        "PATCH",
        f"/conversations/?conversation_id={conversation_id}",
        200,
        json={"title": "Functional conversation updated"},
    )

    message = call(
        session,
        "POST",
        "/messages/",
        201,
        json={
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Mensagem funcional",
        },
    ).json()
    message_id = int(message["id"])
    call(session, "GET", f"/messages/?conversation_id={conversation_id}", 200)
    call(session, "GET", f"/messages/{message_id}", 200)
    call(
        session,
        "PATCH",
        f"/messages/?message_id={message_id}",
        200,
        json={"content": "Mensagem funcional atualizada"},
    )

    dashboard = call(
        session,
        "POST",
        "/dashboards/",
        201,
        json={
            "title": "Functional dashboard",
            "prompt": "Functional prompt",
            "data_source_id": source_id,
            "is_outdated": False,
        },
    ).json()
    dashboard_id = int(dashboard["id"])
    call(session, "GET", "/dashboards/", 200)
    call(session, "GET", f"/dashboards/{dashboard_id}", 200)
    call(
        session,
        "PATCH",
        f"/dashboards/?dashboard_id={dashboard_id}",
        200,
        json={"title": "Functional dashboard updated"},
    )
    call(
        session,
        "GET",
        f"/data-sources/linked-dashboards?data_source_id={source_id}",
        200,
    )

    chart = call(
        session,
        "POST",
        "/dashboard-charts/",
        201,
        json={
            "dashboard_id": dashboard_id,
            "chart_type": "bar",
            "title": "Functional chart",
            "chart_data": [{"label": "A", "value": 1}],
            "chart_config": {},
        },
    ).json()
    chart_id = int(chart["id"])
    call(
        session,
        "GET",
        f"/dashboard-charts/?dashboard_id={dashboard_id}",
        200,
    )
    call(session, "GET", f"/dashboard-charts/{chart_id}", 200)
    call(
        session,
        "PATCH",
        f"/dashboard-charts/?chart_id={chart_id}",
        200,
        json={"title": "Functional chart updated"},
    )

    setting = call(
        session,
        "POST",
        "/dashboard-chart-settings/",
        201,
        json={
            "dashboard_id": dashboard_id,
            "chart_id": chart_id,
            "chart_color": "#000000",
        },
    ).json()
    setting_id = int(setting["id"])
    call(
        session,
        "GET",
        f"/dashboard-chart-settings/?dashboard_id={dashboard_id}",
        200,
    )
    call(
        session,
        "GET",
        f"/dashboard-chart-settings/{setting_id}",
        200,
    )
    call(
        session,
        "PATCH",
        f"/dashboard-chart-settings/?setting_id={setting_id}",
        200,
        json={"show_legend": False},
    )

    collaboration = call(
        session,
        "POST",
        "/dashboard-collaborations/",
        201,
        json={
            "dashboard_id": dashboard_id,
            "collaborator_user_id": collaborator["user_id"],
            "permission": "read",
        },
    ).json()
    collaboration_id = int(collaboration["id"])
    call(session, "GET", "/dashboard-collaborations/", 200)
    call(
        session,
        "GET",
        f"/dashboard-collaborations/{collaboration_id}",
        200,
    )
    call(
        session,
        "PATCH",
        f"/dashboard-collaborations/?collaboration_id={collaboration_id}",
        200,
        json={"permission": "edit"},
    )
    call(
        collaborator_session,
        "POST",
        f"/dashboard-collaborations/respond?collaboration_id={collaboration_id}",
        200,
        json={"response": "accepted"},
    )

    notification = call(
        session,
        "POST",
        "/collaboration-notifications/",
        202,
        json={
            "collaboration_id": collaboration_id,
            "dashboard_id": dashboard_id,
            "message": "Functional notification",
            "notification_type": "functional",
        },
    ).json()
    notification_id = int(notification["id"])
    call(session, "GET", "/collaboration-notifications/", 200)
    call(
        session,
        "GET",
        f"/collaboration-notifications/{notification_id}",
        200,
    )
    call(
        session,
        "PATCH",
        f"/collaboration-notifications/?notification_id={notification_id}",
        200,
        json={"is_read": True},
    )
    call(
        session,
        "PATCH",
        "/collaboration-notifications/read-all",
        200,
    )

    old_refresh = session.cookies.get("X-refresh_user")
    call(session, "POST", "/auth/refresh", 200)
    if session.cookies.get("X-refresh_user") == old_refresh:
        raise RuntimeError("X-refresh_user was not rotated")

    call(
        session,
        "PATCH",
        "/users/",
        200,
        json={"auth2": True},
    )
    call(session, "POST", "/auth/logout", 200)

    login = call(
        session,
        "POST",
        "/auth/",
        202,
        json={"identifier": email, "password": password},
    ).json()
    if not login.get("auth2_required"):
        raise RuntimeError("auth2 was not required")

    auth2 = call(session, "POST", "/sender/auth2", 202).json()
    code = auth2.get("code")
    if not code:
        raise RuntimeError("sender/auth2 did not return code in test mode")

    call(
        session,
        "POST",
        "/auth/",
        200,
        json={"identifier": email, "password": password, "code": code},
    )

    call(
        session,
        "DELETE",
        f"/collaboration-notifications/?notification_id={notification_id}",
        200,
    )
    call(
        session,
        "DELETE",
        f"/dashboard-collaborations/?collaboration_id={collaboration_id}",
        200,
    )
    call(
        session,
        "DELETE",
        f"/dashboard-chart-settings/?setting_id={setting_id}",
        200,
    )
    call(
        session,
        "DELETE",
        f"/dashboard-charts/?chart_id={chart_id}",
        200,
    )
    call(session, "DELETE", f"/messages/?message_id={message_id}", 200)
    call(
        session,
        "DELETE",
        f"/conversations/?conversation_id={conversation_id}",
        202,
    )
    call(
        session,
        "DELETE",
        f"/dashboards/?dashboard_id={dashboard_id}",
        202,
    )
    call(
        session,
        "DELETE",
        f"/data-sources/?data_source_id={source_id}",
        202,
    )

    call(collaborator_session, "DELETE", "/users/", 202)
    call(session, "POST", "/auth/logout", 200)
    call(session, "GET", "/users/", 401)

    print("Functional HTTP checks passed.", flush=True)


if __name__ == "__main__":
    main()
