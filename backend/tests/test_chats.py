from pydantic_ai.models.test import TestModel  # le faux LLM de PydanticAI

from agent import chat_agent  # notre agent, qu'on va remplacer par le faux LLM


# Test 3 : sans badge, on ne peut pas créer de discussion
def test_creer_discussion_sans_badge(client):
    response = client.post("/chats")
    assert response.status_code == 401


# Test 4 : Alice crée une discussion, puis la relit
def test_creer_puis_lire_discussion(client, alice_headers):
    response = client.post("/chats", headers=alice_headers)
    assert response.status_code == 201
    chat_id = response.json()["id"]

    response = client.get(f"/chats/{chat_id}", headers=alice_headers)
    assert response.status_code == 200
    assert response.json()["messages"] == []  # pas encore de message


# Test 5 : Alice envoie un message, et le faux LLM répond
def test_envoyer_message(client, alice_headers):
    chat_id = client.post("/chats", headers=alice_headers).json()["id"]

    # On remplace Mistral par le faux LLM, qui répond toujours "Réponse de test"
    with chat_agent.override(model=TestModel(custom_output_text="Réponse de test")):
        response = client.post(
            f"/chats/{chat_id}/messages", headers=alice_headers, json={"content": "Bonjour"}
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Réponse de test"

    # L'historique contient bien 2 messages : la question et la réponse
    chat = client.get(f"/chats/{chat_id}", headers=alice_headers).json()
    assert len(chat["messages"]) == 2


# Test 6 🔒 : Bob ne peut pas lire la discussion d'Alice
def test_bob_ne_peut_pas_lire_discussion_alice(client, alice_headers, bob_headers):
    chat_id = client.post("/chats", headers=alice_headers).json()["id"]

    response = client.get(f"/chats/{chat_id}", headers=bob_headers)
    assert response.status_code == 404


# Test 7 🔒 : Bob ne peut pas écrire dans la discussion d'Alice
def test_bob_ne_peut_pas_ecrire_discussion_alice(client, alice_headers, bob_headers):
    chat_id = client.post("/chats", headers=alice_headers).json()["id"]

    with chat_agent.override(model=TestModel()):
        response = client.post(
            f"/chats/{chat_id}/messages", headers=bob_headers, json={"content": "Coucou"}
        )
    assert response.status_code == 404


# Test 8 🔒 : la liste de Bob ne contient pas les discussions d'Alice
def test_liste_bob_sans_discussions_alice(client, alice_headers, bob_headers):
    client.post("/chats", headers=alice_headers)  # Alice crée une discussion

    response = client.get("/chats", headers=bob_headers)
    assert response.json() == []  # la liste de Bob est vide