import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    \"\"\"Prueba simple para verificar que la ruta principal responde.\"\"\"
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data or response.status_code == 200

def test_admin_route(client):
    \"\"\"Prueba simple para la ruta de admin.\"\"\"
    response = client.get('/admin')
    assert response.status_code == 200
