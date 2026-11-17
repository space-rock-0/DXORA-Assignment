import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app, validate_url

@pytest.mark.parametrize('url',['file:///etc/passwd','http://127.0.0.1','http://169.254.169.254','http://[::1]','http://user:pass@example.com','http://example.com:8080'])
def test_unsafe_urls(url):
    with pytest.raises(ValueError): asyncio.run(validate_url(url))

def test_health():
    assert TestClient(app).get('/health').status_code == 200

def test_invalid_request():
    assert TestClient(app).post('/link-analysis',json={}).status_code == 422
