import logging
import time
from collections.abc import Generator
from dataclasses import dataclass
from uuid import uuid4

import pytest

from rclone_client.client import RcloneClient

logger = logging.getLogger(name=None)


@dataclass
class RcloneFixture:
    client: RcloneClient
    remote_name: str


def _wait_op(client: RcloneClient):
    abort_counter = 0
    while not client.operational():
        time.sleep(0.1)
        abort_counter += 1
        assert abort_counter < 50, "rclone not getting operational, aborting!"


@pytest.fixture()
def _rclone_fixture() -> Generator[RcloneFixture, None, None]:
    client = RcloneClient("localhost:5573")

    # ensure is installed, otherwise will download prior start.
    # client.is_installed()

    client.start()

    _wait_op(client)

    # create local remote for testing
    remote_name = uuid4().hex
    client.config_create(remote_name, "local", {})

    try:
        yield RcloneFixture(client, remote_name)
    finally:
        client.config_delete(remote_name)
        client.stop()


def test_operational():
    ins = RcloneClient("localhost:5573")
    assert ins.operational() is False

    ins.start()
    _wait_op(ins)

    assert ins.operational() is True

    ins.start()  # ensure second start doesn't break everything...

    ins.stop()

    assert ins.operational() is False


def test_version(_rclone_fixture: RcloneFixture):
    version = _rclone_fixture.client.version()

    assert _rclone_fixture.client.version()

    logger.info(version)
