# --- La librairie dont on a besoin ---
from pydantic_ai import Agent  # pour créer un agent (un LLM avec un rôle et des instructions)

# Le modèle Mistral utilisé : "small" est rapide et peu cher
MODEL_NAME = "mistral:mistral-small-latest"

# Le prompt système : les instructions qui définissent le comportement de l'assistant
SYSTEM_PROMPT = """Tu es l'assistant de NewsFoundry, un outil qui aide les journalistes pigistes à préparer leurs revues de presse.

Ton rôle : aider l'utilisateur à explorer l'actualité, à rassembler des informations sur un sujet et à préparer une revue de presse.

Règles :
- Réponds toujours en français.
- Adopte un ton professionnel, neutre et factuel, comme un journaliste.
- Sois clair et concis : commence par un court résumé, puis présente les points clés sous forme de liste à puces.
- Ne jamais inventer d'informations, de chiffres ou de sources. Si tu ne connais pas une information récente, dis-le clairement.
- Quand c'est pertinent, propose à l'utilisateur de générer une revue de presse sur le sujet abordé."""

# L'agent du chat.
# defer_model_check=True : la clé Mistral n'est vérifiée qu'au moment d'appeler le LLM.
# Utile pour les tests automatiques, qui n'auront pas de vraie clé.
chat_agent = Agent(MODEL_NAME, system_prompt=SYSTEM_PROMPT, defer_model_check=True)