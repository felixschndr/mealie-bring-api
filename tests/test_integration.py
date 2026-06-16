import asyncio
import contextlib
import os
import socket
import subprocess  # nosec B404
import threading
import time
from dataclasses import dataclass

import pytest
import requests
from source.bring_handler import BringHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEALIE_DEMO_BASE_URL = "https://demo.mealie.io"
MEALIE_DEMO_USERNAME = "changeme@example.com"
MEALIE_DEMO_PASSWORD = "MyPassword"  # nosec B105

pytestmark = pytest.mark.skipif(
    not os.getenv("BRING_USERNAME") or not os.getenv("BRING_PASSWORD") or not os.getenv("BRING_LIST_NAME"),
    reason="The necessary environment variables are not set.",
)


def test_example_request_against_server(example_request):
    with running_server({"MEALIE_BASE_URL": "", "MEALIE_API_KEY": ""}) as server:
        response = requests.post(f"{server.base_url}/", json=example_request, timeout=5)
        assert response.status_code == 200
        assert response.text == "OK"

    assert_server_output(
        server.stdout,
        [
            f"Listening on 0.0.0.0:{server.port}",
            "Adding ingredients to Bring:",
            "Received SIGTERM. Exiting now...",
        ],
    )


def test_move_ingredients_from_shopping_list_against_server():
    items_to_add = ["apples", "bread", "eggs"]
    demo_setup = setup_demo_setup(items_to_add)

    with running_server(
        {
            "MEALIE_BASE_URL": MEALIE_DEMO_BASE_URL,
            "MEALIE_API_KEY": demo_setup.api_key,
            "MEALIE_SHOPPING_LIST_UUID": demo_setup.list_uuid,
        }
    ) as server:
        response = requests.post(f"{server.base_url}/move-ingredients-from-shopping-list", timeout=30)
        assert response.status_code == 200
        assert response.text == "OK"

    assert _mealie_demo_get_items(demo_setup.api_key, demo_setup.list_uuid) == []

    bring_item_names = _get_item_names_of_bring_list()
    for expected_name in items_to_add:
        assert expected_name in "\t".join(bring_item_names)

    assert_server_output(
        server.stdout,
        [
            "Connection to Mealie successful",
            "Moving ingredients from shopping list to Bring",
            "Adding ingredients to Bring:",
            "Received SIGTERM. Exiting now...",
        ],
    )

    cleanup_demo_setup(demo_setup)


@dataclass
class RunningServer:
    process: subprocess.Popen
    port: int
    stdout: str | None = None

    @property
    def base_url(self) -> str:
        return f"http://localhost:{self.port}"


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def running_server(extra_env: dict[str, str]):
    port = _find_free_port()
    # `-u` keeps stdout unbuffered so the full server log is captured even when the process is terminated
    process = subprocess.Popen(  # nosec B603, B607
        ["python", "-u", "-m", "source.mealie_bring_api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT, "HTTP_PORT": str(port), **(extra_env or {})},
    )
    server = RunningServer(process, port)
    # Drain stdout in a background thread so the OS pipe buffer never fills up. Otherwise a verbose server
    # (e.g. LOG_LEVEL=DEBUG) blocks on writing once the buffer is full and the request handler deadlocks.
    output_lines: list[str] = []
    reader = threading.Thread(target=lambda: output_lines.extend(process.stdout), daemon=True)
    reader.start()
    try:
        startup_timeout_seconds = 15
        start = time.time()
        while time.time() - start < startup_timeout_seconds:
            if process.poll() is not None:
                raise AssertionError("Server exited during startup")
            try:
                if requests.get(f"{server.base_url}/status", timeout=5).status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                print("Waiting for server to start...")
                time.sleep(1)
        else:
            raise AssertionError(f"Server did not respond within {startup_timeout_seconds}s")

        yield server
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
        reader.join(timeout=10)
        server.stdout = "".join(output_lines)


def assert_server_output(stdout: str, messages_to_find: list[str]) -> None:
    for message_to_find in messages_to_find:
        assert message_to_find in stdout
    for message_not_to_find in ["[WARNING]", "[ERROR]", "[FATAL]"]:
        assert message_not_to_find not in stdout


def _get_item_names_of_bring_list() -> list[str]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bring_handler = BringHandler(loop)
    try:
        items = loop.run_until_complete(bring_handler.bring.get_list(bring_handler.list_uuid)).items.purchase
        return [item.itemId for item in items]
    finally:
        loop.run_until_complete(bring_handler.logout())
        loop.close()


def _clean_bring_list() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bring_handler = BringHandler(loop)

    for item in loop.run_until_complete(bring_handler.bring.get_list(bring_handler.list_uuid)).items.purchase:
        loop.run_until_complete(
            bring_handler.bring.remove_item(
                list_uuid=bring_handler.list_uuid, item_name="placeholder", item_uuid=item.uuid
            )
        )

    loop.run_until_complete(bring_handler.logout())
    loop.close()


def _mealie_demo_login() -> str:
    response = requests.post(
        f"{MEALIE_DEMO_BASE_URL}/api/auth/token",
        data={"username": MEALIE_DEMO_USERNAME, "password": MEALIE_DEMO_PASSWORD, "remember_me": "false"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _mealie_demo_create_api_key(access_token: str, name: str) -> tuple[str, int]:
    response = requests.post(
        f"{MEALIE_DEMO_BASE_URL}/api/users/api-tokens",
        json={"name": name},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return data["token"], data["id"]


def _mealie_demo_delete_api_key(access_token: str, token_id: int) -> None:
    requests.delete(
        f"{MEALIE_DEMO_BASE_URL}/api/users/api-tokens/{token_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    ).raise_for_status()


def _mealie_demo_create_shopping_list(api_key: str, name: str) -> str:
    response = requests.post(
        f"{MEALIE_DEMO_BASE_URL}/api/households/shopping/lists",
        json={"name": name},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["id"]


def _mealie_demo_delete_shopping_list(api_key: str, list_uuid: str) -> None:
    requests.delete(
        f"{MEALIE_DEMO_BASE_URL}/api/households/shopping/lists/{list_uuid}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )


def _mealie_demo_add_item(api_key: str, list_uuid: str, note: str, quantity: float) -> None:
    response = requests.post(
        f"{MEALIE_DEMO_BASE_URL}/api/households/shopping/items",
        json={
            "shoppingListId": list_uuid,
            "note": note,
            "quantity": quantity,
            "isFood": False,
            "disableAmount": True,
        },
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    response.raise_for_status()


def _mealie_demo_get_items(api_key: str, list_uuid: str) -> list[dict]:
    response = requests.get(
        f"{MEALIE_DEMO_BASE_URL}/api/households/shopping/items?perPage=-1",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    response.raise_for_status()
    return [item for item in response.json()["items"] if item["shoppingListId"] == list_uuid]


@dataclass
class DemoSetup:
    api_key: str
    api_token_id: int
    list_uuid: str
    access_token: str


def setup_demo_setup(items_to_add: list[str]) -> DemoSetup:
    access_token = _mealie_demo_login()
    api_key, token_id = _mealie_demo_create_api_key(access_token, "bring-api-integration-test")

    list_uuid = _mealie_demo_create_shopping_list(api_key, "Bring Integration Test List")
    for item in items_to_add:
        _mealie_demo_add_item(api_key, list_uuid, item, 1)
    assert len(_mealie_demo_get_items(api_key, list_uuid)) == len(items_to_add)

    _clean_bring_list()

    return DemoSetup(api_key, token_id, list_uuid, access_token)


def cleanup_demo_setup(demo_setup: DemoSetup) -> None:
    _mealie_demo_delete_api_key(demo_setup.access_token, demo_setup.api_token_id)
    _mealie_demo_delete_shopping_list(demo_setup.api_key, demo_setup.list_uuid)
