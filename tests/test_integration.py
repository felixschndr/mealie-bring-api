import asyncio
import os
import subprocess  # nosec B404
import time

import pytest
import requests
from source.bring_handler import BringHandler


@pytest.mark.skipif(
    not os.getenv("BRING_USERNAME") or not os.getenv("BRING_PASSWORD") or not os.getenv("BRING_LIST_NAME"),
    reason="The necessary environment variables are not set.",
)
def test_example_request_against_server(example_request):
    server_process = subprocess.Popen(  # nosec B603, B607
        ["python", "-m", "source.mealie_bring_api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    timeout_seconds = 10
    start = time.time()
    response = None
    while time.time() - start < timeout_seconds:
        try:
            response = requests.post("http://localhost:8742/", json=example_request, timeout=5)
            break
        except requests.exceptions.ConnectionError:
            print("Waiting for server to start...")
            time.sleep(1)

    assert response is not None, f"Server did not respond within {timeout_seconds}s"
    response.raise_for_status()
    assert response.status_code == 200
    assert response.text == "OK"

    server_process.terminate()
    stdout, _ = server_process.communicate(timeout=10)

    for message_to_find in [
        "Listening on 0.0.0.0:8742",
        "Adding ingredients to Bring:",
        "Received SIGTERM. Exiting now...",
    ]:
        assert message_to_find in stdout, f"Expected message {message_to_find} not found in server output"
    for message_not_to_find in ["[WARNING]", "[ERROR]", "[FATAL]"]:
        assert message_not_to_find not in stdout, f"Unexpected log level {message_not_to_find} found in server output"

    clean_bring_list()


def clean_bring_list():
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
