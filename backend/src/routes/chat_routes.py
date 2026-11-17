# --- Les routes des discussions ---
from fastapi import APIRouter, Depends, HTTPException
from pydantic_ai.messages import ModelMessagesTypeAdapter  # pour relire l'historique enregistré en JSON
from pydantic_core import to_jsonable_python  # pour transformer l'historique en JSON
from sqlmodel import Session, select

from agent import chat_agent, to_display_messages  # notre agent IA + la simplification des messages
from auth import get_current_user_id  # le contrôleur de badge
from database import get_session  # la connexion à la base
from models import Chat  # la table des discussions
from schemas import (  # la forme des données
    ChatCreatedResponse,
    ChatResponse,
    ChatSummary,
    MessageRequest,
    MessageResponse,
)

# Le groupe des routes "/chats".
# prefix="/chats" : toutes les routes de ce fichier commencent par /chats
router = APIRouter(prefix="/chats", tags=["Discussions"])


# Route pour créer une nouvelle discussion (vide) et renvoyer son numéro → POST /chats
@router.post("", response_model=ChatCreatedResponse, status_code=201)
def create_chat(
    user_id: int = Depends(get_current_user_id),  # le contrôleur vérifie le badge
    session: Session = Depends(get_session),
):
    chat = Chat(user_id=user_id)  # une discussion vide, qui appartient à cet utilisateur
    session.add(chat)
    session.commit()
    session.refresh(chat)  # on récupère le numéro créé par la base
    return ChatCreatedResponse(id=chat.id)


# Route pour lister les discussions de l'utilisateur connecté → GET /chats
@router.get("", response_model=list[ChatSummary])
def list_chats(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # Seulement SES discussions, de la plus récente à la plus ancienne
    statement = (
        select(Chat)
        .where(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )
    chats = session.exec(statement).all()
    return [ChatSummary(id=chat.id, created_at=chat.created_at) for chat in chats]


# Route pour lire une discussion (son historique) → GET /chats/{chat_id}
@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    chat = session.get(Chat, chat_id)

    # Elle n'existe pas, ou elle appartient à quelqu'un d'autre → 404
    # (même réponse dans les 2 cas : on ne révèle pas qu'elle existe)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Discussion introuvable")

    return ChatResponse(
        id=chat.id, messages=to_display_messages(chat.messages), created_at=chat.created_at
    )


# Route pour envoyer un message et recevoir la réponse de l'IA → POST /chats/{chat_id}/messages
@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    body: MessageRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # 1. On cherche la discussion, et on vérifie qu'elle appartient à l'utilisateur
    chat = session.get(Chat, chat_id)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Discussion introuvable")

    # 2. On relit l'historique enregistré (JSON) pour le redonner à l'agent
    history = ModelMessagesTypeAdapter.validate_python(chat.messages)

    # 3. On envoie le nouveau message + l'historique à l'IA
    try:
        result = await chat_agent.run(body.content, message_history=history)
    except Exception:
        # L'IA ne répond pas (clé invalide, quota dépassé, panne...) → erreur 502
        raise HTTPException(status_code=502, detail="L'IA n'a pas pu répondre. Réessayez.")

    # 4. On enregistre tout l'historique (ancien + nouveau message + réponse) en JSON
    chat.messages = to_jsonable_python(result.all_messages())
    session.add(chat)
    session.commit()

    # 5. On renvoie la réponse de l'IA
    return MessageResponse(answer=result.output)