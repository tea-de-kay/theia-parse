from pathlib import Path

import pytest
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent.parent
TESTS_ROOT = PROJECT_ROOT / "tests"
RESOURCE_PATH = TESTS_ROOT / "resources"
DOTENV_PATH = PROJECT_ROOT / ".env"


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv(DOTENV_PATH)
