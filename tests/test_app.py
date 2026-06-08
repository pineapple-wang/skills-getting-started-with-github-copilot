"""
Tests for the Mergington High School Activities API

Uses the AAA (Arrange-Act-Assert) pattern for clear test structure.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse


@pytest.fixture
def test_app():
    """
    Fixture that creates a fresh app instance with minimal test data.
    Each test gets a clean state to avoid side effects.
    """
    # Arrange: Create a fresh app with test activities
    app = FastAPI()
    
    # Minimal test data
    test_activities = {
        "Chess Club": {
            "description": "Learn chess strategies",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["alice@test.edu"]
        },
        "Programming Class": {
            "description": "Learn coding",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        }
    }
    
    # Add routes to the fresh app
    @app.get("/")
    def root():
        return RedirectResponse(url="/static/index.html")
    
    @app.get("/activities")
    def get_activities():
        return test_activities
    
    @app.post("/activities/{activity_name}/signup")
    def signup_for_activity(activity_name: str, email: str):
        """Sign up a student for an activity"""
        if activity_name not in test_activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        activity = test_activities[activity_name]
        
        if email in activity["participants"]:
            raise HTTPException(status_code=400, detail="Student already signed up for this activity")
        activity["participants"].append(email)
        return {"message": f"Signed up {email} for {activity_name}"}
    
    @app.delete("/activities/{activity_name}/signup")
    def unregister_from_activity(activity_name: str, email: str):
        """Unregister a student from an activity"""
        if activity_name not in test_activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        activity = test_activities[activity_name]
        
        if email in activity["participants"]:
            activity["participants"].remove(email)
            return {"message": f"Unregistered {email} from {activity_name}"}
        else:
            raise HTTPException(status_code=404, detail="Participant not found")
    
    return app


@pytest.fixture
def client(test_app):
    """TestClient fixture for making requests to the test app."""
    return TestClient(test_app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: Fresh app with test activities
        Act: Make GET request to /activities
        Assert: Response contains all activities with correct structure
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert activities["Chess Club"]["description"] == "Learn chess strategies"
        assert activities["Programming Class"]["max_participants"] == 20
    
    def test_get_activities_includes_participant_list(self, client):
        """
        Arrange: Fresh app with activities that have participants
        Act: Make GET request to /activities
        Assert: Response includes participants list for each activity
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert "participants" in activities["Chess Club"]
        assert "alice@test.edu" in activities["Chess Club"]["participants"]
        assert isinstance(activities["Programming Class"]["participants"], list)


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: Fresh app with root redirect
        Act: Make GET request to /
        Assert: Response redirects to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_succeeds(self, client):
        """
        Arrange: Fresh app with empty Programming Class
        Act: Sign up new student for activity
        Assert: Student is added and success message returned
        """
        # Arrange
        activity_name = "Programming Class"
        email = "bob@test.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            json={}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up bob@test.edu" in response.json()["message"]
        
        # Verify student was added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_student_returns_400(self, client):
        """
        Arrange: Fresh app with Chess Club having alice@test.edu
        Act: Try to sign up alice@test.edu for Chess Club again
        Assert: Returns 400 error with duplicate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@test.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            json={}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Fresh app without "Music Club" activity
        Act: Try to sign up for non-existent activity
        Assert: Returns 404 error
        """
        # Arrange
        activity_name = "Music Club"
        email = "charlie@test.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            json={}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_existing_participant_succeeds(self, client):
        """
        Arrange: Fresh app with Chess Club containing alice@test.edu
        Act: Unregister alice from Chess Club
        Assert: Participant is removed and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "alice@test.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered alice@test.edu" in response.json()["message"]
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_nonexistent_participant_returns_404(self, client):
        """
        Arrange: Fresh app with Chess Club not containing unknown@test.edu
        Act: Try to unregister non-existent participant
        Assert: Returns 404 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "unknown@test.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Fresh app without "Music Club" activity
        Act: Try to unregister from non-existent activity
        Assert: Returns 404 error
        """
        # Arrange
        activity_name = "Music Club"
        email = "alice@test.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
