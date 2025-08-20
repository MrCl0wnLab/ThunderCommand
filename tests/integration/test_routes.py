from app import create_app
import pytest

@pytest.fixture
def app():
    """Cria instância do aplicativo Flask para testes"""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    # Outras configurações específicas para testes
    
    yield app

@pytest.fixture
def client(app):
    """Cliente de teste HTTP"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner de comandos CLI"""
    return app.test_cli_runner()

def test_request_example(client):
    """Exemplo de teste para API"""
    response = client.get("/")
    assert response.status_code == 200

def test_auth_required(client):
    """Teste de rotas protegidas por autenticação"""
    response = client.get("/admin/dashboard")
    assert response.status_code == 302  # Redirecionamento para login
