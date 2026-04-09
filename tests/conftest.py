import os
import shutil
import tempfile
import time
from pathlib import Path

import afmformats
import pytest

TMPDIR = tempfile.mkdtemp(prefix=time.strftime(
    "afmformats_test_%H.%M_"))
LOG_PATH_KEY = pytest.StashKey[Path]()


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    tempfile.tempdir = TMPDIR
    # deal with logging directory
    ci_log_path = os.getenv("AFMFORMATS_LOG_PATH")
    if ci_log_path:
        log_path = ci_log_path
    else:
        log_path = os.path.join(TMPDIR, "afmformats.log")
    configured_log_path = afmformats.configure_logging(log_path)
    config.stash[LOG_PATH_KEY] = Path(configured_log_path)


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    shutil.rmtree(TMPDIR, ignore_errors=True)


@pytest.fixture
def afmformats_log_path(pytestconfig):
    return pytestconfig.stash[LOG_PATH_KEY]
