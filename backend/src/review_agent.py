# --- L'agent revue de presse (étape 7) ---
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter, SystemPromptPart, TextPart, ToolReturnPart, UserPromptPart

from agent import MODEL_NAME  # le même LLM que le chat : Mistral Small
from schemas import PressReview  # le formulaire à remplir

# 1. Les instructions de l'agent
REVIEW_INSTRUCTIONS = """Tu es un rédacteur de revues de presse pour des journalistes pigistes.

On te donne une discussion entre un utilisateur et un assistant, et un sujet.
Ta tâche : rédiger une revue de presse sur ce sujet, à partir de cette discussion.

Règles :
- Écris en français, avec un ton professionnel, neutre et factuel.
- Utilise UNIQUEMENT les informations et les articles présents dans la discussion.
- N'invente jamais d'article, de source, de date, de lien ou de chiffre.
- Si une date ou un lien n'apparaît pas dans la discussion, laisse la case vide.
- Si la discussion ne contient aucun article sur ce sujet, laisse la liste d'articles vide
  et explique-le dans la synthèse."""

# 2. L'agent
# output_type=PressReview : l'IA DOIT répondre en remplissant le formulaire PressReview
review_agent = Agent(
    MODEL_NAME,
    output_type=PressReview,
    instructions=REVIEW_INSTRUCTIONS,
    defer_model_check=True,
)

# 3. Transformer l'historique du chat en texte simple, pour l'agent revue de presse
def history_to_text(raw_messages: list) -> str:
    messages = ModelMessagesTypeAdapter.validate_python(raw_messages)
    lines = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, SystemPromptPart):
                lines.append(f"[Actualités du jour données à l'assistant]\n{part.content}")
            elif isinstance(part, UserPromptPart):
                lines.append(f"Utilisateur : {part.content}")
            elif isinstance(part, TextPart):
                lines.append(f"Assistant : {part.content}")
            elif isinstance(part, ToolReturnPart):
                lines.append(f"[Articles trouvés par la recherche]\n{part.model_response_str()}")
    return "\n\n".join(lines)