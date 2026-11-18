# --- La librairie dont on a besoin ---
from pydantic_ai import Agent  # pour créer un agent (un LLM avec un rôle et des instructions)
from datetime import date  # pour la date du jour
# Le modèle Mistral utilisé : "small" est rapide et peu cher
MODEL_NAME = "mistral:mistral-small-latest"

# Le prompt système : les instructions qui définissent le comportement de l'assistant
BASE_SYSTEM_PROMPT = """Tu es l'assistant de NewsFoundry, un outil qui aide les journalistes pigistes à préparer leurs revues de presse.

Ton rôle : aider l'utilisateur à explorer l'actualité, à rassembler des informations sur un sujet et à préparer une revue de presse.

Règles :
- Réponds toujours en français.
- Adopte un ton professionnel, neutre et factuel, comme un journaliste.
- Sois clair et concis : commence par un court résumé, puis présente les points clés sous forme de liste à puces.
- Ne jamais inventer d'informations, de chiffres ou de sources. Si tu ne connais pas une information récente, dis-le clairement.
- Quand c'est pertinent, propose à l'utilisateur de générer une revue de presse sur le sujet abordé."""

# Fabrique le prompt complet : le prompt de base + les actualités du jour.
# articles = la liste renvoyée par fetch_top_news() : [{"title": ..., "summary": ...}]
def build_system_prompt(articles: list[dict]) -> str:
    # Pas d'actualités (API en panne...) → on prévient l'IA, pour qu'elle ne les invente pas
    if not articles:
        return (
            BASE_SYSTEM_PROMPT
            + "\n\nAucune actualité du jour n'a pu être chargée. "
            "Si on te demande l'actualité récente, dis-le clairement."
        )

    today = date.today().strftime("%d/%m/%Y")  # la date du jour, ex : 18/11/2026
    news_lines = "\n".join(f"- {article['title']} : {article['summary']}" for article in articles)

    return f"""{BASE_SYSTEM_PROMPT}

Voici les actualités du jour ({today}), issues de World News API :
{news_lines}

Pour toute question sur l'actualité, appuie-toi en priorité sur ces actualités. Ne présente pas des informations plus anciennes comme si elles étaient récentes."""

# L'agent du chat.
# defer_model_check=True : la clé Mistral n'est vérifiée qu'au moment d'appeler le LLM.
# Utile pour les tests automatiques, qui n'auront pas de vraie clé.
# L'agent du chat. Il n'a plus de prompt fixe : chaque discussion aura SON prompt
# (avec les actualités de son jour), enregistré dans la base.
chat_agent = Agent(MODEL_NAME, defer_model_check=True)
# --- Pour transformer l'historique de PydanticAI en messages simples à afficher ---
from pydantic_ai.messages import (
    ModelMessagesTypeAdapter,  # pour relire l'historique enregistré en JSON
    ModelRequest,  # un message envoyé AU modèle (dont celui de l'utilisateur)
    ModelResponse,  # une réponse DU modèle
    TextPart,  # un morceau de texte dans la réponse
    UserPromptPart,  # le message tapé par l'utilisateur
)


# Transforme l'historique complet en une liste simple : rôle, texte, heure.
# On garde seulement les messages de l'utilisateur et les réponses de l'IA
# (pas le prompt système ni les informations techniques).
def to_display_messages(raw_messages: list) -> list[dict]:
    display = []
    for message in ModelMessagesTypeAdapter.validate_python(raw_messages):
        # Message de l'utilisateur
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    display.append(
                        {"role": "user", "content": part.content, "timestamp": part.timestamp}
                    )
        # Réponse de l'IA
        elif isinstance(message, ModelResponse):
            text = "".join(part.content for part in message.parts if isinstance(part, TextPart))
            if text:
                display.append(
                    {"role": "assistant", "content": text, "timestamp": message.timestamp}
                )
    return display