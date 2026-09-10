from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, Session as SessionModel
from backend.routers.auth import get_current_user
from backend.schemas.session import SessionCreateResponse, SessionListResponse, SessionResponse, SessionUpdateTitle
from backend.services.openrouter import generate_title


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/", response_model=SessionListResponse)
def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionListResponse:
    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.user_id == current_user.id)
        .order_by(SessionModel.updated_at.desc())
        .all()
    )
    return SessionListResponse(sessions=sessions)


@router.post("/", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionCreateResponse:
    session = SessionModel(user_id=current_user.id, title="Nova conversa")
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionCreateResponse(id=session.id, title=session.title)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionResponse:
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    return session


@router.patch("/{session_id}/title", response_model=SessionResponse)
def update_session_title(
    session_id: int,
    payload: SessionUpdateTitle,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionResponse:
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    session.title = payload.title
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/generate-title", response_model=SessionResponse)
async def generate_session_title(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Gera um titulo automatico para a sessao com base nas mensagens existentes."""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")

    # Pega TODAS as mensagens da conversa para gerar contexto completo
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == str(session_id))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem para gerar titulo.")

    # Monta o contexto completo da conversa com TODAS as mensagens
    conversation_lines = []
    for m in messages:
        prefix = "Usuario" if m.role == "user" else "Assistente"
        content = m.content[:300] + ("..." if len(m.content) > 300 else "")
        conversation_lines.append(f"{prefix}: {content}")
    conversation_context = "\n\n".join(conversation_lines)

    try:
        title = await generate_title(conversation_context=conversation_context)
    except Exception:
        # Fallback: extrai da primeira mensagem do usuario
        first_user_msg = ""
        for m in messages:
            if m.role == "user":
                first_user_msg = m.content
                break
        title = first_user_msg[:60] + ("..." if len(first_user_msg) > 60 else "")

    session.title = title
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    # Remove mensagens associadas
    from backend.models import ChatMessage
    db.query(ChatMessage).filter(ChatMessage.session_key == str(session_id)).delete()
    db.delete(session)
    db.commit()