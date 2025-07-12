from fastapi.testclient import TestClient
from main import app
from datetime import date
import json

BASE_URL = '/api/v1'

client = TestClient(app)

def test_post_crud():
    """Test complete CRUD operations for posts"""
    
    # First create a user and get auth token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "postuser123",
        "email": "postuser@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "admin"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    # Login to get token
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "postuser@test.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Test create post
    post_data = {
        "type": "notice",
        "title": "Test Notice",
        "content": "This is a test notice content",
        "date": str(date.today())
    }
    
    create_response = client.post(
        f"{BASE_URL}/posts", 
        json=post_data,
        headers={"Authorization": token}
    )
    assert create_response.status_code == 201
    created_post = create_response.json()
    post_id = created_post["id"]
    assert created_post["title"] == "Test Notice"
    assert created_post["type"] == "notice"
    assert created_post["content"] == "This is a test notice content"
    
    # Test get all posts (no auth required)
    get_all_response = client.get(f"{BASE_URL}/posts")
    assert get_all_response.status_code == 200
    posts = get_all_response.json()
    assert isinstance(posts, list)
    assert len(posts) >= 1
    
    # Test get specific post
    get_one_response = client.get(
        f"{BASE_URL}/posts/{post_id}",
        headers={"Authorization": token}
    )
    assert get_one_response.status_code == 200
    retrieved_post = get_one_response.json()
    assert retrieved_post["id"] == post_id
    assert retrieved_post["title"] == "Test Notice"
    
    # Test update post
    update_data = {
        "title": "Updated Test Notice",
        "content": "Updated content"
    }
    update_response = client.put(
        f"{BASE_URL}/posts/{post_id}",
        json=update_data,
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_post = update_response.json()
    assert updated_post["title"] == "Updated Test Notice"
    assert updated_post["content"] == "Updated content"
    
    # Test delete post
    delete_response = client.delete(
        f"{BASE_URL}/posts/{post_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 204
    
    # Verify post is deleted
    get_deleted_response = client.get(
        f"{BASE_URL}/posts/{post_id}",
        headers={"Authorization": token}
    )
    assert get_deleted_response.status_code == 404
    
    # Clean up - delete user
    cleanup_response = client.delete(
        f"{BASE_URL}/users/{user_id}",
        headers={"Authorization": token}
    )
    assert cleanup_response.status_code == 204


def test_post_not_found():
    """Test handling of non-existent post"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "notfounduser123",
        "email": "notfound@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "admin"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "notfound@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Test get non-existent post
    non_existent_id = 99999
    get_response = client.get(
        f"{BASE_URL}/posts/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert get_response.status_code == 404
    assert "Post not found" in get_response.json()["detail"]
    
    # Test update non-existent post
    update_response = client.put(
        f"{BASE_URL}/posts/{non_existent_id}",
        json={"title": "Updated"},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 404
    
    # Test delete non-existent post
    delete_response = client.delete(
        f"{BASE_URL}/posts/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 404
    
    # Clean up
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_post_different_types():
    """Test creating posts with different types"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "typeuser123",
        "email": "typeuser@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "admin"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "typeuser@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    post_types = ["notice", "announcement", "event"]
    created_posts = []
    
    for post_type in post_types:
        post_data = {
            "type": post_type,
            "title": f"Test {post_type.capitalize()}",
            "content": f"This is a test {post_type} content",
            "date": str(date.today())
        }
        
        response = client.post(
            f"{BASE_URL}/posts",
            json=post_data,
            headers={"Authorization": token}
        )
        assert response.status_code == 201
        post = response.json()
        assert post["type"] == post_type
        created_posts.append(post["id"])
    
    # Clean up posts
    for post_id in created_posts:
        client.delete(f"{BASE_URL}/posts/{post_id}", headers={"Authorization": token})
    
    # Clean up user
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_post_unauthorized():
    """Test unauthorized access to protected endpoints"""
    
    # Test create post without auth
    post_data = {
        "type": "notice",
        "title": "Unauthorized Test",
        "content": "This should fail",
        "date": str(date.today())
    }
    
    response = client.post(f"{BASE_URL}/posts", json=post_data)
    assert response.status_code == 401


def test_post_participant_management():
    """Test complete participant management for posts"""
    
    # Create first user (post creator)
    signup_response1 = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "postcreator123",
        "email": "postcreator@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "admin"
    })
    assert signup_response1.status_code == 201
    creator_id = signup_response1.json().get("id")
    
    # Login creator
    login_response1 = client.post(f"{BASE_URL}/auth/login", json={
        "email": "postcreator@test.com",
        "password": "password123"
    })
    assert login_response1.status_code == 200
    creator_token = "Bearer " + login_response1.json().get("access_token")
    
    # Create second user (participant)
    signup_response2 = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "participant123",
        "email": "participant@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "female",
        "role": "user"
    })
    assert signup_response2.status_code == 201
    participant_id = signup_response2.json().get("id")
    
    # Login participant
    login_response2 = client.post(f"{BASE_URL}/auth/login", json={
        "email": "participant@test.com",
        "password": "password123"
    })
    assert login_response2.status_code == 200
    participant_token = "Bearer " + login_response2.json().get("access_token")
    
    # Create third user (another participant)
    signup_response3 = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "participant2_123",
        "email": "participant2@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    assert signup_response3.status_code == 201
    participant2_id = signup_response3.json().get("id")
    
    # Create a post
    post_data = {
        "type": "event",
        "title": "Test Event with Participants",
        "content": "This is a test event for participant management",
        "date": str(date.today())
    }
    
    create_response = client.post(
        f"{BASE_URL}/posts", 
        json=post_data,
        headers={"Authorization": creator_token}
    )
    assert create_response.status_code == 201
    post_id = create_response.json()["id"]
    
    # Test initial participants list (should be empty)
    participants_response = client.get(
        f"{BASE_URL}/posts/{post_id}/participants",
        headers={"Authorization": creator_token}
    )
    assert participants_response.status_code == 200
    participants_data = participants_response.json()
    assert participants_data["participants_count"] == 0
    assert len(participants_data["participants"]) == 0
    
    # Test add first participant
    add_participant_response = client.post(
        f"{BASE_URL}/posts/{post_id}/participants/{participant_id}",
        headers={"Authorization": creator_token}
    )
    assert add_participant_response.status_code == 200
    assert "successfully added as participant" in add_participant_response.json()["message"]
    
    # Test add second participant
    add_participant2_response = client.post(
        f"{BASE_URL}/posts/{post_id}/participants/{participant2_id}",
        headers={"Authorization": creator_token}
    )
    assert add_participant2_response.status_code == 200
    
    # Test participants list after adding participants
    participants_response = client.get(
        f"{BASE_URL}/posts/{post_id}/participants",
        headers={"Authorization": creator_token}
    )
    assert participants_response.status_code == 200
    participants_data = participants_response.json()
    assert participants_data["participants_count"] == 2
    assert len(participants_data["participants"]) == 2
    
    # Check participant details
    participant_ids = [p["id"] for p in participants_data["participants"]]
    assert participant_id in participant_ids
    assert participant2_id in participant_ids
    
    # Test add duplicate participant (should fail)
    duplicate_response = client.post(
        f"{BASE_URL}/posts/{post_id}/participants/{participant_id}",
        headers={"Authorization": creator_token}
    )
    assert duplicate_response.status_code == 409
    assert "already a participant" in duplicate_response.json()["detail"]
    
    # Test remove participant
    remove_response = client.delete(
        f"{BASE_URL}/posts/{post_id}/participants/{participant_id}",
        headers={"Authorization": creator_token}
    )
    assert remove_response.status_code == 200
    assert "successfully removed from post" in remove_response.json()["message"]
    
    # Test participants list after removal
    participants_response = client.get(
        f"{BASE_URL}/posts/{post_id}/participants",
        headers={"Authorization": creator_token}
    )
    assert participants_response.status_code == 200
    participants_data = participants_response.json()
    assert participants_data["participants_count"] == 1
    assert len(participants_data["participants"]) == 1
    assert participants_data["participants"][0]["id"] == participant2_id
    
    # Test remove non-participant (should fail)
    remove_non_participant_response = client.delete(
        f"{BASE_URL}/posts/{post_id}/participants/{participant_id}",
        headers={"Authorization": creator_token}
    )
    assert remove_non_participant_response.status_code == 404
    assert "not a participant" in remove_non_participant_response.json()["detail"]
    
    # Clean up - remove remaining participant
    client.delete(
        f"{BASE_URL}/posts/{post_id}/participants/{participant2_id}",
        headers={"Authorization": creator_token}
    )
    
    # Clean up - delete post
    client.delete(
        f"{BASE_URL}/posts/{post_id}",
        headers={"Authorization": creator_token}
    )
    
    # Clean up - delete users
    client.delete(f"{BASE_URL}/users/{creator_id}", headers={"Authorization": creator_token})
    client.delete(f"{BASE_URL}/users/{participant_id}", headers={"Authorization": participant_token})
    client.delete(f"{BASE_URL}/users/{participant2_id}", headers={"Authorization": creator_token})


def test_post_participant_not_found_scenarios():
    """Test participant management with non-existent posts and users"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "notfoundtest123",
        "email": "notfoundtest@test.com",
        "phone": "345",
        "password": "password123",
        "gender": "male",
        "role": "admin"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "notfoundtest@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Create a post for testing
    post_data = {
        "type": "notice",
        "title": "Test Post for Not Found",
        "content": "Testing not found scenarios",
        "date": str(date.today())
    }
    
    create_response = client.post(
        f"{BASE_URL}/posts", 
        json=post_data,
        headers={"Authorization": token}
    )
    post_id = create_response.json()["id"]
    
    non_existent_post_id = 99999
    non_existent_user_id = 99999
    
    # Test add participant to non-existent post
    add_to_non_post_response = client.post(
        f"{BASE_URL}/posts/{non_existent_post_id}/participants/{user_id}",
        headers={"Authorization": token}
    )
    assert add_to_non_post_response.status_code == 404
    assert "Post not found" in add_to_non_post_response.json()["detail"]
    
    # Test add non-existent user to post
    add_non_user_response = client.post(
        f"{BASE_URL}/posts/{post_id}/participants/{non_existent_user_id}",
        headers={"Authorization": token}
    )
    assert add_non_user_response.status_code == 404
    assert "User not found" in add_non_user_response.json()["detail"]
    
    # Test remove participant from non-existent post
    remove_from_non_post_response = client.delete(
        f"{BASE_URL}/posts/{non_existent_post_id}/participants/{user_id}",
        headers={"Authorization": token}
    )
    assert remove_from_non_post_response.status_code == 404
    assert "Post not found" in remove_from_non_post_response.json()["detail"]
    
    # Test remove non-existent user from post
    remove_non_user_response = client.delete(
        f"{BASE_URL}/posts/{post_id}/participants/{non_existent_user_id}",
        headers={"Authorization": token}
    )
    assert remove_non_user_response.status_code == 404
    assert "User not found" in remove_non_user_response.json()["detail"]
    
    # Test get participants of non-existent post
    get_participants_non_post_response = client.get(
        f"{BASE_URL}/posts/{non_existent_post_id}/participants",
        headers={"Authorization": token}
    )
    assert get_participants_non_post_response.status_code == 404
    assert "Post not found" in get_participants_non_post_response.json()["detail"]
    
    # Clean up
    client.delete(f"{BASE_URL}/posts/{post_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_post_participant_unauthorized():
    """Test unauthorized access to participant management endpoints"""
    
    # Test add participant without auth
    add_response = client.post(f"{BASE_URL}/posts/1/participants/1")
    assert add_response.status_code == 401
    
    # Test remove participant without auth
    remove_response = client.delete(f"{BASE_URL}/posts/1/participants/1")
    assert remove_response.status_code == 401
    
    # Test get participants without auth
    get_response = client.get(f"{BASE_URL}/posts/1/participants")
    assert get_response.status_code == 401
