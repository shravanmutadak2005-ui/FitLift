"""
Automated tests for User Authentication, Sign In / Sign Up, and Per-User Data Isolation in FitLift.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import app
import database

def run_auth_tests():
    print("========================================")
    print("Testing FitLift Authentication & Data Isolation")
    print("========================================")

    # 1. Test database user registration & authentication
    print("\n[1] Testing Registration & Password Verification...")
    test_username = "testathlete_unique_1"
    new_user, err = database.register_user(
        name="Athlete One",
        username=test_username,
        password="securepassword123",
        email=f"{test_username}@example.com"
    )
    if err and "already taken" in err:
        # Re-fetch user if already created in earlier test run
        conn = database.get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (test_username,)).fetchone()
        conn.close()
        new_user = dict(row)
        print("  -> User already exists, reused for test.")
    else:
        assert new_user is not None
        assert new_user["username"] == test_username
        print("  -> Successfully registered new user:", new_user["username"])

    # Test authentication with valid password
    auth_ok = database.authenticate_user(test_username, "securepassword123")
    assert auth_ok is not None
    assert auth_ok["id"] == new_user["id"]
    print("  -> Valid credentials authentication PASSED.")

    # Test authentication with wrong password
    auth_bad = database.authenticate_user(test_username, "wrongpassword999")
    assert auth_bad is None
    print("  -> Invalid credentials rejection PASSED.")

    # 2. Test Flask Test Client & Unauthenticated Redirection
    print("\n[2] Testing Entry Point & Route Protection...")
    client = app.app.test_client()

    # Accessing root '/' unauthenticated should redirect to '/login'
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
    print("  -> Unauthenticated GET / redirects to /login [PASSED]")

    # Accessing protected pages unauthenticated redirects to /login
    for path in ["/dashboard", "/progress", "/ai-coach", "/profile"]:
        r = client.get(path)
        assert r.status_code == 302, f"{path} did not redirect (status {r.status_code})"
        assert "/login" in r.headers["Location"]
        print(f"  -> Protected {path} redirects to /login [PASSED]")

    # 3. Test Web Sign In (Login flow)
    print("\n[3] Testing Sign In (POST /login)...")
    login_res = client.post("/login", data={
        "username": test_username,
        "password": "securepassword123"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    print("  -> Web Login successful with session.")

    # 4. Test Data Isolation Between Two Users
    print("\n[4] Testing Strict Data Isolation Between Two Users...")
    # Create User B
    user_b_name = "testathlete_unique_2"
    user_b, err_b = database.register_user(
        name="Athlete Two",
        username=user_b_name,
        password="passwordUserB123",
        email=f"{user_b_name}@example.com"
    )
    if err_b and "already taken" in err_b:
        conn = database.get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (user_b_name,)).fetchone()
        conn.close()
        user_b = dict(row)

    # User A logs a Bench Press lift of 125 kg
    id_a, is_pr_a, _ = database.log_exercise_record(
        user_id=new_user["id"],
        exercise_name="Isolated Test Bench",
        category="Chest",
        weight_lifted=125.0,
        reps=5,
        sets=3,
        notes="Logged by User A",
        logged_date="2026-09-09"
    )

    # User B logs the SAME exercise but with 75 kg
    id_b, is_pr_b, _ = database.log_exercise_record(
        user_id=user_b["id"],
        exercise_name="Isolated Test Bench",
        category="Chest",
        weight_lifted=75.0,
        reps=10,
        sets=3,
        notes="Logged by User B",
        logged_date="2026-09-09"
    )

    # Query User A's PRs: should ONLY see 125 kg, NEVER 75 kg
    prs_a = database.get_personal_records(user_id=new_user["id"])
    bench_a = next(p for p in prs_a if p["exercise_name"] == "Isolated Test Bench")
    assert bench_a["weight_lifted"] == 125.0
    print("  -> User A sees own PR of 125 kg [ISOLATION VERIFIED]")

    # Query User B's PRs: should ONLY see 75 kg, NEVER 125 kg
    prs_b = database.get_personal_records(user_id=user_b["id"])
    bench_b = next(p for p in prs_b if p["exercise_name"] == "Isolated Test Bench")
    assert bench_b["weight_lifted"] == 75.0
    print("  -> User B sees own PR of 75 kg [ISOLATION VERIFIED]")

    # Verify User A CANNOT delete User B's record
    del_attempt = database.delete_exercise_record(id_b, user_id=new_user["id"])
    assert del_attempt is False, "User A should NOT be able to delete User B's record!"
    print("  -> Cross-user unauthorized deletion blocked [PASSED]")

    # Clean up test lift records
    database.delete_exercise_record(id_a, user_id=new_user["id"])
    database.delete_exercise_record(id_b, user_id=user_b["id"])

    # 5. Test Logout
    print("\n[5] Testing Sign Out (GET /logout)...")
    logout_res = client.get("/logout", follow_redirects=False)
    assert logout_res.status_code == 302
    assert "/login" in logout_res.headers["Location"]

    # Verify session cleared: protected page should redirect to login again
    dash_check = client.get("/dashboard")
    assert dash_check.status_code == 302
    print("  -> Session successfully cleared on logout [PASSED]")

    print("\n========================================")
    print("ALL AUTH & DATA ISOLATION TESTS PASSED 100%!")
    print("========================================")

if __name__ == "__main__":
    run_auth_tests()
