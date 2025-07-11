from fastapi.testclient import TestClient
from main import app

BASE_URL = '/api/v1'

client = TestClient(app)

def test_signup_and_login():
    # Test signup
    response = client.post(f"{BASE_URL}/auth/signup", json={
                    "username": "testuser123",
                    "email": "test@gmail.com",
                    "phone": "1234567890",
                    "password": "password123",
                    "gender": "male",
                    "role": "user"
                    })
    assert response.status_code == 201

    user_id = response.json().get("id")

    response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "test@gmail.com",
        "password": "password123"
    })

    access_token = response.json().get("access_token")

    token = "Bearer " + access_token

    assert response.status_code == 200

    response = client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})

    assert response.status_code == 204






