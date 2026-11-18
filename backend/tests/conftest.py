import os

# On donne des réglages de test AVANT de charger le code du backend.
# "sqlite://" = une base de données temporaire, en mémoire (pas besoin de Docker).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "une-cle-secrete-uniquement-pour-les-tests-automatiques")
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # cache un message d'information de PydanticAI

import bcrypt  # pour cacher les mots de passe des faux utilisateurs
import pytest  # la librairie de tests
from fastapi.testclient import TestClient  # pour simuler des demandes, comme le frontend
from pydantic_ai import models  # pour bloquer les vrais appels au LLM
from sqlalchemy.pool import StaticPool  # pour garder la base en mémoire pendant un test
from sqlmodel import Session, SQLModel, create_engine

from auth import create_access_token  # pour fabriquer les badges de test
from database import get_session  # la connexion à la base (elle est maintenant dans database.py)
from main import app  # l'application
from models import User  # la table des utilisateurs

# Sécurité : interdit tout appel au vrai Mistral pendant les tests
models.ALLOW_MODEL_REQUESTS = False


# Fixture : une base de données vide, toute neuve pour CHAQUE test
@pytest.fixture
def session():
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)  # crée les tables user et chat
    with Session(test_engine) as session:
        yield session


# Fixture : un "faux navigateur" qui envoie des demandes au backend
# On remplace la vraie base par la base de test
@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()  # on remet tout comme avant


# Outil : crée un utilisateur dans la base de test
def create_user(session, email, password):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email=email, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# Fixtures : nos 2 faux utilisateurs, Alice et Bob
@pytest.fixture
def alice(session):
    return create_user(session, "alice@test.com", "motdepasse-alice")


@pytest.fixture
def bob(session):
    return create_user(session, "bob@test.com", "motdepasse-bob")


# Fixtures : le badge de chaque utilisateur, prêt à être envoyé
@pytest.fixture
def alice_headers(alice):
    return {"Authorization": f"Bearer {create_access_token(alice.id)}"}


@pytest.fixture
def bob_headers(bob):
    return {"Authorization": f"Bearer {create_access_token(bob.id)}"}



# Fausses actualités, utilisées à la place de World News API pendant les tests
FAKE_ARTICLES = [{"title": "Titre de test", "summary": "Résumé de test"}]


# autouse=True : cette fixture s'applique AUTOMATIQUEMENT à tous les tests.
# Elle remplace fetch_top_news par une fonction qui renvoie les fausses actualités.
@pytest.fixture(autouse=True)
def fake_news(monkeypatch):
    monkeypatch.setattr("routes.chat_routes.fetch_top_news", lambda: FAKE_ARTICLES)