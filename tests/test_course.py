from fastapi.testclient import TestClient
from main import app

BASE_URL = '/api/v1'

client = TestClient(app)

def test_course_crud():
    """Test complete CRUD operations for courses"""
    
    # First create a user and get auth token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "courseuser123",
        "email": "courseuser@test.com",
        "phone": "456",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    # Login to get token
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "courseuser@test.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # First, create a program for the course
    program_data = {
        "type": "BSc",
        "name": "Computer Science",
        "duration": 4,
        "description": "Bachelor of Science in Computer Science"
    }
    
    program_response = client.post(
        f"{BASE_URL}/programs",
        json=program_data,
        headers={"Authorization": token}
    )
    assert program_response.status_code == 201
    program_id = program_response.json()["id"]
    
    # Test create course
    course_data = {
        "name": "Data Structures",
        "program_id": program_id,
        "credits": 3,
        "description": "Introduction to data structures and algorithms"
    }
    
    create_response = client.post(
        f"{BASE_URL}/courses", 
        json=course_data,
        headers={"Authorization": token}
    )
    assert create_response.status_code == 201
    created_course = create_response.json()
    course_id = created_course["id"]
    assert created_course["name"] == "Data Structures"
    assert created_course["program_id"] == program_id
    assert created_course["credits"] == 3
    
    # Test get all courses
    get_all_response = client.get(
        f"{BASE_URL}/courses",
        headers={"Authorization": token}
    )
    assert get_all_response.status_code == 200
    courses = get_all_response.json()
    assert isinstance(courses, list)
    assert len(courses) >= 1
    
    # Test get specific course
    get_one_response = client.get(
        f"{BASE_URL}/courses/{course_id}",
        headers={"Authorization": token}
    )
    assert get_one_response.status_code == 200
    retrieved_course = get_one_response.json()
    assert retrieved_course["id"] == course_id
    assert retrieved_course["name"] == "Data Structures"
    
    # Test update course
    update_data = {
        "name": "Advanced Data Structures",
        "credits": 4,
        "description": "Advanced concepts in data structures"
    }
    update_response = client.put(
        f"{BASE_URL}/courses/{course_id}",
        json=update_data,
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_course = update_response.json()
    assert updated_course["name"] == "Advanced Data Structures"
    assert updated_course["credits"] == 4
    assert updated_course["description"] == "Advanced concepts in data structures"
    
    # Test delete course
    delete_response = client.delete(
        f"{BASE_URL}/courses/{course_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 204
    
    # Verify course is deleted
    get_deleted_response = client.get(
        f"{BASE_URL}/courses/{course_id}",
        headers={"Authorization": token}
    )
    assert get_deleted_response.status_code == 404
    
    # Clean up - delete program and user
    client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    cleanup_response = client.delete(
        f"{BASE_URL}/users/{user_id}",
        headers={"Authorization": token}
    )
    assert cleanup_response.status_code == 204


def test_course_not_found():
    """Test handling of non-existent course"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "notfoundcourse123",
        "email": "notfoundcourse@test.com",
        "phone": "456",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    assert signup_response.status_code == 201
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "notfoundcourse@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Test get non-existent course
    non_existent_id = 99999
    get_response = client.get(
        f"{BASE_URL}/courses/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert get_response.status_code == 404
    assert "Course not found" in get_response.json()["detail"]
    
    # Test update non-existent course
    update_response = client.put(
        f"{BASE_URL}/courses/{non_existent_id}",
        json={"name": "Updated Course"},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 404
    
    # Test delete non-existent course
    delete_response = client.delete(
        f"{BASE_URL}/courses/{non_existent_id}",
        headers={"Authorization": token}
    )
    assert delete_response.status_code == 404
    
    # Clean up
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_course_with_different_credits():
    """Test creating courses with different credit values"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "credituser123",
        "email": "credituser@test.com",
        "phone": "456",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "credituser@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Create a program first
    program_data = {
        "type": "MSc",
        "name": "Data Science",
        "duration": 2,
        "description": "Master of Science in Data Science"
    }
    
    program_response = client.post(
        f"{BASE_URL}/programs",
        json=program_data,
        headers={"Authorization": token}
    )
    program_id = program_response.json()["id"]
    
    credit_values = [1, 2, 3, 4, 6]
    created_courses = []
    
    for credits in credit_values:
        course_data = {
            "name": f"Course with {credits} Credits",
            "program_id": program_id,
            "credits": credits,
            "description": f"A course worth {credits} credits"
        }
        
        response = client.post(
            f"{BASE_URL}/courses",
            json=course_data,
            headers={"Authorization": token}
        )
        assert response.status_code == 201
        course = response.json()
        assert course["credits"] == credits
        created_courses.append(course["id"])
    
    # Clean up courses and program
    for course_id in created_courses:
        client.delete(f"{BASE_URL}/courses/{course_id}", headers={"Authorization": token})
    
    client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    
    # Clean up user
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})


def test_course_unauthorized():
    """Test unauthorized access to course endpoints"""
    
    # Test get courses without auth
    response = client.get(f"{BASE_URL}/courses")
    assert response.status_code == 401
    
    # Test create course without auth
    course_data = {
        "name": "Unauthorized Course",
        "program_id": 1,
        "credits": 3
    }
    
    response = client.post(f"{BASE_URL}/courses", json=course_data)
    assert response.status_code == 401


def test_course_partial_update():
    """Test partial updates to course"""
    
    # Create user and get token
    signup_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "partialuser123",
        "email": "partialuser@test.com",
        "phone": "456",
        "password": "password123",
        "gender": "male",
        "role": "user"
    })
    user_id = signup_response.json().get("id")
    
    login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "partialuser@test.com",
        "password": "password123"
    })
    access_token = login_response.json().get("access_token")
    token = "Bearer " + access_token
    
    # Create a program first
    program_data = {
        "type": "PhD",
        "name": "Computer Science Research",
        "duration": 5
    }
    
    program_response = client.post(
        f"{BASE_URL}/programs",
        json=program_data,
        headers={"Authorization": token}
    )
    program_id = program_response.json()["id"]
    
    # Create course
    course_data = {
        "name": "Research Methods",
        "program_id": program_id,
        "credits": 2,
        "description": "Introduction to research methodology"
    }
    
    create_response = client.post(
        f"{BASE_URL}/courses",
        json=course_data,
        headers={"Authorization": token}
    )
    course_id = create_response.json()["id"]
    
    # Test partial update - only name
    update_response = client.put(
        f"{BASE_URL}/courses/{course_id}",
        json={"name": "Advanced Research Methods"},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_course = update_response.json()
    assert updated_course["name"] == "Advanced Research Methods"
    assert updated_course["credits"] == 2  # Should remain unchanged
    
    # Test partial update - only credits
    update_response = client.put(
        f"{BASE_URL}/courses/{course_id}",
        json={"credits": 4},
        headers={"Authorization": token}
    )
    assert update_response.status_code == 200
    updated_course = update_response.json()
    assert updated_course["credits"] == 4
    assert updated_course["name"] == "Advanced Research Methods"  # Should remain unchanged
    
    # Clean up
    client.delete(f"{BASE_URL}/courses/{course_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/programs/{program_id}", headers={"Authorization": token})
    client.delete(f"{BASE_URL}/users/{user_id}", headers={"Authorization": token})
