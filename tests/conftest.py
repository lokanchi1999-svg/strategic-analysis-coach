import os
import sys
from pathlib import Path
os.environ["MODEL_ADAPTER"] = "mock"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)
