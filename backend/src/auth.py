# --- Les librairies dont on a besoin ---
import os  # pour lire les variables du fichier .env
from datetime import datetime, timedelta, timezone  # pour gérer les dates et les durées

import bcrypt  # pour vérifier les mots de passe cachés
import jwt  # pour créer les tokens JWT (les badges)

# --- Les réglages ---
# La clé secrète, lue dans le .env. Elle sert à "signer" les tokens :
# sans elle, personne ne peut fabriquer un faux badge.
JWT_SECRET = os.getenv("JWT_SECRET")

# La méthode de signature utilisée (HS256 est la plus courante)
JWT_ALGORITHM = "HS256"

# Combien de temps le badge reste valable
TOKEN_DURATION_HOURS = 24


# Vérifie que le mot de passe tapé correspond au mot de passe caché en base.
# Renvoie True (vrai) si c'est le bon, False (faux) sinon.
def verify_password(password: str, hashed_password: str) -> bool:
    # Dans la base, le mot de passe caché est enregistré sous la forme "\x2432..."
    # (en hexadécimal). Si c'est le cas, on le reconvertit dans sa forme d'origine.
    if hashed_password.startswith("\\x"):
        hashed_bytes = bytes.fromhex(hashed_password[2:])
    else:
        # Sinon, on le transforme simplement en "bytes" (le format attendu par bcrypt)
        hashed_bytes = hashed_password.encode("utf-8")

    # bcrypt compare le mot de passe tapé avec le mot de passe caché
    return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)


# Crée un token JWT (le badge) valable 24 heures pour cet utilisateur
def create_access_token(user_id: int) -> str:
    # On calcule la date d'expiration : maintenant + 24 heures
    expiration = datetime.now(timezone.utc) + timedelta(hours=TOKEN_DURATION_HOURS)

    # Le contenu du badge :
    # - "sub" (subject) = l'identifiant de l'utilisateur
    # - "exp" (expiration) = la date où le badge n'est plus valable
    payload = {"sub": str(user_id), "exp": expiration}

    # On fabrique le badge et on le signe avec la clé secrète
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)