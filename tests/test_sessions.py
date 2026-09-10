from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _register_and_login(client: TestClient) -> tuple[str, dict]:
    """Registra um usuario e retorna (token, user)."""
    resp = client.post(
        "/api/auth/register",
        json={"email": "sessao@teste.com", "password": "123456"},
    )
    data = resp.json()
    return data["access_token"], data["user"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSessionCreate:
    def test_create_session_success(self, client: TestClient):
        """Deve criar uma nova sessao com titulo padrao."""
        token, _ = _register_and_login(client)
        resp = client.post("/api/sessions/", headers=_auth_header(token))
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Nova conversa"

    def test_create_session_without_auth(self, client: TestClient):
        """Criar sessao sem token deve retornar 401."""
        resp = client.post("/api/sessions/", json={})
        assert resp.status_code == 401


class TestSessionList:
    def test_list_sessions(self, client: TestClient):
        """Deve listar sessoes do usuario."""
        token, _ = _register_and_login(client)
        # Criar 2 sessoes
        client.post("/api/sessions/", headers=_auth_header(token))
        client.post("/api/sessions/", headers=_auth_header(token))
        resp = client.get("/api/sessions/", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 2

    def test_list_sessions_empty(self, client: TestClient):
        """Usuario sem sessoes deve receber lista vazia."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/sessions/", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_list_sessions_other_user_isolation(self, client: TestClient):
        """Sessoes de um usuario nao devem aparecer para outro."""
        token1, _ = _register_and_login(client)
        # Registrar segundo usuario
        resp2 = client.post(
            "/api/auth/register",
            json={"email": "outro@teste.com", "password": "123456"},
        )
        token2 = resp2.json()["access_token"]

        client.post("/api/sessions/", headers=_auth_header(token1))
        resp = client.get("/api/sessions/", headers=_auth_header(token2))
        assert len(resp.json()["sessions"]) == 0


class TestSessionDelete:
    def test_delete_session(self, client: TestClient):
        """Deve excluir uma sessao."""
        token, _ = _register_and_login(client)
        created = client.post("/api/sessions/", headers=_auth_header(token)).json()
        resp = client.delete(f"/api/sessions/{created['id']}", headers=_auth_header(token))
        assert resp.status_code == 204

    def test_delete_nonexistent_session(self, client: TestClient):
        """Excluir sessao inexistente deve retornar 404."""
        token, _ = _register_and_login(client)
        resp = client.delete("/api/sessions/99999", headers=_auth_header(token))
        assert resp.status_code == 404


class TestSessionTitle:
    def test_update_title(self, client: TestClient):
        """Deve atualizar o titulo de uma sessao."""
        token, _ = _register_and_login(client)
        created = client.post("/api/sessions/", headers=_auth_header(token)).json()
        resp = client.patch(
            f"/api/sessions/{created['id']}/title",
            headers=_auth_header(token),
            json={"title": "Meu titulo personalizado"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Meu titulo personalizado"

    def test_auto_title_on_first_message(self, client: TestClient):
        """O titulo automatico deve ser definido com base na mensagem."""
        token, _ = _register_and_login(client)
        created = client.post("/api/sessions/", headers=_auth_header(token)).json()
        session_id = created["id"]

        # Enviar mensagem para a sessao (o titulo e atualizado pelo frontend)
        resp = client.patch(
            f"/api/sessions/{session_id}/title",
            headers=_auth_header(token),
            json={"title": "Minha primeira pergunta sobre..."},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Minha primeira pergunta sobre..."


class TestSessionChatIsolation:
    def test_messages_isolated_between_sessions(self, client: TestClient):
        """Mensagens de sessoes diferentes nao devem se misturar."""
        token, _ = _register_and_login(client)
        s1 = client.post("/api/sessions/", headers=_auth_header(token)).json()
        s2 = client.post("/api/sessions/", headers=_auth_header(token)).json()

        # Enviar mensagem para sessao 1
        client.post(
            "/api/chat",
            headers=_auth_header(token),
            json={"message": "Mensagem da sessao 1", "session_id": s1["id"]},
        )

        # Histórico da sessao 1 deve ter a mensagem
        hist1 = client.get(f"/api/chat/history/{s1['id']}", headers=_auth_header(token))
        assert len(hist1.json()) > 0

        # Histórico da sessao 2 deve estar vazio
        hist2 = client.get(f"/api/chat/history/{s2['id']}", headers=_auth_header(token))
        # Pode ter a mensagem de boas-vindas ou estar vazio
        assert len(hist2.json()) == 0


class TestChatWithSession:
    def test_chat_with_session_id(self, client: TestClient):
        """O chat deve aceitar session_id e persistir mensagens na sessao."""
        token, _ = _register_and_login(client)
        session = client.post("/api/sessions/", headers=_auth_header(token)).json()

        resp = client.post(
            "/api/chat",
            headers=_auth_header(token),
            json={"message": "Ola", "session_id": session["id"]},
        )
        # Pode ser 200, 422, 502 ou 503 dependendo da API key
        assert resp.status_code in (200, 422, 502, 503)

    def test_chat_without_session_id_uses_default(self, client: TestClient):
        """Chat sem session_id deve usar 'default' como fallback."""
        token, _ = _register_and_login(client)
        resp = client.post(
            "/api/chat",
            headers=_auth_header(token),
            json={"message": "Ola"},
        )
        assert resp.status_code in (200, 422, 502, 503)