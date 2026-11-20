# --- Les routes de la revue de presse (étape 7) ---
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from auth import get_current_user_id  # le contrôleur de badge
from database import get_session  # la connexion à la base
from models import Chat  # la table des discussions
from review_agent import history_to_text, review_agent  # l'agent revue de presse
from schemas import ReviewRequest, ReviewResponse  # la forme des données

# Pas de prefix ici : les 2 routes n'ont pas le même début d'adresse
router = APIRouter(tags=["Revues de presse"])


# Transforme une discussion de la base en revue prête à envoyer au frontend
def to_review_response(chat: Chat) -> ReviewResponse:
    return ReviewResponse(
        chat_id=chat.id,
        title=chat.review_title,
        synthesis=chat.review_synthesis,
        articles=chat.review_articles,
        created_at=chat.review_created_at,
    )


# Route 1 : générer la revue de presse d'une discussion, sur un thème choisi
@router.post("/chats/{chat_id}/review", response_model=ReviewResponse)
async def generate_review(
    chat_id: int,
    body: ReviewRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # 1. La discussion doit exister et m'appartenir, sinon 404
    chat = session.get(Chat, chat_id)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Discussion introuvable")

    # 2. Une discussion vide → rien à résumer → 400 (demande incorrecte)
    if not chat.messages:
        raise HTTPException(status_code=400, detail="La discussion est vide : envoyez d'abord un message.")

    # 3. On donne à l'agent le thème + toute la discussion en texte
    prompt = f"Sujet de la revue de presse : {body.topic}\n\nDiscussion :\n\n{history_to_text(chat.messages)}"
    try:
        result = await review_agent.run(prompt)
    except Exception:
        raise HTTPException(status_code=502, detail="L'IA n'a pas pu générer la revue de presse. Réessayez.")

    # 4. result.output est un PressReview rempli : on le range dans la base
    review = result.output
    chat.review_title = review.title
    chat.review_synthesis = review.synthesis
    chat.review_articles = [article.model_dump() for article in review.articles]
    chat.review_created_at = datetime.now(timezone.utc)
    session.add(chat)
    session.commit()
    session.refresh(chat)

    return to_review_response(chat)


# Route 2 : lire toutes MES revues de presse (de toutes mes discussions)
@router.get("/reviews", response_model=list[ReviewResponse])
def list_reviews(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # Mes discussions qui ont une revue, la plus récente en premier
    statement = (
        select(Chat)
        .where(Chat.user_id == user_id, Chat.review_title.is_not(None))
        .order_by(Chat.review_created_at.desc())
    )
    return [to_review_response(chat) for chat in session.exec(statement).all()]