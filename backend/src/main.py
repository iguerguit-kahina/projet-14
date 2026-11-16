# --- Les librairies et fichiers dont on a besoin ---
from database import init_db, engine  # la connexion à la base (fichier du CTO)
from fastapi import Depends, FastAPI, HTTPException  # pour créer l'API et les erreurs
from fastapi.middleware.cors import CORSMiddleware  # pour autoriser le frontend à parler au backend
from pydantic import BaseModel, Field  # pour décrire la forme des données (🆕 Field)
from pydantic_ai.messages import ModelMessagesTypeAdapter  # 🆕 pour relire l'historique enregistré en JSON
from pydantic_core import to_jsonable_python  # 🆕 pour transformer l'historique en JSON
from sqlmodel import Session, select  # pour lire dans la base de données
from datetime import datetime  # pour la date de création des discussions
import uvicorn  # le serveur qui fait tourner le backend

from agent import chat_agent  # 🆕 notre agent IA
from auth import create_access_token, get_current_user_id, verify_password  # nos outils de auth.py
from models import Chat, User  # les tables : utilisateurs et discussions

# On crée l'application backend
app = FastAPI()

# Liste des adresses du frontend autorisées à parler au backend (CORS)
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # le frontend en local
    "https://projet-14-beta.vercel.app",  # le frontend en ligne (Vercel)
]

# On active le CORS : le navigateur laissera passer les demandes de ces adresses
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # les adresses autorisées
    allow_methods=["*"],  # toutes les méthodes (GET, POST...)
    allow_headers=["*"],  # tous les en-têtes (dont celui qui contiendra le badge)
)


# Ouvre une connexion à la base de données pour une requête, puis la referme
def get_session():
    with Session(engine) as session:
        yield session  # on "prête" la connexion à la route, puis on la referme


# Ce que le frontend doit envoyer pour se connecter
class LoginRequest(BaseModel):
    email: str  # l'email (du texte)
    password: str  # le mot de passe (du texte)


# Ce que le backend renvoie si la connexion réussit : le badge (token)
class LoginResponse(BaseModel):
    access_token: str  # le badge
    token_type: str = "bearer"  # le type de badge ("bearer" = "porteur", le standard)


# Ce que le backend renvoie quand une discussion est créée : son numéro
class ChatCreatedResponse(BaseModel):
    id: int


# Ce que le backend renvoie quand on lit une discussion
class ChatResponse(BaseModel):
    id: int  # le numéro de la discussion
    messages: list  # l'historique des messages
    created_at: datetime  # la date de création


# Ce que le backend renvoie pour chaque discussion dans la liste : son numéro et sa date
class ChatSummary(BaseModel):
    id: int
    created_at: datetime


# 🆕 Ce que le frontend envoie : le message de l'utilisateur (au moins 1 caractère)
class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


# 🆕 Ce que le backend renvoie : la réponse de l'IA
class MessageResponse(BaseModel):
    answer: str


# Route de test : affiche 👋 (déjà écrite par le CTO)
@app.get("/")
async def hello():
    return {"message": "👋"}


# Route de connexion : vérifie l'email et le mot de passe, puis renvoie un token JWT
@app.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    # 1. On cherche l'utilisateur avec cet email dans la base
    statement = select(User).where(User.email == credentials.email)
    user = session.exec(statement).first()

    # 2. S'il n'existe pas, ou si le mot de passe est faux → erreur 401 (non autorisé)
    #    Même message dans les 2 cas : on ne révèle pas si l'email existe (sécurité).
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # 3. Tout est bon → on crée le badge et on le renvoie
    return LoginResponse(access_token=create_access_token(user.id))


# Route pour créer une nouvelle discussion (vide) et renvoyer son numéro
@app.post("/chats", response_model=ChatCreatedResponse, status_code=201)
def create_chat(
    user_id: int = Depends(get_current_user_id),  # le contrôleur vérifie le badge
    session: Session = Depends(get_session),  # la connexion à la base
):
    # 1. On crée une discussion vide, qui appartient à cet utilisateur
    chat = Chat(user_id=user_id)

    # 2. On l'enregistre dans la base
    session.add(chat)
    session.commit()
    session.refresh(chat)  # on récupère le numéro créé par la base

    # 3. On renvoie son numéro
    return ChatCreatedResponse(id=chat.id)


# Route pour lister les discussions de l'utilisateur connecté (pour la colonne de gauche)
@app.get("/chats", response_model=list[ChatSummary])
def list_chats(
    user_id: int = Depends(get_current_user_id),  # le contrôleur vérifie le badge
    session: Session = Depends(get_session),
):
    # On prend seulement SES discussions, de la plus récente à la plus ancienne
    statement = (
        select(Chat)
        .where(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )
    chats = session.exec(statement).all()

    # On renvoie le numéro et la date de chaque discussion
    return [ChatSummary(id=chat.id, created_at=chat.created_at) for chat in chats]


# Route pour lire une discussion (son historique)
@app.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,  # le numéro de la discussion, lu dans l'adresse
    user_id: int = Depends(get_current_user_id),  # le contrôleur vérifie le badge
    session: Session = Depends(get_session),
):
    # 1. On cherche la discussion avec ce numéro
    chat = session.get(Chat, chat_id)

    # 2. Elle n'existe pas, ou elle appartient à quelqu'un d'autre → 404
    #    (même réponse dans les 2 cas : on ne révèle pas qu'elle existe)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="Discussion introuvable")

    # 3. Tout est bon → on renvoie la discussion
    return ChatResponse(id=chat.id, messages=chat.messages, created_at=chat.created_at)


# 🆕 Route pour envoyer un message dans une discussion, et recevoir la réponse de l'IA
@app.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    body: MessageRequest,  # le message envoyé par l'utilisateur
    user_id: int = Depends(get_current_user_id),  # le contrôleur vérifie le badge
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


# Ce qui se passe quand on lance le fichier avec "uv run ... src/main.py"
if __name__ == "__main__":
    init_db()  # prépare la base (table + utilisateur test)
    uvicorn.run(app, host="0.0.0.0", port=8000)  # démarre le serveur sur le port 8000