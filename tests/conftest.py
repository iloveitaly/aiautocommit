import os
import pytest
from click.testing import CliRunner
from tests.utils import GitTestMixin

@pytest.fixture(autouse=True)
def clean_env():
    """Ensure AIAUTOCOMMIT environment variables don't leak into tests."""
    old_env = os.environ.copy()
    
    # Remove all AIAUTOCOMMIT_ prefixed variables
    for key in list(os.environ.keys()):
        if key.startswith("AIAUTOCOMMIT_"):
            del os.environ[key]
            
    yield
    
    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def git_repo(runner):
    with runner.isolated_filesystem():
        mixin = GitTestMixin()
        mixin.init_repo()
        yield mixin
