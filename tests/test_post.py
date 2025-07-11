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
        "role": "user"
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
        "role": "user"
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
        "role": "user"
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
