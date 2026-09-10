from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestGenerateTitle:
    def test_generate_title_fallback_without_api_key(self):
        """Sem API key, generate_title deve extrair um trecho da conversa."""
        from backend.services.openrouter import generate_title

        import asyncio
        context = "Usuario: Como faço para aprender React do zero?\n\nAssistente: Recomendo começar com os fundamentos de JavaScript, depois estudar componentes, estado e props."
        title = asyncio.run(generate_title(conversation_context=context))
        assert len(title) > 0

    def test_generate_title_empty_context(self):
        """Com contexto vazio, deve retornar fallback."""
        from backend.services.openrouter import generate_title

        import asyncio
        title = asyncio.run(generate_title(conversation_context=""))
        assert len(title) > 0


class TestSessionGenerateTitleEndpoint:
    def test_generate_title_endpoint_no_messages(self, client: TestClient):
        """Endpoint deve retornar 400 se nao houver mensagens."""
        token = _register_and_get_token(client)
        session = client.post("/api/sessions/", headers=_auth_header(token)).json()

        resp = client.post(f"/api/sessions/{session['id']}/generate-title", headers=_auth_header(token))
        assert resp.status_code == 400

    def test_generate_title_endpoint_with_messages(self, client: TestClient):
        """Endpoint deve gerar titulo mesmo que seja fallback."""
        token = _register_and_get_token(client)
        session = client.post("/api/sessions/", headers=_auth_header(token)).json()

        # Adicionar mensagem de usuario
        client.post(
            "/api/chat",
            headers=_auth_header(token),
            json={"message": "Qual a capital do Brasil?", "session_id": session["id"]},
        )

        resp = client.post(f"/api/sessions/{session['id']}/generate-title", headers=_auth_header(token))
        # Pode ser 200 (com titulo gerado) ou 502 (erro de conexao com API)
        assert resp.status_code in (200, 502), f"Status inesperado: {resp.status_code}"

    def test_generate_title_unauthorized(self, client: TestClient):
        """Sem token, deve retornar 401."""
        resp = client.post("/api/sessions/1/generate-title")
        assert resp.status_code == 401

    def test_generate_title_nonexistent_session(self, client: TestClient):
        """Sessao inexistente deve retornar 404."""
        token = _register_and_get_token(client)
        resp = client.post("/api/sessions/99999/generate-title", headers=_auth_header(token))
        assert resp.status_code == 404


def _register_and_get_token(client: TestClient) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"email": f"titulo_{id({client})}@teste.com", "password": "123456"},
    )
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}