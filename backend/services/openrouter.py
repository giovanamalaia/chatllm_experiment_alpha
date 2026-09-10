from __future__ import annotations

import json

import httpx

from backend.config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL_DEFAULT


class OpenRouterConfigError(RuntimeError):
    pass


_SYSTEM_PROMPT = (
    "Keep your answers short and concise. "
    "When writing mathematical expressions, use LaTeX notation: "
    r"\( ... \) for inline math and $$ ... $$ for display/block math. "
    "When writing currency values (e.g. dollar amounts), always escape the dollar sign as the HTML entity &#36; "
    "(e.g. write &#36;5.00 instead of $5.00) so it is never confused with a LaTeX delimiter."
)


def _build_messages(*, user_message: str, history: list[dict]) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for item in history:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content.strip()})

    messages.append({"role": "user", "content": user_message.strip()})
    return messages


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ChatLLM Experiment",
    }


async def generate_reply(*, user_message: str, history: list[dict], model: str | None = None) -> tuple[str, str]:
    if not OPENROUTER_API_KEY:
        raise OpenRouterConfigError(
            "OPENROUTER_API_KEY nao definido. Configure em .env ou environment variables."
        )

    resolved_model = model or OPENROUTER_MODEL_DEFAULT
    messages = _build_messages(user_message=user_message, history=history)

    payload = {
        "model": resolved_model,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=_build_headers())
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de conexao com OpenRouter: {exc}") from exc

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter retornou erro {response.status_code}: {response.text}")

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    reply = content.strip()
    if not reply:
        raise RuntimeError("OpenRouter nao retornou conteudo de resposta.")

    return reply, resolved_model


async def stream_reply(*, user_message: str, history: list[dict], model: str | None = None):
    if not OPENROUTER_API_KEY:
        raise OpenRouterConfigError(
            "OPENROUTER_API_KEY nao definido. Configure em .env ou environment variables."
        )

    resolved_model = model or OPENROUTER_MODEL_DEFAULT
    payload = {
        "model": resolved_model,
        "messages": _build_messages(user_message=user_message, history=history),
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            async with client.stream("POST", OPENROUTER_API_URL, json=payload, headers=_build_headers()) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise RuntimeError(
                        f"OpenRouter retornou erro {response.status_code}: {body.decode(errors='replace')}"
                    )

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break

                    try:
                        parsed = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                    if isinstance(delta, str) and delta:
                        yield delta
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha de conexao com OpenRouter: {exc}") from exc


async def generate_title(*, conversation_context: str) -> str:
    """Gera um titulo curto para a conversa com base no contexto completo do dialogo."""
    if not OPENROUTER_API_KEY:
        first_line = conversation_context.split("\n")[0] if conversation_context else "Conversa"
        first_line = first_line.replace("Usuario: ", "").replace("Assistente: ", "")
        return first_line[:60] + ("..." if len(first_line) > 60 else "")

    system_prompt = (
        "You are a title generator. Given a conversation, generate a very short title (maximum 8 words) "
        "in the same language as the conversation that summarizes the main topic. "
        "The title should be specific enough to distinguish different conversations. "
        "For example: 'Aprendendo React do zero', 'Viagem para Sao Paulo', 'Erro no código Python'. "
        "Respond with ONLY the title, no quotes, no punctuation at the end, no extra text."
    )

    payload = {
        "model": OPENROUTER_MODEL_DEFAULT,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a short title for this conversation:\n\n{conversation_context}"},
        ],
        "max_tokens": 30,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=_build_headers())
        except httpx.HTTPError:
            first_line = conversation_context.split("\n")[0] if conversation_context else "Conversa"
            first_line = first_line.replace("Usuario: ", "").replace("Assistente: ", "")
            return first_line[:60] + ("..." if len(first_line) > 60 else "")

    if response.status_code >= 400:
        first_line = conversation_context.split("\n")[0] if conversation_context else "Conversa"
        first_line = first_line.replace("Usuario: ", "").replace("Assistente: ", "")
        return first_line[:60] + ("..." if len(first_line) > 60 else "")

    try:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if content:
            clean = content.strip("\"'").strip()
            return clean[:80]
    except (KeyError, IndexError, json.JSONDecodeError):
        pass

    first_line = conversation_context.split("\n")[0] if conversation_context else "Conversa"
    first_line = first_line.replace("Usuario: ", "").replace("Assistente: ", "")
    return first_line[:60] + ("..." if len(first_line) > 60 else "")
