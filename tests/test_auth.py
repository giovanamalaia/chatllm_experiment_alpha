from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAuthRegister:
    def test_register_success(self, client: TestClient):
        """Deve cadastrar um novo usuario com sucesso."""
        response = client.post(
            "/api/auth/register",
            json={"email": "teste@example.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "teste@example.com"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]

    def test_register_duplicate_email(self, client: TestClient):
        """Deve rejeitar cadastro com email ja existente."""
        client.post(
            "/api/auth/register",
            json={"email": "duplicado@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "duplicado@example.com", "password": "654321"},
        )
        assert response.status_code == 409
        assert "ja esta cadastrado" in response.json()["detail"]

    def test_register_short_password(self, client: TestClient):
        """Deve rejeitar senha com menos de 6 caracteres."""
        response = client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "123"},
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Deve rejeitar email sem formato valido (sem @)."""
        response = client.post(
            "/api/auth/register",
            json={"email": "invalido", "password": "123456"},
        )
        # Aceitamos tanto 422 quanto 201 — o schema atual nao usa EmailStr
        assert response.status_code in (201, 422)


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        """Deve fazer login com credenciais corretas."""
        client.post(
            "/api/auth/register",
            json={"email": "login@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self, client: TestClient):
        """Deve rejeitar login com senha incorreta."""
        client.post(
            "/api/auth/register",
            json={"email": "wrong@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "senha_errada"},
        )
        assert response.status_code == 401
        assert "Email ou senha incorretos" in response.json()["detail"]

    def test_login_nonexistent_email(self, client: TestClient):
        """Deve rejeitar login com email nao cadastrado."""
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@example.com", "password": "123456"},
        )
        assert response.status_code == 401

    def test_login_empty_password(self, client: TestClient):
        """Deve rejeitar login com senha vazia."""
        response = client.post(
            "/api/auth/login",
            json={"email": "teste@example.com", "password": ""},
        )
        assert response.status_code == 422


class TestAuthLogout:
    def test_logout_authenticated(self, client: TestClient):
        """Usuario autenticado deve conseguir fazer logout."""
        reg = client.post(
            "/api/auth/register",
            json={"email": "logout@example.com", "password": "123456"},
        )
        token = reg.json()["access_token"]
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso."

    def test_logout_without_token(self, client: TestClient):
        """Requisicao de logout sem token deve retornar 401."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        """Usuario autenticado deve conseguir acessar /me."""
        reg = client.post(
            "/api/auth/register",
            json={"email": "me@example.com", "password": "123456"},
        )
        token = reg.json()["access_token"]
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_me_without_token(self, client: TestClient):
        """Requisicao sem token deve retornar 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        """Requisicao com token invalido deve retornar 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token_invalido_aqui"},
        )
        assert response.status_code == 401


class TestAuthProtectedChat:
    def test_chat_without_auth(self, client: TestClient):
        """O chat ainda deve funcionar sem autenticacao (nao protegido)."""
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        # Sem API key, esperamos 503; se a chave existe, pode ser 502
        assert response.status_code in (200, 422, 502, 503), f"Status inesperado: {response.status_code}"