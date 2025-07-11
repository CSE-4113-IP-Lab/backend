from fastapi.testclient import TestClient
from main import app
import time

BASE_URL = '/api/v1'

client = TestClient(app)

def test_program_crud():
    """Test complete CRUD operations for programs"""
    
    # First create a user and get auth token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "programuser123",
        "email": "programuser@test.com",
        "phone": "1234567890",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    # Login to get token
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "programuser@test.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Test create program
    timestamp = int(time.time())
    program_data = {
        "type": "BSc",
        "name": f"Computer Science {timestamp}",
        "duration": 4,
        "description": "Bachelor of Science in Computer Science",
        "is_active": 1
    }
    
    create_response = client.post(
        f"{BASE_URL}/programs", 
        json=program_data,
        headers={"Authorization": token}
    )
    assert create_response.status_code == 201
    created_program = create_response.json()
    program_id = created_program["id"]
    assert created_program["name"] == f"Computer Science {timestamp}"
    assert created_program["type"] == "BSc"
    assert created_program["duration"] == 4
    assert created_program["description"] == "Bachelor of Science in Computer Science"
    
    # Test get all programs
    get_all_response = client.get(
        f"{BASE_URL}/programs",
        headers={"Authorization": token}
    )
    assert get_all_response.status_code == 200
    programs = get_all_response.json()
    assert isinstance(programs, list)
    assert len(programs) >= 1
    
    # Test get specific program
    get_one_response = client.get(
        f"{BASE_URL}/programs/{program_id}",
        headers={"Authorization": token}
    )
    assert get_one_response.status_code == 200
    retrieved_program = get_one_response.json()
    assert retrieved_program["id"] == program_id
    assert retrieved_program["name"] == f"Computer Science {timestamp}"
    
    # Test update program
    update_data = {
        "name": "Advanced Computer Science",
        "duration": 5,
        "description": "Advanced Bachelor of Science in Computer Science"
    }
    update_response = client.put(
        f"{BASE_URL}/programs/{program_id}",
        json=update_data,
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_program = update_response.json()
    assert updated_program["name"] == "Advanced Computer Science"
    assert updated_program["duration"] == 5
    assert updated_program["description"] == "Advanced Bachelor of Science in Computer Science"
    
    # Test delete program
    delete_response = client.delete(
        f"{BASE_URL}/programs/{program_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 204
    
    # Verify program is deleted
    get_deleted_response = client.get(
        f"{BASE_URL}/programs/{program_id}",
        headers={"Authorization": token}
    )
    assert get_deleted_response.status_code == 404
    
    # Clean up - delete user
    cleanup_response = client.delete(
        f"{BASE_URL}/users/{user_id}",
        headers={"Authorization": token}
    )
    assert cleanup_response.status_code == 204


def test_program_not_found():
    """Test handling of non-existent program"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "notfoundprogram123",
        "email": "notfoundprogram@test.com",
        "phone": "1234567890",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "notfoundprogram@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Test get non-existent program
    non_existent_id = 99999
    get_response = client.get(
        f"{BASE_URL}/programs/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert get_response.status_code == 404
    assert "Program not found" in get_response.json()["detail"]
    
    # Test update non-existent program
    update_response = client.put(
        f"{BASE_URL}/programs/{non_existent_id}",
        json={"name": "Updated Program"},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 404
    
    # Test delete non-existent program
    delete_response = client.delete(
        f"{BASE_URL}/programs/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 404
    
    # Clean up
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_program_different_types():
    """Test creating programs with different types"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "typeprogram123",
        "email": "typeprogram@test.com",
        "phone": "1234567890",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "typeprogram@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    program_types = [
        ("BSc", "Bachelor of Science", 4),
        ("MSc", "Master of Science", 2),
        ("PhD", "Doctor of Philosophy", 5),
        ("Postdoc", "Postdoctoral Research", 2)
    ]
    created_programs = []
    timestamp = int(time.time())
    
    for program_type, name, duration in program_types:
        program_data = {
            "type": program_type,
            "name": f"{name} in Computer Science {timestamp}",
            "duration": duration,
            "description": f"{name} program in Computer Science"
        }
        
        response = client.post(
            f"{BASE_URL}/programs",
            json=program_data,
            headers={"Authorization": token}
        )
        assert response.status_code == 201
        program = response.json()
        assert program["type"] == program_type
        assert program["duration"] == duration
        created_programs.append(program["id"])
    
    # Clean up programs
    for program_id in created_programs:
        client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    
    # Clean up user
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_program_unauthorized():
    """Test unauthorized access to program endpoints"""
    
    # Test get programs without auth
    response = client.get(f"{BASE_URL}/programs")
    assert response.status_code == 401
    
    # Test create program without auth
    program_data = {
        "type": "BSc",
        "name": "Unauthorized Program",
        "duration": 4
    }
    
    response = client.post(f"{BASE_URL}/programs", json=program_data)
    assert response.status_code == 401


def test_program_partial_update():
    """Test partial updates to program"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "partialprogram123",
        "email": "partialprogram@test.com",
        "phone": "1234567891",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "partialprogram@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Create program
    timestamp = int(time.time())
    program_data = {
        "type": "MSc",
        "name": f"Data Science {timestamp}",
        "duration": 2,
        "description": "Master of Science in Data Science"
    }
    
    create_response = client.post(
        f"{BASE_URL}/programs",
        json=program_data,
        headers={"Authorization": token}
    )
    program_id = create_response.json()["id"]
    
    # Test partial update - only name
    update_response = client.put(
        f"{BASE_URL}/programs/{program_id}",
        json={"name": "Advanced Data Science"},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_program = update_response.json()
    assert updated_program["name"] == "Advanced Data Science"
    assert updated_program["duration"] == 2  # Should remain unchanged
    
    # Test partial update - only duration
    update_response = client.put(
        f"{BASE_URL}/programs/{program_id}",
        json={"duration": 3},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_program = update_response.json()
    assert updated_program["duration"] == 3
    assert updated_program["name"] == "Advanced Data Science"  # Should remain unchanged
    
    # Test partial update - deactivate program
    update_response = client.put(
        f"{BASE_URL}/programs/{program_id}",
        json={"is_active": 0},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_program = update_response.json()
    assert updated_program["is_active"] == 0
    
    # Clean up
    client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_program_active_inactive():
    """Test creating and managing active/inactive programs"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "activeprogram123",
        "email": "activeprogram@test.com",
        "phone": "1234567892",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "activeprogram@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Create active program
    timestamp = int(time.time())
    active_program_data = {
        "type": "BSc",
        "name": f"Active Program {timestamp}",
        "duration": 4,
        "is_active": 1
    }
    
    active_response = client.post(
        f"{BASE_URL}/programs",
        json=active_program_data,
        headers={"Authorization": token}
    )
    assert active_response.status_code == 201
    active_program = active_response.json()
    assert active_program["is_active"] == 1
    active_program_id = active_program["id"]
    
    # Create inactive program
    inactive_program_data = {
        "type": "MSc",
        "name": f"Inactive Program {timestamp}",
        "duration": 2,
        "is_active": 0
    }
    
    inactive_response = client.post(
        f"{BASE_URL}/programs",
        json=inactive_program_data,
        headers={"Authorization": token}
    )
    assert inactive_response.status_code == 201
    inactive_program = inactive_response.json()
    assert inactive_program["is_active"] == 0
    inactive_program_id = inactive_program["id"]
    
    # Clean up
    client.delete(f"{BASE_URL}/programs/{active_program_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/programs/{inactive_program_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_program_duration_validation():
    """Test programs with different duration values"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "durationprogram123",
        "email": "durationprogram@test.com",
        "phone": "1234567893",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "durationprogram@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    durations = [1, 2, 3, 4, 5, 6]
    created_programs = []
    timestamp = int(time.time())
    
    for duration in durations:
        program_data = {
            "type": "BSc",
            "name": f"Program {duration} Years {timestamp}",
            "duration": duration,
            "description": f"A {duration}-year program"
        }
        
        response = client.post(
            f"{BASE_URL}/programs",
            json=program_data,
            headers={"Authorization": token}
        )
        assert response.status_code == 201
        program = response.json()
        assert program["duration"] == duration
        created_programs.append(program["id"])
    
    # Clean up
    for program_id in created_programs:
        client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})
