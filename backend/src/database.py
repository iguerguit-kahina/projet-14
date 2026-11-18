import os
from models import User
from sqlmodel import SQLModel, Session, create_engine, select
import bcrypt
from sqlalchemy import text  # pour écrire une commande SQL directement

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
    # La table "chat" existe déjà : create_all n'y ajoute pas les nouvelles colonnes.
    # On ajoute donc la colonne "system_prompt" à la main, si elle n'existe pas encore.
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE chat ADD COLUMN IF NOT EXISTS system_prompt TEXT"))
    print("Database initialized successfully")

    # Creating a default user
    default_email = "test@test.com"
    default_password = "test"

    with Session(engine) as session:
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        if not user:
            session.add(
                User(
                    email=default_email,
                    hashed_password=bcrypt.hashpw(
                        default_password.encode("utf-8"), bcrypt.gensalt()
                    ),
                )
            )
            session.commit()


# Ouvre une connexion à la base de données pour une requête, puis la referme
def get_session():
    with Session(engine) as session:
        yield session  # on "prête" la connexion à la route, puis on la referme