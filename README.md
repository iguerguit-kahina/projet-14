# NewsFoundry

NewsFoundry aide les journalistes pigistes à préparer leurs revues de presse.
L'utilisateur discute avec une IA qui connaît l'actualité du jour, peut chercher des articles récents, puis génère une revue de presse structurée à partir de la discussion.

## Application en ligne

| Partie | Hébergement | URL |
|---|---|---|
| Frontend | Vercel | https://projet-14-beta.vercel.app |
| Backend (API) | Railway | https://projet-14-production.up.railway.app |
| Documentation de l'API (Swagger) | Railway | https://projet-14-production.up.railway.app/docs |

Compte de démonstration : `test@test.com` / `test`

## Documentation technique

| Fichier | Contenu |
|---|---|
| [Architecture](docs/architecture.md) | structure des dossiers, tables, routes, erreurs de l'API, parcours d'un message, les deux agents |
| [Choix techniques](docs/choix-techniques.md) | les choix faits pendant le projet, et leurs raisons (dont les choix de prompts) |
| [Installation et tests](docs/installation-et-tests.md) | lancer le projet en local, lancer les tests, CI, déploiement |
| [Pistes d'amélioration](docs/ameliorations.md) | qualité et performance de la partie IA : mesures, solutions, objectifs |

## Stack

- **Backend** : Python, FastAPI, SQLModel, PydanticAI, Mistral (dossier `backend/`)
- **Frontend** : Next.js, Tailwind CSS (dossier `frontend/`)
- **Base de données** : PostgreSQL
- **Actualités** : World News API

## Démarrage rapide

```bash
# Backend (après avoir rempli backend/.env et lancé PostgreSQL)
cd backend
uv sync
uv run --env-file .env src/main.py

# Frontend
cd frontend
npm install
npm run dev
```

## Lancer les tests

```bash
cd backend
uv run pytest
```

Les tests sont aussi lancés automatiquement par GitHub Actions à chaque push sur `main`.
Le détail de toutes ces étapes est dans [Installation et tests](docs/installation-et-tests.md).
