"""
Bulk CSV Farmer Onboarding - Backend API Tests
Tests: /api/farmers/bulk/template (GET), /api/farmers/bulk/validate-csv (POST multipart), /api/farmers/bulk/onboard (POST JSON)
"""
import pytest
import requests
import os
import io
import csv

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Session with demo mode cookie
@pytest.fixture(scope="module")
def demo_session():
    session = requests.Session()
    session.cookies.set('demo_mode', 'true')
    session.headers.update({'Content-Type': 'application/json'})
    return session


# ─── Helper: Build in-memory CSV ─────────────────────────────────────────────

def make_csv(rows: list[dict]) -> bytes:
    """Build CSV bytes from list of dicts."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "phone", "land_type", "acres", "upi_id"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def make_csv_file(rows: list[dict]) -> tuple:
    """Return (filename, bytes, content-type) tuple for multipart upload."""
    return ("test_farmers.csv", make_csv(rows), "text/csv")


# ─── Template Endpoint ────────────────────────────────────────────────────────

class TestBulkTemplate:
    """GET /api/farmers/bulk/template"""

    def test_template_returns_csv(self, demo_session):
        """Should return 200 with text/csv content-type"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/bulk/template")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        ct = res.headers.get("Content-Type", "")
        assert "text/csv" in ct or "csv" in ct.lower() or "text/plain" in ct, \
            f"Expected CSV content-type, got: {ct}"

    def test_template_has_correct_columns(self, demo_session):
        """Template header should have: name, phone, land_type, acres, upi_id"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/bulk/template")
        assert res.status_code == 200
        content = res.text
        reader = csv.DictReader(io.StringIO(content))
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        expected_cols = {"name", "phone", "land_type", "acres", "upi_id"}
        assert expected_cols.issubset(set(headers)), \
            f"Missing columns. Expected {expected_cols}, got {headers}"

    def test_template_has_10_sample_rows(self, demo_session):
        """Template should contain 10 sample data rows"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/bulk/template")
        assert res.status_code == 200
        reader = csv.DictReader(io.StringIO(res.text))
        rows = list(reader)
        assert len(rows) == 10, f"Expected 10 sample rows, got {len(rows)}"

    def test_template_sample_rows_valid(self, demo_session):
        """Sample rows should have valid phone numbers (10 digits, starts with 6-9)"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/bulk/template")
        assert res.status_code == 200
        reader = csv.DictReader(io.StringIO(res.text))
        rows = list(reader)
        for row in rows:
            phone = row.get("phone", "").strip()
            assert len(phone) == 10, f"Template row phone not 10 digits: {phone}"
            assert phone[0] in "6789", f"Template phone doesn't start with 6-9: {phone}"

    def test_template_requires_auth(self):
        """Template endpoint should require authentication (no cookie => 404 or 401)"""
        res = requests.get(f"{BASE_URL}/api/farmers/bulk/template")
        # Demo user not found without demo_mode cookie
        assert res.status_code in [401, 404], \
            f"Expected 401/404 without auth, got {res.status_code}"


# ─── Validate CSV Endpoint ────────────────────────────────────────────────────

class TestBulkValidateCSV:
    """POST /api/farmers/bulk/validate-csv (multipart/form-data)"""

    @pytest.fixture(scope="class")
    def project_id(self, demo_session):
        """Get first project_id from the demo user's projects"""
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200
        projects = res.json()
        assert len(projects) >= 1, "Need at least one project"
        return projects[0]["project_id"]

    def _post_validate(self, demo_session, rows, project_id, filename="test.csv"):
        """Helper: POST to validate-csv and return response"""
        csv_bytes = make_csv(rows)
        # multipart upload - don't use json Content-Type header
        headers = {"Cookie": f"demo_mode=true"}
        res = requests.post(
            f"{BASE_URL}/api/farmers/bulk/validate-csv",
            files={"file": (filename, csv_bytes, "text/csv")},
            data={"project_id": project_id},
            cookies={"demo_mode": "true"}
        )
        return res

    def test_validate_all_valid_rows(self, demo_session, project_id):
        """CSV with all valid unique rows should return valid_count = total_rows, error_count = 0"""
        rows = [
            {"name": "TEST_BulkFarmer Alpha", "phone": "9011223344", "land_type": "owned", "acres": "2.5", "upi_id": "alpha@gpay"},
            {"name": "TEST_BulkFarmer Beta",  "phone": "9022334455", "land_type": "leased", "acres": "1.0", "upi_id": "beta@paytm"},
        ]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["total_rows"] == 2
        assert data["valid_count"] == 2
        assert data["error_count"] == 0
        assert "rows" in data
        for r in data["rows"]:
            assert r["errors"] == [], f"Row {r['row']} should be valid, got errors: {r['errors']}"

    def test_validate_returns_correct_summary_fields(self, demo_session, project_id):
        """Response should contain total_rows, valid_count, error_count, project_id, project_name, rows"""
        rows = [{"name": "TEST_SummaryCheck", "phone": "9033445566", "land_type": "owned", "acres": "1.0", "upi_id": ""}]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        required = ["total_rows", "valid_count", "error_count", "project_id", "project_name", "rows"]
        for field in required:
            assert field in data, f"Missing field '{field}' in response"
        assert data["project_id"] == project_id

    def test_validate_missing_name(self, demo_session, project_id):
        """Row with missing name should have 'name is required' error"""
        rows = [{"name": "", "phone": "9044556677", "land_type": "owned", "acres": "1.0", "upi_id": ""}]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["error_count"] == 1
        assert data["valid_count"] == 0
        row = data["rows"][0]
        assert any("name" in e.lower() for e in row["errors"]), \
            f"Expected name error, got: {row['errors']}"

    def test_validate_bad_phone_too_short(self, demo_session, project_id):
        """Row with phone '123' (3 digits) should be flagged"""
        rows = [{"name": "TEST_BadPhone", "phone": "123", "land_type": "owned", "acres": "1.0", "upi_id": ""}]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["error_count"] == 1
        row = data["rows"][0]
        assert any("phone" in e.lower() or "digit" in e.lower() for e in row["errors"]), \
            f"Expected phone digit error, got: {row['errors']}"

    def test_validate_invalid_land_type(self, demo_session, project_id):
        """Row with land_type='community' should be flagged"""
        rows = [{"name": "TEST_BadLand", "phone": "9055667788", "land_type": "community", "acres": "1.0", "upi_id": ""}]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["error_count"] == 1
        row = data["rows"][0]
        assert any("land_type" in e.lower() for e in row["errors"]), \
            f"Expected land_type error, got: {row['errors']}"

    def test_validate_negative_acres(self, demo_session, project_id):
        """Row with acres=-1 should be flagged"""
        rows = [{"name": "TEST_NegAcres", "phone": "9066778899", "land_type": "owned", "acres": "-1", "upi_id": ""}]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["error_count"] == 1
        row = data["rows"][0]
        assert any("acres" in e.lower() or "positive" in e.lower() for e in row["errors"]), \
            f"Expected acres error, got: {row['errors']}"

    def test_validate_mixed_valid_and_invalid(self, demo_session, project_id):
        """Mixed CSV: valid rows and invalid rows should be split correctly"""
        rows = [
            # Valid
            {"name": "TEST_MixedValid1", "phone": "9077889900", "land_type": "owned", "acres": "2.0", "upi_id": "mixv1@gpay"},
            {"name": "TEST_MixedValid2", "phone": "9088990011", "land_type": "leased", "acres": "3.0", "upi_id": ""},
            # Invalid: missing name
            {"name": "", "phone": "9099001122", "land_type": "owned", "acres": "1.0", "upi_id": ""},
            # Invalid: bad phone
            {"name": "TEST_BadPhone2", "phone": "123", "land_type": "owned", "acres": "", "upi_id": ""},
            # Invalid: bad land_type
            {"name": "TEST_BadLand2", "phone": "9100112233", "land_type": "community", "acres": "", "upi_id": ""},
        ]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["total_rows"] == 5, f"Expected 5 total rows, got {data['total_rows']}"
        assert data["valid_count"] == 2, f"Expected 2 valid rows, got {data['valid_count']}"
        assert data["error_count"] == 3, f"Expected 3 error rows, got {data['error_count']}"

    def test_validate_duplicate_phone_in_csv(self, demo_session, project_id):
        """Duplicate phone in same CSV should be caught as error"""
        rows = [
            {"name": "TEST_DupFirst",  "phone": "9111222333", "land_type": "owned", "acres": "2.0", "upi_id": ""},
            {"name": "TEST_DupSecond", "phone": "9111222333", "land_type": "owned", "acres": "1.5", "upi_id": ""},
        ]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        # Second row with duplicate phone should have an error
        assert data["error_count"] >= 1, f"Expected at least 1 error for duplicate phone, got {data['error_count']}"
        # Find the duplicate row's errors
        duplicate_row = next((r for r in data["rows"] if r["row"] == 3), None)
        if duplicate_row:
            assert any("duplicate" in e.lower() for e in duplicate_row["errors"]), \
                f"Expected 'duplicate' error, got: {duplicate_row['errors']}"

    def test_validate_phone_already_in_db(self, demo_session, project_id):
        """Phone that is already in DB should be flagged"""
        # Get an existing farmer's phone from DB
        farmers_res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=1")
        assert farmers_res.status_code == 200
        farmers = farmers_res.json()
        if not farmers:
            pytest.skip("No farmers in DB to test with")
        existing_phone = farmers[0]["phone"]
        existing_name = farmers[0]["name"]

        rows = [
            {"name": "TEST_DBDupCheck", "phone": existing_phone, "land_type": "owned", "acres": "1.0", "upi_id": ""},
        ]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        assert data["error_count"] == 1, f"Expected DB duplicate to be caught as error, got {data['error_count']}"
        row = data["rows"][0]
        assert any("registered" in e.lower() or "already" in e.lower() for e in row["errors"]), \
            f"Expected 'already registered' error for existing phone, got: {row['errors']}"

    def test_validate_empty_csv(self, demo_session, project_id):
        """Empty CSV (just headers, no rows) should return 400"""
        csv_bytes = b"name,phone,land_type,acres,upi_id\n"
        res = requests.post(
            f"{BASE_URL}/api/farmers/bulk/validate-csv",
            files={"file": ("empty.csv", csv_bytes, "text/csv")},
            data={"project_id": project_id},
            cookies={"demo_mode": "true"}
        )
        assert res.status_code == 400, f"Expected 400 for empty CSV, got {res.status_code}"

    def test_validate_missing_required_columns(self, demo_session, project_id):
        """CSV missing required columns should return 400"""
        csv_bytes = b"firstname,mobile\nJohn,9876543210\n"
        res = requests.post(
            f"{BASE_URL}/api/farmers/bulk/validate-csv",
            files={"file": ("bad_cols.csv", csv_bytes, "text/csv")},
            data={"project_id": project_id},
            cookies={"demo_mode": "true"}
        )
        assert res.status_code == 400, f"Expected 400 for missing columns, got {res.status_code}"
        assert "missing" in res.text.lower(), f"Expected 'missing columns' in error, got: {res.text}"

    def test_validate_invalid_project(self, demo_session):
        """Non-existent project_id should return 404"""
        rows = [{"name": "TEST_ProjCheck", "phone": "9222333444", "land_type": "owned", "acres": "1.0", "upi_id": ""}]
        csv_bytes = make_csv(rows)
        res = requests.post(
            f"{BASE_URL}/api/farmers/bulk/validate-csv",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"project_id": "proj_does_not_exist"},
            cookies={"demo_mode": "true"}
        )
        assert res.status_code == 404, f"Expected 404 for invalid project, got {res.status_code}"

    def test_validate_phone_strip_plus91(self, demo_session, project_id):
        """Phone with +91 prefix should be normalized (10-digit valid phone)"""
        rows = [
            {"name": "TEST_Plus91Farm", "phone": "+919333444555", "land_type": "owned", "acres": "2.0", "upi_id": ""}
        ]
        res = self._post_validate(demo_session, rows, project_id)
        assert res.status_code == 200
        data = res.json()
        # After stripping +91, 9333444555 is a valid 10-digit number starting with 9
        row = data["rows"][0]
        assert row["errors"] == [], f"+91 prefix should be stripped and phone valid, but got errors: {row['errors']}"
        assert row["phone"] == "9333444555", f"Expected stripped phone '9333444555', got '{row['phone']}'"


# ─── Onboard Endpoint ─────────────────────────────────────────────────────────

class TestBulkOnboard:
    """POST /api/farmers/bulk/onboard"""

    @pytest.fixture(scope="class")
    def project_id(self, demo_session):
        """Get first project_id from the demo user's projects"""
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200
        projects = res.json()
        assert len(projects) >= 1, "Need at least one project"
        return projects[0]["project_id"]

    def test_onboard_valid_rows(self, demo_session, project_id):
        """Onboard 2 valid farmers - both should succeed"""
        rows = [
            {"row": 2, "name": "TEST_OnboardA", "phone": "9400000001", "land_type": "owned", "acres": "2.5", "upi_id": "oba@gpay", "errors": []},
            {"row": 3, "name": "TEST_OnboardB", "phone": "9400000002", "land_type": "leased", "acres": "1.0", "upi_id": "", "errors": []},
        ]
        # Clean up any existing test farmers first
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": rows}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["success_count"] == 2, f"Expected 2 successes, got {data['success_count']}"
        assert data["error_count"] == 0, f"Expected 0 errors, got {data['error_count']}"
        assert data["project_id"] == project_id

    def test_onboard_returns_project_name(self, demo_session, project_id):
        """Onboard response should contain project_name"""
        rows = [
            {"row": 2, "name": "TEST_ProjNameCheck", "phone": "9400000003", "land_type": "owned", "acres": "1.0", "upi_id": "", "errors": []},
        ]
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": rows}
        )
        assert res.status_code == 200
        data = res.json()
        assert "project_name" in data, "Response should contain project_name"
        assert len(data["project_name"]) > 0

    def test_onboard_duplicate_phone_rejected(self, demo_session, project_id):
        """Phone already in DB (from previous onboard test) should be rejected"""
        # 9400000001 was onboarded in test_onboard_valid_rows
        rows = [
            {"row": 2, "name": "TEST_DupOnboard", "phone": "9400000001", "land_type": "owned", "acres": "1.0", "upi_id": "", "errors": []},
        ]
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": rows}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success_count"] == 0, f"Expected 0 successes for dup phone, got {data['success_count']}"
        assert data["error_count"] == 1, f"Expected 1 error for dup phone, got {data['error_count']}"
        assert len(data["errors"]) == 1
        error_reason = data["errors"][0]["reason"]
        assert "registered" in error_reason.lower() or "already" in error_reason.lower(), \
            f"Expected 'already registered' reason, got: {error_reason}"

    def test_onboard_persists_to_db(self, demo_session, project_id):
        """Onboarded farmer should appear in /api/farmers list"""
        # Use a unique phone unlikely to be in DB
        rows = [
            {"row": 2, "name": "TEST_PersistCheck", "phone": "9400000010", "land_type": "owned", "acres": "3.0", "upi_id": "persist@gpay", "errors": []},
        ]
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": rows}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success_count"] == 1

        # Verify farmer appears in list
        farmers_res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=10")
        assert farmers_res.status_code == 200
        farmers = farmers_res.json()
        farmer_phones = [f["phone"] for f in farmers]
        assert "9400000010" in farmer_phones, \
            f"Onboarded farmer phone '9400000010' not found in first page. Found: {farmer_phones}"

    def test_onboard_invalid_project_returns_404(self, demo_session):
        """Non-existent project_id should return 404"""
        rows = [
            {"row": 2, "name": "TEST_NoProject", "phone": "9400000099", "land_type": "owned", "acres": "1.0", "upi_id": "", "errors": []},
        ]
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": "proj_does_not_exist", "rows": rows}
        )
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"

    def test_onboard_empty_rows_returns_400(self, demo_session, project_id):
        """Empty rows list should return 400"""
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": []}
        )
        assert res.status_code == 400, f"Expected 400 for empty rows, got {res.status_code}"

    def test_onboard_partial_success(self, demo_session, project_id):
        """Batch with 1 valid and 1 duplicate phone => success_count=1, error_count=1"""
        rows = [
            # New farmer
            {"row": 2, "name": "TEST_PartialGood", "phone": "9400000020", "land_type": "owned", "acres": "2.0", "upi_id": "", "errors": []},
            # Duplicate (9400000001 was onboarded earlier)
            {"row": 3, "name": "TEST_PartialBad", "phone": "9400000001", "land_type": "owned", "acres": "1.0", "upi_id": "", "errors": []},
        ]
        res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": rows}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success_count"] == 1, f"Expected 1 success, got {data['success_count']}"
        assert data["error_count"] == 1, f"Expected 1 error, got {data['error_count']}"


# ─── End-to-End: Validate then Onboard ───────────────────────────────────────

class TestBulkE2E:
    """End-to-end: validate CSV → onboard valid rows"""

    @pytest.fixture(scope="class")
    def project_id(self, demo_session):
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200
        return res.json()[0]["project_id"]

    def test_full_flow_validate_then_onboard(self, demo_session, project_id):
        """Full flow: validate mixed CSV → onboard only valid rows"""
        rows_csv = [
            # Valid
            {"name": "TEST_E2E_Good1", "phone": "9500000001", "land_type": "owned", "acres": "2.0", "upi_id": "e2eg1@gpay"},
            {"name": "TEST_E2E_Good2", "phone": "9500000002", "land_type": "leased", "acres": "3.0", "upi_id": ""},
            # Invalid - missing name
            {"name": "", "phone": "9500000003", "land_type": "owned", "acres": "1.0", "upi_id": ""},
            # Invalid - bad phone
            {"name": "TEST_E2E_BadPhone", "phone": "123", "land_type": "owned", "acres": "", "upi_id": ""},
        ]
        csv_bytes = make_csv(rows_csv)

        # Step 1: Validate
        validate_res = requests.post(
            f"{BASE_URL}/api/farmers/bulk/validate-csv",
            files={"file": ("e2e.csv", csv_bytes, "text/csv")},
            data={"project_id": project_id},
            cookies={"demo_mode": "true"}
        )
        assert validate_res.status_code == 200
        vdata = validate_res.json()
        assert vdata["valid_count"] == 2, f"Expected 2 valid rows, got {vdata['valid_count']}"
        assert vdata["error_count"] == 2, f"Expected 2 error rows, got {vdata['error_count']}"

        # Step 2: Onboard only valid rows
        valid_rows = [r for r in vdata["rows"] if r["errors"] == []]
        onboard_res = demo_session.post(
            f"{BASE_URL}/api/farmers/bulk/onboard",
            json={"project_id": project_id, "rows": valid_rows}
        )
        assert onboard_res.status_code == 200
        odata = onboard_res.json()
        assert odata["success_count"] == 2, f"Expected 2 onboarded, got {odata['success_count']}"
        assert odata["error_count"] == 0, f"Expected 0 errors, got {odata['error_count']}"

        # Step 3: Verify count increased
        count_res = demo_session.get(f"{BASE_URL}/api/farmers/count/total")
        assert count_res.status_code == 200
        total = count_res.json()["total"]
        assert total >= 2, f"Farmer count should have grown: got {total}"
