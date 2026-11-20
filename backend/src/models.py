# --- Les librairies dont on a besoin ---
from datetime import datetime, timezone  # pour la date de création
from typing import Optional  # pour dire qu'une valeur peut être vide au départ

from sqlalchemy import JSON, Column, Text  # pour les colonnes JSON et les textes longs
from sqlmodel import Field, SQLModel  # pour décrire les tables de la base


# Table "user" : les utilisateurs (déjà écrite par le CTO)
class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)  # le numéro de l'utilisateur
    email: str = Field(unique=True, index=True)  # l'email (unique)
    hashed_password: str = Field()  # le mot de passe caché


# Table "chat" : les discussions
class Chat(SQLModel, table=True):
    # Le numéro de la discussion (créé automatiquement par la base)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Le numéro de l'utilisateur à qui appartient la discussion.
    # "foreign_key" = clé étrangère : elle pointe vers l'id de la table "user"
    user_id: int = Field(foreign_key="user.id", index=True)

    # Tout l'historique des messages, rangé en JSON (vide au départ)
    messages: list = Field(default_factory=list, sa_column=Column(JSON))

    # Le prompt système de cette discussion (prompt de base + actualités de son jour)
    system_prompt: Optional[str] = Field(default=None, sa_column=Column(Text))

    # La date de création de la discussion (remplie automatiquement)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

 # --- Étape 7 : la revue de presse (vide tant qu'elle n'est pas générée) ---
    review_title: Optional[str] = None
    review_synthesis: Optional[str] = Field(default=None, sa_column=Column(Text))
    review_articles: Optional[list] = Field(default=None, sa_column=Column(JSON))
    review_created_at: Optional[datetime] = None
