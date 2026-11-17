# --- Le point d'entrée du backend : il crée l'appli et branche les routes ---
import uvicorn  # le serveur qui fait tourner le backend
from fastapi import FastAPI  # pour créer l'API
from fastapi.middleware.cors import CORSMiddleware  # pour autoriser le frontend à parler au backend

from database import init_db  # la préparation de la base (fichier du CTO)
from routes import auth_routes, chat_routes  # nos groupes de routes

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
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Route de test : affiche 👋 (déjà écrite par le CTO)
@app.get("/")
async def hello():
    return {"message": "👋"}


# On branche les groupes de routes
app.include_router(auth_routes.router)  # la route /login
app.include_router(chat_routes.router)  # les routes /chats


# Ce qui se passe quand on lance le fichier avec "uv run ... src/main.py"
if __name__ == "__main__":
    init_db()  # prépare la base (table + utilisateur test)
    uvicorn.run(app, host="0.0.0.0", port=8000)  # démarre le serveur sur le port 8000