# --- Les librairies et fichiers dont on a besoin ---
from database import init_db, engine  # la connexion à la base (fichier du CTO)
from fastapi import Depends, FastAPI, HTTPException  # pour créer l'API et les erreurs
from pydantic import BaseModel  # pour décrire la forme des données
from sqlmodel import Session, select  # pour lire dans la base de données
import uvicorn  # le serveur qui fait tourner le backend

from auth import create_access_token, verify_password  # nos 2 outils de auth.py
from models import User  # la forme d'un utilisateur (email + mot de passe caché)
from fastapi.middleware.cors import CORSMiddleware  # pour autoriser le frontend à parler au backend

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


# Ce qui se passe quand on lance le fichier avec "uv run ... src/main.py"
if __name__ == "__main__":
    init_db()  # prépare la base (table + utilisateur test)
    uvicorn.run(app, host="0.0.0.0", port=8000)  # démarre le serveur sur le port 8000