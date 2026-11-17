# --- La forme des données envoyées et reçues par les routes ---
from datetime import datetime  # pour les dates

from pydantic import BaseModel, Field  # pour décrire la forme des données


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


# Un message simple, prêt à afficher dans une bulle
class DisplayMessage(BaseModel):
    role: str  # "user" (l'utilisateur) ou "assistant" (l'IA)
    content: str  # le texte du message
    timestamp: datetime  # l'heure du message


# Ce que le backend renvoie quand on lit une discussion
class ChatResponse(BaseModel):
    id: int  # le numéro de la discussion
    messages: list[DisplayMessage]  # l'historique, en messages simples
    created_at: datetime  # la date de création


# Ce que le backend renvoie pour chaque discussion dans la liste : son numéro et sa date
class ChatSummary(BaseModel):
    id: int
    created_at: datetime


# Ce que le frontend envoie : le message de l'utilisateur (au moins 1 caractère)
class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


# Ce que le backend renvoie : la réponse de l'IA
class MessageResponse(BaseModel):
    answer: str