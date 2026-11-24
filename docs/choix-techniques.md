# Choix techniques

Ce document explique les choix faits pendant le développement, et leurs raisons.
La stack de base (Next.js, FastAPI, SQLModel, PostgreSQL, PydanticAI, World News API, Vercel, Railway)
a été imposée par le CTO (voir le `README.md` à la racine).

## Organisation du code

| Choix | Raison |
|---|---|
| Un **monorepo** (frontend et backend dans le même dépôt) | un seul endroit pour tout le projet ; Vercel et Railway déploient chacun leur dossier |
| Backend découpé en fichiers par rôle : `auth.py`, `news.py`, `agent.py`, `review_agent.py`, `schemas.py`, `models.py` | un fichier = un rôle : on trouve vite le code, et `main.py` reste court (environ 40 lignes) |
| Routes rangées en groupes avec `APIRouter` (`auth_routes.py`, `chat_routes.py`, `review_routes.py`) | éviter d'écrire toutes les routes dans `main.py` : chaque fonctionnalité a son fichier, on retrouve vite une route, et on ajoute une fonctionnalité sans toucher au reste (à l'étape 7 : un nouveau fichier + une ligne dans `main.py`) ; en bonus, les groupes apparaissent séparément dans Swagger |
| Modèles Pydantic dans `schemas.py`, séparés des tables (`models.py`) | les données envoyées au frontend ne sont pas forcément les mêmes que celles de la base (ex : le mot de passe haché n'est jamais renvoyé) |
| Frontend découpé en composants (`Sidebar`, `ChatWindow`, `ReviewModal`, `ReviewsList`) | chaque partie de l'écran a son fichier ; `page.js` les réunit et leur passe les données (props) |

## Authentification

| Choix | Raison |
|---|---|
| Badge **JWT** signé en HS256 avec `JWT_SECRET`, valable 24 heures | demandé par le CTO ; le backend n'a pas besoin de stocker les sessions ; personne ne peut fabriquer un faux badge sans la clé secrète |
| Le badge contient l'**identifiant** de l'utilisateur (`sub`), pas son email | on retrouve directement ses discussions avec `user_id`, et l'email peut changer sans casser les badges |
| Un seul **contrôleur de badge**, `get_current_user_id`, appelé par chaque route avec `Depends` | la vérification est écrite une seule fois : impossible d'oublier de la faire sur une nouvelle route |
| Même message d'erreur (401) pour un email inconnu et un mauvais mot de passe | on ne révèle pas quels emails ont un compte |
| Badge rangé dans le **local storage** du navigateur ; `apiFetch` l'ajoute à chaque demande et renvoie vers `/login` en cas de 401 | demandé par l'énoncé ; tout le frontend passe par un seul outil |
| Un champ mot de passe ajouté à la page de connexion | il manquait sur la maquette, mais il est nécessaire pour se connecter |

## Sécurité des discussions

| Choix | Raison |
|---|---|
| Chaque discussion a un `user_id` ; chaque route vérifie `chat.user_id == user_id` | un utilisateur ne peut lire, écrire ni générer de revue que sur ses propres discussions |
| Réponse **404** (« Discussion introuvable ») plutôt que 403 quand la discussion n'est pas à l'utilisateur | on ne révèle même pas que la discussion existe |
| Des **tests automatiques** dédiés (Bob essaie d'accéder aux données d'Alice) | demandé par le CTO : c'est la fonctionnalité la plus importante à garantir, et les tests tournent à chaque push |

## Le chat avec l'IA

| Choix | Raison |
|---|---|
| **Mistral** (`mistral-small-latest`) comme LLM | compatible avec PydanticAI, peu coûteux, déjà utilisé dans des projets précédents |
| On n'entraîne pas le LLM nous-mêmes : on contrôle son comportement avec le **prompt système** | le modèle est déjà entraîné par Mistral AI ; le prompt suffit pour fixer son rôle, sa langue, son ton et ses règles, sans réentraînement (fine-tuning), qui coûterait cher et demanderait beaucoup de données |
| Tout l'**historique** est enregistré en JSON dans la colonne `messages` et renvoyé à l'IA à chaque message | l'IA se souvient de la conversation, et l'utilisateur peut reprendre une ancienne discussion |
| `to_display_messages` transforme l'historique de PydanticAI en messages simples (`role`, `content`, `timestamp`) | le frontend n'a pas besoin de connaître le format interne de PydanticAI |
| `defer_model_check=True` | la clé Mistral n'est vérifiée qu'au moment d'appeler le LLM : les tests peuvent tourner sans clé |
| Erreur **502** si le LLM ne répond pas | le problème vient d'un service extérieur, pas de la demande de l'utilisateur |
| Les réponses de l'IA sont affichées avec **`react-markdown`** | l'IA écrit en Markdown (`###` pour un titre, `**` pour le gras, `-` pour une liste) ; sans traitement, l'utilisateur verrait ces symboles tels quels. `react-markdown` les transforme en vrais titres, gras et listes |

## Les actualités du jour

| Choix | Raison |
|---|---|
| Les actualités (route `/top-news`, France, en français) sont ajoutées au **prompt système** (`news.py` → `fetch_top_news`, puis `agent.py` → `build_system_prompt`) | sans elles, l'IA ne connaît que ce qu'elle a appris jusqu'à sa date de fin d'entraînement |
| On garde un seul article par sujet, avec seulement le titre et le résumé, 10 maximum (`news.py` → `fetch_top_news`, `MAX_ARTICLES = 10`) | un prompt court : moins de coût, et l'IA reste concentrée |
| Le prompt est fabriqué et **enregistré à la création de chaque discussion** (route `create_chat` dans `chat_routes.py`, colonne `system_prompt` de la table `chat`) | au démarrage du backend, les actualités vieilliraient ; à chaque message, on ferait trop d'appels à l'API et l'IA pourrait se contredire ; enregistré, il reste stable : une discussion de lundi garde les actualités de lundi |
| Si World News API est en panne, la discussion est créée quand même, avec un prompt qui le signale (`try / except` dans `create_chat`, puis `build_system_prompt` sans articles) | une panne extérieure ne doit pas empêcher d'utiliser le chat |
| Les nouvelles colonnes sont ajoutées avec `ALTER TABLE ... IF NOT EXISTS` dans `init_db()` (`database.py`) | `create_all` ne modifie pas une table qui existe déjà ; cette solution simple suffit pour ce projet (voir les pistes d'amélioration : Alembic) |

## L'outil de recherche d'articles

| Choix | Raison |
|---|---|
| Un **outil** (`rechercher_articles`, dans `agent.py`) donné à l'agent du chat, qui appelle `/search-news` (`news.py` → `search_news`) | c'est l'IA qui décide quand chercher et quels mots-clés utiliser, à partir de la demande de l'utilisateur |
| La **docstring** de l'outil explique quand l'utiliser (`agent.py`) | PydanticAI l'envoie au LLM comme mode d'emploi de l'outil |
| Résultats en français, les plus récents d'abord, 5 maximum, avec titre, résumé, date et lien (`news.py` → `search_news`) | des articles récents et une réponse courte ; la date et le lien permettent de citer les sources |
| En cas d'échec ou d'absence de résultat, l'outil renvoie un message à l'IA au lieu de planter (`try / except` dans `rechercher_articles`) | l'IA peut prévenir l'utilisateur, et la discussion continue |
| Règles ajoutées au prompt (`BASE_SYSTEM_PROMPT` dans `agent.py`) : citer les sources (titre, date, lien), ne pas donner de chiffres ou de dates absents des articles | limiter les informations inventées par le LLM |

## La revue de presse

| Choix | Raison |
|---|---|
| Un **second agent** (`review_agent`, dans `review_agent.py`), séparé de celui du chat, **sans outil** | recommandation de l'énoncé : un agent spécialisé dans une seule tâche est plus performant qu'un agent généraliste |
| Une **sortie structurée** (`output_type=PressReview`, formulaire défini dans `schemas.py`) : titre, synthèse générale, liste d'articles (titre, source, date, lien, résumé) | l'IA doit remplir un formulaire au lieu d'écrire un texte libre : le résultat a toujours la même forme et peut être enregistré et affiché directement |
| Date et lien **optionnels** dans le formulaire (`ArticleSummary` dans `schemas.py`) | on ne force pas l'IA à inventer une information absente de la discussion |
| Instructions strictes (`REVIEW_INSTRUCTIONS` dans `review_agent.py`) : utiliser uniquement la discussion, ne rien inventer | la revue doit refléter les articles réellement trouvés |
| L'historique est transformé en **texte simple** (`history_to_text` dans `review_agent.py`), avec les questions, les réponses, les actualités du jour et les articles trouvés par l'outil | l'agent revue de presse voit tout le contexte, y compris les liens des articles, sans dépendre du format des outils de l'agent du chat |
| La revue est stockée dans la table `chat` (4 colonnes `review_...` dans `models.py`, ajoutées par `database.py` ; remplies par `review_routes.py`), **une revue par discussion** | l'énoncé demande d'ajouter les informations de la revue au modèle `Chat`, plutôt que de créer une nouvelle table. Conséquence : chaque discussion n'a de la place que pour une seule revue, et en générer une nouvelle remplace l'ancienne |
| Erreur **400** si la discussion est vide (`review_routes.py`) ; le bouton n'apparaît que s'il y a des messages (`ChatWindow.js`) | il n'y a rien à résumer dans une discussion vide |
| Bouton **Copier** sur chaque revue (`ReviewsList.js`) | le journaliste peut coller la revue où il veut (e-mail, traitement de texte) |

## Tests et qualité

| Choix | Raison |
|---|---|
| Base **SQLite en mémoire** pour les tests (`tests/conftest.py`) | rapide, vide au début de chaque test, et la vraie base n'est jamais touchée |
| Faux LLM de PydanticAI (`TestModel`, `FunctionModel`, dans `test_chats.py` et `test_reviews.py`) et `ALLOW_MODEL_REQUESTS = False` (`conftest.py`) | tests gratuits, rapides, sans clé, avec des réponses prévisibles |
| Faux appels à World News API (`monkeypatch`, dans `conftest.py` et `test_chats.py`) | pas de quota utilisé, et des résultats prévisibles |
| CI avec **GitHub Actions** et `uv` (`.github/workflows/tests.yml`) | les tests tournent sur un ordinateur neuf à chaque push : on détecte un oubli (fichier non commité, dépendance manquante) |
| Version de `httpx2` fixée à `2.15.0` (`backend/pyproject.toml`) | la version suivante provoquait une erreur avec Python 3.13 |

## Déploiement

| Choix | Raison |
|---|---|
| Secrets uniquement dans les variables d'environnement (`.env` en local, Variables sur Railway et Vercel) | aucune clé n'est jamais écrite dans le code ni poussée sur GitHub |
| Une clé `JWT_SECRET` différente en local et en ligne | un badge fabriqué en local ne fonctionne pas en production |
| CORS limité au frontend local et au frontend Vercel | seul notre frontend peut appeler l'API depuis un navigateur |
