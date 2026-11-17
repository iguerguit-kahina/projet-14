# --- Les routes de connexion ---
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from auth import create_access_token, verify_password  # nos outils de auth.py
from database import get_session  # la connexion à la base
from models import User  # la table des utilisateurs
from schemas import LoginRequest, LoginResponse  # la forme des données

# Un "routeur" : un groupe de routes, qu'on branchera dans main.py.
# tags = le nom du groupe affiché dans la page /docs
router = APIRouter(tags=["Authentification"])


# Route de connexion : vérifie l'email et le mot de passe, puis renvoie un token JWT
@router.post("/login", response_model=LoginResponse)
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