# --- La connexion à la base de données (fichier du CTO, complété aux étapes 5 et 7) ---
import os  # pour lire les variables du fichier .env
from models import User  # la table des utilisateurs
from sqlmodel import SQLModel, Session, create_engine, select  # pour créer les tables et parler à la base
import bcrypt  # pour hacher le mot de passe du compte de test
from sqlalchemy import text  # pour écrire une commande SQL directement

# L'adresse de la base, lue dans le .env (en local) ou dans les Variables de Railway (en ligne)
DATABASE_URL = os.getenv("DATABASE_URL")

# La connexion à la base.
engine = create_engine(DATABASE_URL, echo=True)


# Prépare la base au démarrage du backend (appelée dans main.py)
def init_db():
    # 1. Crée toutes les tables décrites dans models.py ("user" et "chat"), si elles n'existent pas
    SQLModel.metadata.create_all(engine)

    # 2. La table "chat" existe déjà : create_all n'y ajoute pas les nouvelles colonnes.
    #    On les ajoute donc à la main, seulement si elles n'existent pas encore 
    with engine.begin() as connection:
        # Étape 5 : le prompt avec les actualités du jour
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS system_prompt TEXT"))
        # Étape 7 : les colonnes de la revue de presse
        # VARCHAR = texte court ; TEXT = texte long ; JSON = liste ; TIMESTAMP = date + heure
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS review_title VARCHAR"))
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS review_synthesis TEXT"))
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS review_articles JSON"))
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS review_created_at TIMESTAMP"))
    print("Database initialized successfully")

    # 3. Le compte de test : test@test.com / test
    #    L'application n'a pas de page d'inscription : sans ce compte,
    #    personne ne pourrait se connecter. Il est créé seulement s'il n'existe pas encore.
    default_email = "test@test.com"
    default_password = "test"

    with Session(engine) as session:
        # On cherche si ce compte existe déjà
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        # S'il n'existe pas, on le crée, avec le mot de passe haché par bcrypt (jamais en clair).
        # Remarque : le hachage est enregistré sous la forme "\x2432..." (hexadécimal),
        # c'est pour ça que verify_password (auth.py) le reconvertit avant de comparer.
        if not user:
            session.add(
                User(
                    email=default_email,
                    hashed_password=bcrypt.hashpw(
                        default_password.encode("utf-8"), bcrypt.gensalt()
                    ),
                )
            )
            session.commit()  # on enregistre dans la base


# Ouvre une connexion à la base de données pour une requête, puis la referme
def get_session():
    with Session(engine) as session:
        yield session  # on "prête" la connexion à la route, puis on la referme