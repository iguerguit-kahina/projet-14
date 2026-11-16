# Test 1 : avec le bon mot de passe, le login renvoie un badge
def test_login_bon_mot_de_passe(client, alice):
    response = client.post(
        "/login", json={"email": "alice@test.com", "password": "motdepasse-alice"}
    )
    assert response.status_code == 200  # on vérifie : code 200
    assert "access_token" in response.json()  # on vérifie : il y a bien un badge


# Test 2 : avec un mauvais mot de passe, le login est refusé
def test_login_mauvais_mot_de_passe(client, alice):
    response = client.post(
        "/login", json={"email": "alice@test.com", "password": "mauvais"}
    )
    assert response.status_code == 401  # on vérifie : code 401