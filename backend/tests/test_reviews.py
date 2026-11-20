# --- Les tests de la revue de presse (étape 7) ---
from pydantic_ai.models.test import TestModel

from agent import chat_agent
from review_agent import review_agent


# Petite aide : Alice crée une discussion et envoie un message (avec le faux LLM)
def create_chat_with_message(client, headers):
    chat_id = client.post("/chats", headers=headers).json()["id"]
    with chat_agent.override(model=TestModel(custom_output_text="Réponse de test", call_tools=[])):
        client.post(
            f"/chats/{chat_id}/messages",
            headers=headers,
            json={"content": "Parle-moi des passoires thermiques"},
        )
    return chat_id


# Test 11 : générer une revue, puis la retrouver dans la liste
def test_generer_et_lister_revue(client, alice_headers):
    chat_id = create_chat_with_message(client, alice_headers)

    with review_agent.override(model=TestModel()):
        response = client.post(
            f"/chats/{chat_id}/review", headers=alice_headers, json={"topic": "passoires thermiques"}
        )
    assert response.status_code == 200

    reviews = client.get("/reviews", headers=alice_headers).json()
    assert len(reviews) == 1
    assert reviews[0]["chat_id"] == chat_id


# Test 12 🔒 : Bob ne peut pas générer ni voir la revue d'Alice
def test_bob_ne_peut_pas_voir_revue_alice(client, alice_headers, bob_headers):
    chat_id = create_chat_with_message(client, alice_headers)

    with review_agent.override(model=TestModel()):
        response = client.post(f"/chats/{chat_id}/review", headers=bob_headers, json={"topic": "test"})
        assert response.status_code == 404
        client.post(f"/chats/{chat_id}/review", headers=alice_headers, json={"topic": "test"})

    assert client.get("/reviews", headers=bob_headers).json() == []


# Test 13 : une discussion vide → pas de revue possible (400)
def test_revue_discussion_vide(client, alice_headers):
    chat_id = client.post("/chats", headers=alice_headers).json()["id"]

    response = client.post(f"/chats/{chat_id}/review", headers=alice_headers, json={"topic": "test"})
    assert response.status_code == 400