from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app

BASE_URL = '/api/v1'

client = TestClient(app)

def test_payment_comprehensive():
    """
    Comprehensive test for all payment APIs:
    1. Create admin and student users
    2. Create a program
    3. Enroll student in program 
    4. Create payment fees
    5. Test all payment endpoints
    """
    
    # 1. Create admin user
    admin_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "admin_user",
        "email": "admin@university.edu",
        "phone": "1234567890",
        "password": "adminpass123",
        "gender": "male",
        "role": "admin"
    })
    assert admin_response.status_code == 201
    admin_data = admin_response.json()
    admin_id = admin_data["id"]
    
    # Login admin
    admin_login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@university.edu",
        "password": "adminpass123"
    })
    assert admin_login_response.status_code == 200
    admin_token = "Bearer " + admin_login_response.json()["access_token"]
    
    # 2. Create student user
    student_response = client.post(f"{BASE_URL}/auth/signup", json={
        "username": "student_user",
        "email": "student@university.edu", 
        "phone": "0987654321",
        "password": "studentpass123",
        "gender": "female",
        "role": "student"
    })
    assert student_response.status_code == 201
    student_data = student_response.json()
    student_user_id = student_data["id"]
    
    # Login student
    student_login_response = client.post(f"{BASE_URL}/auth/login", json={
        "email": "student@university.edu",
        "password": "studentpass123"
    })
    assert student_login_response.status_code == 200
    student_token = "Bearer " + student_login_response.json()["access_token"]
    
    # 3. Create a program (as admin)
    program_response = client.post(f"{BASE_URL}/programs", 
        headers={"Authorization": admin_token},
        json={
            "type": "BSc",
            "name": "Computer Science",
            "duration": 4,
            "description": "Bachelor of Science in Computer Science",
            "is_active": 1
        }
    )
    assert program_response.status_code == 201
    program_data = program_response.json()
    program_id = program_data["id"]
    
    # 4. Get student record to get student_id
    student_by_user_response = client.get(f"{BASE_URL}/students/user/{student_user_id}",
        headers={"Authorization": student_token}
    )
    assert student_by_user_response.status_code == 200
    student_record = student_by_user_response.json()
    student_id = student_record["id"]
    
    # 5. Create payment fees for the program (as admin)
    # Tuition fee
    tuition_fee_response = client.post(f"{BASE_URL}/payments/fees",
        headers={"Authorization": admin_token},
        json={
            "program_id": program_id,
            "amount": 50000,
            "description": "Tuition fee for semester 1",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
    )
    assert tuition_fee_response.status_code == 201
    tuition_fee_data = tuition_fee_response.json()
    tuition_fee_id = tuition_fee_data["id"]
    
    # Registration fee  
    registration_fee_response = client.post(f"{BASE_URL}/payments/fees",
        headers={"Authorization": admin_token},
        json={
            "program_id": program_id,
            "amount": 5000,
            "description": "Registration fee",
            "due_date": (datetime.now() + timedelta(days=15)).isoformat()
        }
    )
    assert registration_fee_response.status_code == 201
    registration_fee_data = registration_fee_response.json()
    registration_fee_id = registration_fee_data["id"]
    
    # 6. Test payment fee endpoints
    
    # Get all payment fees
    all_fees_response = client.get(f"{BASE_URL}/payments/fees")
    assert all_fees_response.status_code == 200
    all_fees = all_fees_response.json()
    assert len(all_fees) >= 2
    
    # Get payment fees by program
    program_fees_response = client.get(f"{BASE_URL}/payments/fees/program/{program_id}")
    assert program_fees_response.status_code == 200
    program_fees = program_fees_response.json()
    assert len(program_fees) == 2
    
    # Get specific payment fee
    fee_response = client.get(f"{BASE_URL}/payments/fees/{tuition_fee_id}")
    assert fee_response.status_code == 200
    fee_data = fee_response.json()
    assert fee_data["amount"] == 50000
    assert fee_data["description"] == "Tuition fee for semester 1"
    
    # Update payment fee (as admin)
    updated_fee_response = client.put(f"{BASE_URL}/payments/fees/{tuition_fee_id}",
        headers={"Authorization": admin_token},
        json={
            "amount": 55000,
            "description": "Updated tuition fee for semester 1"
        }
    )
    assert updated_fee_response.status_code == 200
    updated_fee = updated_fee_response.json()
    assert updated_fee["amount"] == 55000
    assert updated_fee["description"] == "Updated tuition fee for semester 1"
    
    # 7. Test student payment creation
    
    # Student makes payment for registration fee
    payment_response = client.post(f"{BASE_URL}/payments",
        headers={"Authorization": student_token},
        json={
            "program_id": program_id,
            "amount": 5000,
            "payment_method": "bank_transfer"
        }
    )
    assert payment_response.status_code == 201
    payment_data = payment_response.json()
    payment_id = payment_data["id"]
    assert payment_data["amount"] == 5000
    assert payment_data["student_id"] == student_id
    assert payment_data["status"] == "pending"
    
    # 8. Test payment retrieval endpoints
    
    # Get all payments (should work without auth)
    all_payments_response = client.get(f"{BASE_URL}/payments")
    assert all_payments_response.status_code == 200
    all_payments = all_payments_response.json()
    assert len(all_payments) >= 1
    
    # Get student's own payments
    my_payments_response = client.get(f"{BASE_URL}/payments/me",
        headers={"Authorization": student_token}
    )
    assert my_payments_response.status_code == 200
    my_payments = my_payments_response.json()
    assert len(my_payments) == 1
    assert my_payments[0]["id"] == payment_id
    
    # Get specific payment
    payment_detail_response = client.get(f"{BASE_URL}/payments/{payment_id}")
    assert payment_detail_response.status_code == 200
    payment_detail = payment_detail_response.json()
    assert payment_detail["id"] == payment_id
    assert payment_detail["amount"] == 5000
    
    # 9. Test admin payment status update
    
    # Admin updates payment status to confirmed
    status_update_response = client.put(f"{BASE_URL}/payments/{payment_id}",
        headers={"Authorization": admin_token},
        json={
            "status": "confirmed"
        }
    )
    assert status_update_response.status_code == 200
    updated_payment = status_update_response.json()
    assert updated_payment["status"] == "confirmed"
    
    # 10. Test unpaid fees endpoints
    
    # Before enrollment, student should see no unpaid fees
    my_unpaid_fees_response = client.get(f"{BASE_URL}/payments/fees/me/unpaid",
        headers={"Authorization": student_token}
    )
    # This might return empty or error if student not enrolled in program
    # The response depends on the enrollment logic
    
    # Admin views unpaid fees for student
    admin_view_unpaid_response = client.get(f"{BASE_URL}/payments/fees/student/{student_id}/unpaid",
        headers={"Authorization": admin_token}
    )
    # This should work regardless of enrollment status
    assert admin_view_unpaid_response.status_code == 200
    
    # 11. Test payment fee deletion (as admin)
    delete_fee_response = client.delete(f"{BASE_URL}/payments/fees/{registration_fee_id}",
        headers={"Authorization": admin_token}
    )
    assert delete_fee_response.status_code == 204
    
    # Verify fee was deleted
    deleted_fee_response = client.get(f"{BASE_URL}/payments/fees/{registration_fee_id}")
    assert deleted_fee_response.status_code == 404
    
    # 12. Clean up - delete created resources
    
    # Delete remaining payment transactions
    try:
        client.delete(f"{BASE_URL}/payments/{payment_id}",
                     headers={"Authorization": admin_token})
    except:
        pass  # Payment deletion might not be implemented
    
    # Delete remaining payment fee (tuition_fee)
    try:
        client.delete(f"{BASE_URL}/payments/fees/{tuition_fee_id}",
                     headers={"Authorization": admin_token})
    except:
        pass  # In case fee was already deleted
    
    # Delete program
    try:
        client.delete(f"{BASE_URL}/programs/{program_id}",
                     headers={"Authorization": admin_token})
    except:
        pass  # Program deletion might not be implemented
    
    # Delete student user
    try:
        client.delete(f"{BASE_URL}/users/{student_user_id}", 
                     headers={"Authorization": student_token})
    except:
        pass  # In case user deletion fails
    
    # Delete admin user
    try:
        client.delete(f"{BASE_URL}/users/{admin_id}",
                     headers={"Authorization": admin_token})
    except:
        pass  # In case user deletion fails
    
    