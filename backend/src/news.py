# --- Tout ce qui concerne World News API (les actualités) ---
import os  # pour lire la clé dans le .env

import httpx  # pour envoyer des demandes sur Internet

# L'adresse de World News API
WORLD_NEWS_API_URL = "https://api.worldnewsapi.com"

# Le nombre maximum d'actualités à garder (pour que le prompt reste court)
MAX_ARTICLES = 10


# Récupère les actualités du jour (route /top-news) et renvoie une liste simple :
# [{"title": "...", "summary": "..."}, ...]
def fetch_top_news(country: str = "fr", language: str = "fr") -> list[dict]:
    # 1. On envoie la demande à World News API, avec la clé dans l'en-tête "x-api-key"
    response = httpx.get(
        f"{WORLD_NEWS_API_URL}/top-news",
        params={"source-country": country, "language": language},  # France, en français
        headers={"x-api-key": os.getenv("WORLD_NEWS_API_KEY")},
        timeout=15,  # on n'attend pas plus de 15 secondes
    )
    response.raise_for_status()  # si l'API renvoie une erreur → on arrête ici

    # 2. La réponse contient des "groupes" d'articles sur le même sujet (top_news).
    #    Pour éviter les doublons, on garde UN seul article par groupe (le 1er).
    articles = []
    for group in response.json().get("top_news", []):
        news = group.get("news", [])
        if not news:
            continue
        first = news[0]
        articles.append(
            {
                "title": first.get("title", ""),
                # On garde le résumé. S'il n'y en a pas, le début du texte (300 caractères).
                "summary": first.get("summary") or first.get("text", "")[:300],
            }
        )
        if len(articles) >= MAX_ARTICLES:
            break

    # 3. On renvoie la liste simple
    return articles



# Le nombre d'articles renvoyés par une recherche (pour que la réponse reste courte)
MAX_SEARCH_RESULTS = 5


# Cherche des articles récents sur un sujet précis (route /search-news).
# Renvoie une liste simple : [{"title", "summary", "date", "url"}, ...]
def search_news(query: str) -> list[dict]:
    # 1. On envoie la demande à World News API
    response = httpx.get(
        f"{WORLD_NEWS_API_URL}/search-news",
        params={
            "text": query,  # les mots-clés à chercher, ex : "grève SNCF"
            "language": "fr",  # des articles en français
            "sort": "publish-time",  # les plus récents d'abord
            "number": MAX_SEARCH_RESULTS,  # 5 articles maximum
        },
        headers={"x-api-key": os.getenv("WORLD_NEWS_API_KEY")},
        timeout=15,
    )
    response.raise_for_status()  # si l'API renvoie une erreur → on arrête ici

    # 2. Pour chaque article, on garde seulement le titre, le résumé, la date et le lien
    return [
        {
            "title": article.get("title", ""),
            "summary": article.get("summary") or article.get("text", "")[:500],
            "date": article.get("publish_date", ""),
            "url": article.get("url", ""),
        }
        for article in response.json().get("news", [])
    ]