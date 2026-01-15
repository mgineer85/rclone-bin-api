# Rclone Api for Python including Rclone binaries

This package is developed for use in the photobooth-app.
It serves to distribute the rclone binary via wheels so a recent version is available
on all platforms that are supported by the photobooth-app.

[![PyPI](https://img.shields.io/pypi/v/rclone-bin-api)](https://pypi.org/project/rclone-bin-api/)
[![ruff](https://github.com/mgineer85/rclone-bin-api/actions/workflows/ruff.yml/badge.svg)](https://github.com/mgineer85/rclone-bin-api/workflows/ruff.yml)
[![pytest](https://github.com/mgineer85/rclone-bin-api/actions/workflows/pytests.yml/badge.svg)](https://github.com/mgineer85/rclone-bin-api/actions/workflows/pytests.yml)
[![codecov](https://codecov.io/gh/mgineer85/rclone-bin-api/graph/badge.svg?token=87aLWw2gIT)](https://codecov.io/gh/mgineer85/rclone-bin-api)

## How it works

The PyPi packages include the Rclone binaries for Linux/Windows/Mac (64bit/ARM64). To use the API, create an instance of the `api=RcloneApi()`.
The provided binding methods make use of [Rclones remote control capabilites](https://rclone.org/rc/), the service needs to be started prior starting file operations `api.start()`.

## Usage

Get the version of the Rclone included in the distribution:

```python
from rclone_api.api import RcloneApi

api = RcloneApi()
api.start()

print(api.version()) # CoreVersion(version='v1.72.1')

api.stop()
```

Synchonize a folder to a remote

```python
from rclone_api.api import RcloneApi

api = RcloneApi()
api.start()

api.sync("localdir/", "cloudremote:remotedir/")

api.stop()
```
