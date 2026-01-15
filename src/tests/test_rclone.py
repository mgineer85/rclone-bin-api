import logging
import time
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest

from rclone_api.api import RcloneApi
from rclone_api.exceptions import RcloneProcessException

logger = logging.getLogger(name=None)


@dataclass
class RcloneFixture:
    client: RcloneApi
    remote_name: str


@pytest.fixture()
def _rclone_fixture() -> Generator[RcloneFixture, None, None]:
    client = RcloneApi("localhost:5573", log_file=Path("./log/rclone.log"))

    client.start()

    # create local remote for testing
    remote_name = uuid4().hex
    client.config_create(remote_name, "local", {})

    try:
        yield RcloneFixture(client, remote_name)
    finally:
        client.config_delete(remote_name)
        client.stop()


def test_operational():
    ins = RcloneApi("localhost:5573")
    assert ins.operational() is False

    ins.start()

    assert ins.operational() is True

    ins.start()  # ensure second start doesn't break everything...

    ins.stop()

    assert ins.operational() is False


def test_transfers_status_request(tmp_path: Path):
    ins = RcloneApi("localhost:5573", bwlimit="5M")
    ins.start()

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.write_bytes(b"0" * 1024 * 1024)

    dummy_local_remote = Path(tmp_path / "out" / "file1.txt").absolute()

    assert len(ins.core_stats().transferring) == 0

    # queue the copy
    job = ins.copyfile_async(str(dummy_local.parent), dummy_local.name, str(dummy_local_remote.parent), dummy_local_remote.name)

    while len(ins.core_stats().transferring) == 0:
        # wait until actually transferring
        time.sleep(0.1)

    # ensure the filename is part of the transfer queue
    assert dummy_local.name in ins.core_stats().transferring[0].name

    ins.wait_for_jobs([job.jobid])

    final_status = ins.job_status(jobid=job.jobid)

    assert final_status.success

    ins.stop()


def test_version(_rclone_fixture: RcloneFixture):
    version = _rclone_fixture.client.version()

    assert _rclone_fixture.client.version()

    logger.info(version)


def test_core_stats(_rclone_fixture: RcloneFixture):
    assert _rclone_fixture.client.core_stats()


def test_create_list_delete_remotes(_rclone_fixture: RcloneFixture):
    name = uuid4().hex

    _rclone_fixture.client.config_create(name, "local", {})
    assert name in _rclone_fixture.client.config_listremotes().remotes

    _rclone_fixture.client.config_delete(name)
    assert name not in _rclone_fixture.client.config_listremotes().remotes


def test_deletefile(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "file1.txt"
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "file1.txt").relative_to(Path.cwd())

    # Perform
    client.deletefile(f"{remote}:", dummy_remote.as_posix())

    # Assertions
    listing = client.ls(f"{remote}:", dummy_remote.parent.as_posix())

    assert not any(entry.Name == "file1.txt" for entry in listing)

    assert not dummy_local.exists()


def test_copyfile(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out" / "file1.txt").relative_to(Path.cwd())

    # Perform
    client.copyfile(str(dummy_local.parent), dummy_local.name, f"{remote}:", dummy_remote.as_posix())

    # Assertions
    listing = client.ls(f"{remote}:", dummy_remote.parent.as_posix())

    assert any(entry.Name == "file1.txt" for entry in listing)

    assert dummy_remote.is_file()


def test_copyfile_async(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out" / "file1.txt").relative_to(Path.cwd())

    # Perform the copy
    job = client.copyfile_async(str(dummy_local.parent), dummy_local.name, f"{remote}:", dummy_remote.as_posix())
    client.wait_for_jobs([job.jobid])

    final_status = client.job_status(jobid=job.jobid)
    final_joblist = client.job_list()

    # --- Assertions ---
    assert final_status.success

    assert job.jobid in final_joblist.jobids
    assert job.jobid in final_joblist.finishedIds

    listing = client.ls(f"{remote}:", dummy_remote.parent.as_posix())
    assert any(entry.Name == "file1.txt" for entry in listing)

    assert dummy_remote.is_file()


def test_copy(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out").relative_to(Path.cwd())

    # Perform
    client.copy(str(dummy_local.parent), f"{remote}:{dummy_remote.as_posix()}")

    # Assertions
    listing = client.ls(f"{remote}:", dummy_remote.as_posix())

    assert any(entry.Name == "file1.txt" for entry in listing)

    assert Path(dummy_remote, "file1.txt").is_file()


def test_copy_async(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out").relative_to(Path.cwd())

    # Perform
    job = client.copy_async(str(dummy_local.parent), f"{remote}:{dummy_remote.as_posix()}")
    client.wait_for_jobs([job.jobid])

    final_status = client.job_status(jobid=job.jobid)
    final_joblist = client.job_list()

    # --- Assertions ---
    assert final_status.success

    assert job.jobid in final_joblist.jobids
    assert job.jobid in final_joblist.finishedIds

    listing = client.ls(f"{remote}:", dummy_remote.as_posix())
    assert any(entry.Name == "file1.txt" for entry in listing)

    assert Path(dummy_remote, "file1.txt").is_file()


def test_copy_localonly(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    # remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_local_remote = Path(tmp_path / "out").absolute()

    # Perform
    client.copy(str(dummy_local.parent), str(dummy_local_remote))

    # Assertions
    listing1 = client.ls(str(dummy_local_remote), "/")
    listing2 = client.ls(str(dummy_local_remote), "")

    assert any(entry.Name == "file1.txt" for entry in listing1)
    assert any(entry.Name == "file1.txt" for entry in listing2)

    assert Path(dummy_local_remote, "file1.txt").is_file()


def test_sync(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out").relative_to(Path.cwd())

    # Perform
    client.sync(str(dummy_local.parent), f"{remote}:{dummy_remote.as_posix()}")

    # Assertions
    listing = client.ls(f"{remote}:", dummy_remote.as_posix())

    assert any(entry.Name == "file1.txt" for entry in listing)

    assert Path(dummy_remote, "file1.txt").is_file()


def test_sync_async(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "in" / "file1.txt"
    dummy_local.parent.mkdir(parents=True)
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "out").relative_to(Path.cwd())

    # Perform
    job = client.sync_async(str(dummy_local.parent), f"{remote}:{dummy_remote.as_posix()}")
    client.wait_for_jobs([job.jobid])

    final_status = client.job_status(jobid=job.jobid)
    final_joblist = client.job_list()

    # --- Assertions ---
    assert final_status.success

    assert job.jobid in final_joblist.jobids
    assert job.jobid in final_joblist.finishedIds

    listing = client.ls(f"{remote}:", dummy_remote.as_posix())
    assert any(entry.Name == "file1.txt" for entry in listing)

    assert Path(dummy_remote, "file1.txt").is_file()


def test_publiclink(_rclone_fixture: RcloneFixture, tmp_path: Path):
    client = _rclone_fixture.client
    remote = _rclone_fixture.remote_name

    dummy_local = tmp_path / "file1.txt"
    dummy_local.touch()

    dummy_remote = Path(tmp_path / "file1.txt").relative_to(Path.cwd())

    # Perform
    with pytest.raises(RcloneProcessException):
        client.publiclink(f"{remote}:", dummy_remote.as_posix())
