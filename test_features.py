"""
Comprehensive test script for FitLift Progress & PR Tracker + AI Coach features.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import app
import database
import ai_advisor

def run_tests():
    print("========================================")
    print("Testing FitLift New Features")
    print("========================================")
    
    # 1. Test database helpers
    print("\n[1] Testing Database Progress & PR helpers...")
    stats = database.get_progress_stats(user_id=1)
    assert stats["total_logs"] > 0, "total_logs should be > 0"
    assert stats["unique_exercises"] > 0, "unique_exercises should be > 0"
    print(f"  -> Total logs: {stats['total_logs']}, Unique exercises: {stats['unique_exercises']}")
    if stats["heaviest_lift"]:
        print(f"  -> Heaviest lift: {stats['heaviest_lift']['exercise_name']} ({stats['heaviest_lift']['weight_lifted']} kg)")

    prs = database.get_personal_records(user_id=1)
    print(f"  -> Found {len(prs)} Personal Records for user 1.")
    assert len(prs) > 0, "PR count should be > 0"

    # Test logging a new PR lift
    new_id, is_pr, old_pr = database.log_exercise_record(
        user_id=1,
        exercise_name="Incline Barbell Bench Press",
        category="Chest",
        weight_lifted=82.5,
        reps=6,
        sets=3,
        notes="Automated test log",
        logged_date="2026-09-09"
    )
    print(f"  -> Logged exercise ID={new_id}, is_new_pr={is_pr}, old_pr={old_pr}")
    assert new_id is not None
    assert is_pr is True

    # Test deleting the test record
    del_ok = database.delete_exercise_record(new_id)
    assert del_ok is True
    print(f"  -> Successfully deleted test record ID={new_id}")

    # 2. Test AI Advisor Engine
    print("\n[2] Testing AI Advisor Situational Reasoning...")
    situations = [
        ("soreness", "I am feeling sore after squats"),
        ("plateau", "I cannot increase weight on bench press"),
        ("quick_workout", "I only have 20 minutes to work out"),
        ("nutrition", "I missed my protein goal today"),
        ("injury_recovery", "My shoulder hurts during benching"),
        ("travel", "I am in a hotel with no equipment"),
        ("general", "How much water should I drink?")
    ]

    for sit_tag, user_msg in situations:
        advice = ai_advisor.generate_situational_advice(user_msg, user_id=1, situation_tag=sit_tag)
        assert len(advice) > 50, f"Advice too short for {sit_tag}"
        first_line = advice.split('\n')[0]
        print(f"  -> Tag '{sit_tag}': {first_line}")

    # 3. Test Flask Test Client Endpoints
    print("\n[3] Testing Flask Routes with TestClient...")
    client = app.app.test_client()

    # Unauthenticated root redirects to /login
    r = client.get("/")
    assert r.status_code == 302, f"Home returned {r.status_code}"
    print("  -> GET / [302 Redirect to /login]")

    # Log in as user 1
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Shravan"

    # Authenticated root redirects to /dashboard
    r = client.get("/")
    assert r.status_code == 302
    assert "/dashboard" in r.headers["Location"]
    print("  -> Authenticated GET / [302 Redirect to /dashboard]")

    # Progress page
    r = client.get("/progress")
    assert r.status_code == 200, f"Progress returned {r.status_code}"
    assert b"Personal Best Vault" in r.data
    assert b"Submit New Log Lift &amp; Record in PR Vault" in r.data or b"Submit New Log Lift & Record in PR Vault" in r.data
    print("  -> GET /progress [200 OK] Verified PR submit button present.")

    # Dashboard with user 1
    r = client.get("/dashboard/1")
    assert r.status_code == 200, f"Dashboard returned {r.status_code}"
    assert b"Personal Records (PRs)" in r.data
    assert b"Submit New Log Lift" in r.data
    assert b"Record New Lift to PR Vault" in r.data
    print("  -> GET /dashboard/1 [200 OK] Verified Dashboard PR submit button & modal present.")

    # Test POST /progress/add with redirect to dashboard
    r = client.post("/progress/add", data={
        "exercise_name": "Trap Bar Deadlift",
        "category": "Back",
        "weight_lifted": 175.0,
        "reps": 5,
        "sets": 3,
        "notes": "Testing dashboard PR submit button",
        "logged_date": "2026-09-09",
        "redirect_to": "dashboard"
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "/dashboard" in r.headers["Location"]
    print("  -> POST /progress/add (redirect_to=dashboard) [302 Redirect to /dashboard]")

    # Check that the new record is in PRs
    prs_after = database.get_personal_records(user_id=1)
    trap_prs = [p for p in prs_after if p["exercise_name"] == "Trap Bar Deadlift"]
    assert len(trap_prs) > 0
    assert trap_prs[0]["weight_lifted"] == 175.0
    print(f"  -> Verified new PR recorded in vault: {trap_prs[0]['exercise_name']} @ {trap_prs[0]['weight_lifted']} kg")

    # Clean up test record
    database.delete_exercise_record(trap_prs[0]["id"], user_id=1)
    print("  -> Cleaned up test record.")

    # AI Coach page
    r = client.get("/ai-coach")
    assert r.status_code == 200, f"AI Coach returned {r.status_code}"
    assert b"FitAI Personal Advisor" in r.data
    print("  -> GET /ai-coach [200 OK]")

    # API Chat endpoint
    r = client.post("/api/chat", json={
        "message": "I hit a plateau on deadlifts, advice please!",
        "user_id": 1,
        "situation_tag": "plateau"
    })
    assert r.status_code == 200, f"API chat returned {r.status_code}"
    data = r.get_json()
    assert data["status"] == "success"
    assert "reply" in data
    print("  -> POST /api/chat [200 OK] Received advice.")

    # API Chat history
    r = client.get("/api/chat/history?user_id=1")
    assert r.status_code == 200
    msgs = r.get_json()["messages"]
    assert len(msgs) > 0
    print(f"  -> GET /api/chat/history [200 OK] {len(msgs)} messages in history.")

    # API User Summary
    r = client.get("/api/user-summary/1")
    assert r.status_code == 200
    u_data = r.get_json()
    assert u_data["id"] == 1
    print(f"  -> GET /api/user-summary/1 [200 OK] Profile '{u_data['name']}' loaded.")

    print("\n========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("========================================")

if __name__ == "__main__":
    run_tests()
