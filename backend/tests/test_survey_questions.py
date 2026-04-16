"""
Test suite for Survey Questions feature in Activities
Tests:
1. POST /api/activities with survey_responses field - verify it stores correctly
2. GET /api/activities - verify survey_responses field is returned
3. Validation that survey_responses is optional (backward compatibility)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Demo mode cookie for authentication
DEMO_COOKIE = {"demo_mode": "true"}


class TestSurveyQuestionsBackend:
    """Test survey questions feature in backend API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.cookies.update(DEMO_COOKIE)
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get a valid project_id and farmer_id for testing
        projects_resp = self.session.get(f"{BASE_URL}/api/projects")
        assert projects_resp.status_code == 200, f"Failed to get projects: {projects_resp.text}"
        projects = projects_resp.json()
        assert len(projects) > 0, "No projects found"
        self.project_id = projects[0]["project_id"]
        self.project_name = projects[0]["name"]
        
        farmers_resp = self.session.get(f"{BASE_URL}/api/farmers?page_size=100")
        assert farmers_resp.status_code == 200, f"Failed to get farmers: {farmers_resp.text}"
        farmers = farmers_resp.json()
        assert len(farmers) > 0, "No farmers found"
        self.farmer_id = farmers[0]["farmer_id"]
        self.farmer_name = farmers[0]["name"]
        
        yield
        
    def test_create_activity_with_survey_responses(self):
        """Test POST /api/activities with survey_responses field"""
        survey_responses = {
            "main_crop": "Rice",
            "crops_per_year": "2",
            "crop_residue": "Mix it into soil",
            "land_preparation": "Medium ploughing (1–2 times)",
            "fertilizer_level": "Medium",
            "irrigation_type": "Drip",
            "compost_usage": "Yes",
            "water_management": "Intermittent (sometimes dry)",
            "participation_agreement": "I Agree and want to participate"
        }
        
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 30,
            "species": "Neem",
            "planted_date": "2026-04-16",
            "lat": 17.385,
            "lng": 78.4867,
            "photo_urls": [],
            "notes": "TEST_survey_activity",
            "survey_responses": survey_responses
        }
        
        response = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert response.status_code == 200, f"Failed to create activity: {response.text}"
        
        data = response.json()
        
        # Verify activity was created
        assert "activity_id" in data
        assert data["tree_count"] == 30
        assert data["species"] == "Neem"
        assert data["status"] == "pending"
        
        # Verify survey_responses is stored and returned
        assert "survey_responses" in data, "survey_responses field missing from response"
        assert data["survey_responses"] is not None, "survey_responses is None"
        assert data["survey_responses"]["main_crop"] == "Rice"
        assert data["survey_responses"]["crops_per_year"] == "2"
        assert data["survey_responses"]["crop_residue"] == "Mix it into soil"
        assert data["survey_responses"]["land_preparation"] == "Medium ploughing (1–2 times)"
        assert data["survey_responses"]["fertilizer_level"] == "Medium"
        assert data["survey_responses"]["irrigation_type"] == "Drip"
        assert data["survey_responses"]["compost_usage"] == "Yes"
        assert data["survey_responses"]["water_management"] == "Intermittent (sometimes dry)"
        assert data["survey_responses"]["participation_agreement"] == "I Agree and want to participate"
        
        print(f"SUCCESS: Created activity {data['activity_id']} with survey_responses")
        
        # Store activity_id for cleanup
        self.created_activity_id = data["activity_id"]
        
    def test_get_activities_returns_survey_responses(self):
        """Test GET /api/activities returns survey_responses field"""
        # First create an activity with survey responses
        survey_responses = {
            "main_crop": "Wheat",
            "crops_per_year": "3 or more",
            "crop_residue": "Leave it as mulch",
            "land_preparation": "No tillage",
            "fertilizer_level": "Low",
            "irrigation_type": "Rainfed",
            "compost_usage": "No",
            "water_management": "Rainfed",
            "participation_agreement": "I Agree and want to participate"
        }
        
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 15,
            "species": "Mango",
            "planted_date": "2026-04-16",
            "notes": "TEST_survey_get_activity",
            "survey_responses": survey_responses
        }
        
        create_resp = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert create_resp.status_code == 200
        created_activity = create_resp.json()
        activity_id = created_activity["activity_id"]
        
        # Now GET all activities and find our created one
        get_resp = self.session.get(f"{BASE_URL}/api/activities")
        assert get_resp.status_code == 200, f"Failed to get activities: {get_resp.text}"
        
        activities = get_resp.json()
        assert len(activities) > 0, "No activities returned"
        
        # Find our created activity
        found_activity = None
        for activity in activities:
            if activity["activity_id"] == activity_id:
                found_activity = activity
                break
        
        assert found_activity is not None, f"Created activity {activity_id} not found in GET response"
        
        # Verify survey_responses is returned
        assert "survey_responses" in found_activity, "survey_responses field missing from GET response"
        assert found_activity["survey_responses"] is not None
        assert found_activity["survey_responses"]["main_crop"] == "Wheat"
        assert found_activity["survey_responses"]["crops_per_year"] == "3 or more"
        
        print(f"SUCCESS: GET /api/activities returns survey_responses for activity {activity_id}")
        
    def test_create_activity_without_survey_responses(self):
        """Test backward compatibility - activity can be created without survey_responses"""
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 10,
            "species": "Teak",
            "planted_date": "2026-04-16",
            "notes": "TEST_no_survey_activity"
            # No survey_responses field
        }
        
        response = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert response.status_code == 200, f"Failed to create activity without survey: {response.text}"
        
        data = response.json()
        assert "activity_id" in data
        assert data["tree_count"] == 10
        
        # survey_responses should be None or empty
        assert "survey_responses" in data
        # It can be None (not provided) - this is acceptable
        print(f"SUCCESS: Created activity {data['activity_id']} without survey_responses (backward compatible)")
        
    def test_create_activity_with_empty_survey_responses(self):
        """Test activity can be created with empty survey_responses dict"""
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 5,
            "species": "Bamboo",
            "planted_date": "2026-04-16",
            "notes": "TEST_empty_survey_activity",
            "survey_responses": {}  # Empty dict
        }
        
        response = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert response.status_code == 200, f"Failed to create activity with empty survey: {response.text}"
        
        data = response.json()
        assert "activity_id" in data
        print(f"SUCCESS: Created activity {data['activity_id']} with empty survey_responses")
        
    def test_create_activity_with_partial_survey_responses(self):
        """Test activity can be created with partial survey_responses (not all 9 questions)"""
        partial_survey = {
            "main_crop": "Cotton",
            "crops_per_year": "1"
            # Only 2 out of 9 questions answered
        }
        
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 8,
            "species": "Eucalyptus",
            "planted_date": "2026-04-16",
            "notes": "TEST_partial_survey_activity",
            "survey_responses": partial_survey
        }
        
        response = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert response.status_code == 200, f"Failed to create activity with partial survey: {response.text}"
        
        data = response.json()
        assert "activity_id" in data
        assert data["survey_responses"]["main_crop"] == "Cotton"
        assert data["survey_responses"]["crops_per_year"] == "1"
        
        print(f"SUCCESS: Created activity {data['activity_id']} with partial survey_responses")
        
    def test_survey_responses_persisted_correctly(self):
        """Test that survey_responses are persisted and retrieved correctly"""
        # Create activity with all 9 survey responses
        survey_responses = {
            "main_crop": "Millets",
            "crops_per_year": "2",
            "crop_residue": "Burn it",
            "land_preparation": "Heavy ploughing (3+ times)",
            "fertilizer_level": "High",
            "irrigation_type": "Flood irrigation",
            "compost_usage": "Yes",
            "water_management": "Continuous flooding",
            "participation_agreement": "I Do Not Agree"
        }
        
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 20,
            "species": "Moringa",
            "planted_date": "2026-04-16",
            "notes": "TEST_persistence_survey_activity",
            "survey_responses": survey_responses
        }
        
        # Create
        create_resp = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        activity_id = created["activity_id"]
        
        # Retrieve via GET /api/activities
        get_resp = self.session.get(f"{BASE_URL}/api/activities")
        assert get_resp.status_code == 200
        
        activities = get_resp.json()
        found = next((a for a in activities if a["activity_id"] == activity_id), None)
        
        assert found is not None
        assert found["survey_responses"]["main_crop"] == "Millets"
        assert found["survey_responses"]["crop_residue"] == "Burn it"
        assert found["survey_responses"]["participation_agreement"] == "I Do Not Agree"
        
        print(f"SUCCESS: Survey responses persisted and retrieved correctly for activity {activity_id}")


class TestSurveyQuestionsValidation:
    """Test survey questions validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.cookies.update(DEMO_COOKIE)
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get a valid project_id and farmer_id
        projects_resp = self.session.get(f"{BASE_URL}/api/projects")
        projects = projects_resp.json()
        self.project_id = projects[0]["project_id"]
        
        farmers_resp = self.session.get(f"{BASE_URL}/api/farmers?page_size=100")
        farmers = farmers_resp.json()
        self.farmer_id = farmers[0]["farmer_id"]
        
        yield
        
    def test_survey_responses_accepts_any_string_values(self):
        """Test that survey_responses accepts any string values (no strict validation)"""
        # Backend should accept any values - validation is on frontend
        survey_responses = {
            "main_crop": "Custom Crop",
            "crops_per_year": "5",  # Not in predefined options
            "custom_field": "Custom Value"  # Extra field
        }
        
        activity_data = {
            "farmer_id": self.farmer_id,
            "project_id": self.project_id,
            "tree_count": 12,
            "species": "Neem",
            "planted_date": "2026-04-16",
            "notes": "TEST_custom_survey_values",
            "survey_responses": survey_responses
        }
        
        response = self.session.post(f"{BASE_URL}/api/activities", json=activity_data)
        assert response.status_code == 200, f"Failed with custom survey values: {response.text}"
        
        data = response.json()
        assert data["survey_responses"]["main_crop"] == "Custom Crop"
        assert data["survey_responses"]["crops_per_year"] == "5"
        assert data["survey_responses"]["custom_field"] == "Custom Value"
        
        print(f"SUCCESS: Backend accepts custom survey values")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
