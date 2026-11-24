# Installation, tests et déploiement

## Prérequis

- Docker (pour la base PostgreSQL en local)
- Python 3.13 ou plus
- uv (gestionnaire de dépendances Python)
- Node.js 22 ou plus

## Les variables d'environnement

### Backend : fichier `backend/.env`

Copier `backend/.env.example` dans `backend/.env`, puis remplir :

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | l'adresse de la base PostgreSQL (`postgresql://user:password@localhost:5432/newsfoundry` en local) |
| `JWT_SECRET` | la clé secrète qui signe les badges JWT (une longue chaîne aléatoire) |
| `MISTRAL_API_KEY` | la clé de l'API Mistral (le LLM) |
| `WORLD_NEWS_API_KEY` | la clé de World News API (les articles) |

Le fichier `.env` contient des secrets : il est dans le `.gitignore` et ne doit jamais être poussé sur GitHub.

### Frontend : fichier `frontend/.env.local`

| Variable | Rôle |
|---|---|
| `NEXT_PUBLIC_API_URL` | l'adresse du backend (`http://localhost:8000` en local) |

## Lancer le projet en local

### 1. La base de données

```bash
docker run --name newsfoundry_db \
  -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=newsfoundry \
  -p 5432:5432 postgres:17
```

Cette commande lance PostgreSQL dans Docker, avec :

- un utilisateur `user`, de mot de passe `password` ;
- une base appelée `newsfoundry` ;
- le port `5432` ouvert sur l'ordinateur.

Ce sont exactement les réglages de `DATABASE_URL` dans `backend/.env` :
`postgresql://user:password@localhost:5432/newsfoundry`.
Le backend trouve ainsi la base au démarrage.

### 2. Le backend

```bash
cd backend
uv sync
uv run --env-file .env src/main.py
```

- L'API tourne sur http://localhost:8000.
- La documentation interactive (Swagger) est sur http://localhost:8000/docs.
- Au démarrage, `init_db()` crée les tables, ajoute les colonnes manquantes et crée un compte de test : `test@test.com` / `test`.

### 3. Le frontend

```bash
cd frontend
npm install
npm run dev
```

L'application est sur http://localhost:3000.

## Lancer les tests

Les tests se lancent depuis le dossier `backend` :

```bash
cd backend
uv run pytest
```

Pour voir le nom de chaque test :

```bash
uv run pytest -v
```

Résultat attendu : `13 passed`.

### Ce que les tests vérifient

| Fichier | Tests |
|---|---|
| `test_auth.py` | login avec le bon mot de passe (200) et un mauvais (401) |
| `test_chats.py` | créer une discussion sans badge (401), créer et lire une discussion, envoyer un message ; **sécurité** : Bob ne peut ni lire, ni écrire dans la discussion d'Alice (404), et ne la voit pas dans sa liste ; les actualités du jour sont bien dans le prompt ; l'outil de recherche est bien appelé |
| `test_reviews.py` | générer une revue puis la retrouver dans la liste ; **sécurité** : Bob ne peut ni générer ni voir la revue d'Alice ; une discussion vide renvoie 400 |

### Comment les tests restent rapides et gratuits

- **Base de données** : une base SQLite en mémoire, recréée pour chaque test (`conftest.py`). Les tests ne touchent jamais la vraie base.
- **LLM** : Mistral est remplacé par les faux modèles de PydanticAI (`TestModel`, `FunctionModel`). `ALLOW_MODEL_REQUESTS = False` empêche tout appel réel par erreur.
- **World News API** : les fonctions `fetch_top_news` et `search_news` sont remplacées par de fausses fonctions (`monkeypatch`). Aucun quota n'est utilisé.
- Aucune clé d'API n'est donc nécessaire pour lancer les tests.

## Intégration continue (CI)

Le fichier `.github/workflows/tests.yml` lance automatiquement les tests sur GitHub Actions :

- à chaque `git push` sur `main` ;
- à chaque pull request ;
- à la main, avec le bouton « Run workflow ».

GitHub installe le projet sur un ordinateur neuf (`uv sync`), puis lance `uv run pytest`. Le résultat est visible dans l'onglet **Actions** du dépôt.

## Déploiement

Le déploiement est automatique : GitHub sert d'intermédiaire. Vercel et Railway sont connectés au dépôt GitHub, et chaque `git push` sur `main` met à jour les deux parties.

### Les secrets en ligne

Le fichier `.env` n'est pas sur GitHub : Vercel et Railway reçoivent donc le code **sans aucun secret**.
Les variables ont été renseignées **à la main**, sur les sites de Railway et de Vercel (page **Variables** de chaque service). Elles remplacent le `.env` en production : sans elles, le backend en ligne ne trouverait ni la base de données, ni Mistral, ni World News API.

Pour déployer le projet sur un autre compte, il faut donc remplir soi-même ces variables, avec ses propres clés (voir la liste ci-dessous).

### Frontend : Vercel

- **Root Directory** : `frontend`
- **Variable** : `NEXT_PUBLIC_API_URL` = l'URL du backend sur Railway (sans `/` à la fin)

### Backend et base de données : Railway

- Le backend est construit avec `backend/Dockerfile`.
- **Root Directory** : `/` (la racine du dépôt), car le Dockerfile copie `backend/...`
- **Variables** :
  - `RAILWAY_DOCKERFILE_PATH` = `backend/Dockerfile`
  - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (la base PostgreSQL du projet Railway)
  - `JWT_SECRET` (une clé différente de celle utilisée en local), `MISTRAL_API_KEY`, `WORLD_NEWS_API_KEY`
- Le domaine public pointe vers le port `8000`.
- Les nouvelles colonnes sont ajoutées automatiquement au démarrage par `init_db()`.

Le backend autorise uniquement le frontend local et le frontend Vercel à l'appeler (CORS, liste `ALLOWED_ORIGINS` dans `main.py`).
