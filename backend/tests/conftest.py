"""
Shared pytest fixtures for the Vanguard Risk Engine test suite.
Eliminates boilerplate duplication across all test files.
"""
import sys
import os
import pytest

# Add backend directory to Python path so engine modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from ml_engine import initialize_model


@pytest.fixture(scope="session")
def client():
    """Shared FastAPI test client for all integration tests."""
    # Ensure ML model is initialized before any tests run
    initialize_model()
    return TestClient(app)
