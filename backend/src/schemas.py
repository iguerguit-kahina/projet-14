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


# --- Étape 7 : le format de la revue de presse (sortie structurée) ---

# Le formulaire d'un article
class ArticleSummary(BaseModel):
    title: str = Field(description="Le titre de l'article")
    source: str = Field(description="Le média, par exemple Radio France")
    date: str | None = Field(default=None, description="La date de l'article, si elle est connue")
    url: str | None = Field(default=None, description="Le lien de l'article, s'il est connu")
    summary: str = Field(description="Le résumé de l'article en 2 ou 3 phrases")


# Le formulaire de la revue de presse complète
class PressReview(BaseModel):
    title: str = Field(description="Le titre de la revue de presse")
    synthesis: str = Field(description="La synthèse générale du sujet")
    articles: list[ArticleSummary] = Field(description="Les articles de la discussion sur ce sujet")

# Ce que le frontend envoie pour générer une revue : le thème choisi
class ReviewRequest(BaseModel):
    topic: str = Field(min_length=1)


# Ce que le backend renvoie pour une revue de presse
class ReviewResponse(BaseModel):
    chat_id: int  # la discussion d'où vient la revue
    title: str
    synthesis: str
    articles: list[ArticleSummary]
    created_at: datetime  # la date de la revue