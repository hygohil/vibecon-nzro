"""
VanaLedger backend API tests
Tests all major API endpoints with demo mode authentication
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Demo mode headers and cookies
DEMO_HEADERS = {
    'Content-Type': 'application/json',
    'X-Demo-Mode': 'true'
}


@pytest.fixture(scope="module")
def demo_session():
    """Create a session with demo mode enabled"""
    session = requests.Session()
    session.cookies.set('demo_mode', 'true')
    session.headers.update({'Content-Type': 'application/json'})
    return session


# ─── Auth Tests ───

class TestAuth:
    """Authentication endpoint tests"""

    def test_demo_user_endpoint(self, demo_session):
        """GET /api/auth/demo-user - should return demo user"""
        res = demo_session.get(f"{BASE_URL}/api/auth/demo-user")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert 'user_id' in data
        assert 'email' in data
        assert data['email'] == 'demo@aggregatoros.com', f"Expected demo email, got {data['email']}"

    def test_auth_me_demo_mode(self, demo_session):
        """GET /api/auth/me - should work in demo mode"""
        res = demo_session.get(f"{BASE_URL}/api/auth/me")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert 'user_id' in data
        assert 'email' in data


# ─── Dashboard Tests ───

class TestDashboard:
    """Dashboard stats tests"""

    def test_dashboard_stats(self, demo_session):
        """GET /api/dashboard/stats - should return all required keys"""
        res = demo_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        # Check required keys
        required_keys = ['total_projects', 'total_farmers', 'total_activities',
                         'pending_verification', 'verified_activities', 'approved_trees',
                         'estimated_credits', 'total_payout', 'recent_activities']
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_dashboard_stats_real_numbers(self, demo_session):
        """Dashboard stats should show seeded data numbers"""
        res = demo_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert res.status_code == 200
        data = res.json()
        # Seeded data should have: 4 projects, 65 farmers, 227 activities
        assert data['total_projects'] >= 4, f"Expected >=4 projects, got {data['total_projects']}"
        assert data['total_farmers'] >= 65, f"Expected >=65 farmers, got {data['total_farmers']}"
        assert data['total_activities'] >= 100, f"Expected many activities, got {data['total_activities']}"

    def test_dashboard_recent_activities_farmer_names(self, demo_session):
        """Recent activities should have farmer names (not None)"""
        res = demo_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert res.status_code == 200
        data = res.json()
        activities = data.get('recent_activities', [])
        for act in activities:
            assert act.get('farmer_name') is not None, f"farmer_name is None for activity {act.get('activity_id')}"
            assert len(act.get('farmer_name', '')) > 0, f"farmer_name is empty for activity {act.get('activity_id')}"


# ─── Projects Tests ───

class TestProjects:
    """Projects CRUD tests"""

    def test_list_projects(self, demo_session):
        """GET /api/projects - should return list of projects"""
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) >= 4, f"Expected >=4 projects, got {len(data)}"

    def test_project_fields(self, demo_session):
        """Projects should have required fields"""
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200
        projects = res.json()
        required_fields = ['project_id', 'name', 'region', 'status', 'farmers_count', 'activities_count', 'payout_rate']
        for proj in projects[:2]:
            for field in required_fields:
                assert field in proj, f"Missing field '{field}' in project {proj.get('project_id')}"

    def test_create_and_delete_project(self, demo_session):
        """POST /api/projects + DELETE - create and clean up"""
        payload = {
            "name": "TEST_Audit Project",
            "region": "gujarat",
            "description": "Test project for audit",
            "payout_rate": 600,
            "payout_rule_type": "per_tco2e",
            "survival_rate": 0.7,
            "conservative_discount": 0.2,
            "max_trees_per_acre": 400,
            "cooldown_days": 30,
            "monitoring_frequency_days": 90
        }
        res = demo_session.post(f"{BASE_URL}/api/projects", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        created = res.json()
        assert created['name'] == "TEST_Audit Project"
        assert 'project_id' in created
        project_id = created['project_id']

        # Delete it
        del_res = demo_session.delete(f"{BASE_URL}/api/projects/{project_id}")
        assert del_res.status_code == 200, f"Delete failed: {del_res.status_code}"

    def test_project_no_village_district_fields(self, demo_session):
        """Projects should NOT have village or district fields"""
        res = demo_session.get(f"{BASE_URL}/api/projects")
        assert res.status_code == 200
        projects = res.json()
        for proj in projects:
            assert 'village' not in proj, "Project has 'village' field (should be removed)"
            assert 'district' not in proj, "Project has 'district' field (should be removed)"


# ─── Farmers Tests ───

class TestFarmers:
    """Farmers CRUD tests"""

    def test_list_farmers_pagination(self, demo_session):
        """GET /api/farmers?page=1&page_size=10 - should return paginated farmers"""
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=10")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) <= 10, f"Expected <=10 farmers per page, got {len(data)}"

    def test_farmers_total_count(self, demo_session):
        """GET /api/farmers/count/total - should return total count"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/count/total")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert 'total' in data, "Missing 'total' field"
        assert data['total'] >= 65, f"Expected >=65 farmers, got {data['total']}"

    def test_farmers_7_pages(self, demo_session):
        """65 farmers with page_size=10 should yield 7 pages"""
        res = demo_session.get(f"{BASE_URL}/api/farmers/count/total")
        assert res.status_code == 200
        total = res.json()['total']
        import math
        pages = math.ceil(total / 10)
        assert pages >= 7, f"Expected >=7 pages, got {pages} (total={total})"

    def test_farmer_fields_no_village_district(self, demo_session):
        """Farmers should NOT have village or district fields"""
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=5")
        assert res.status_code == 200
        farmers = res.json()
        for farmer in farmers:
            assert 'village' not in farmer, f"Farmer {farmer.get('farmer_id')} has 'village' field"
            assert 'district' not in farmer, f"Farmer {farmer.get('farmer_id')} has 'district' field"

    def test_farmer_phone_format(self, demo_session):
        """Farmer phone numbers should be 10 digits"""
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=20")
        assert res.status_code == 200
        farmers = res.json()
        for farmer in farmers:
            phone = farmer.get('phone', '')
            digits = ''.join(c for c in phone if c.isdigit())
            assert len(digits) == 10, f"Farmer {farmer['name']} has non-10-digit phone: {phone} (digits: {digits})"

    def test_farmer_names_are_proper(self, demo_session):
        """Farmer names should be proper Indian names (not test data)"""
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=20")
        assert res.status_code == 200
        farmers = res.json()
        for farmer in farmers:
            name = farmer.get('name', '')
            assert len(name) > 2, f"Farmer name too short: {name}"
            # Should not be generic test names
            assert 'test' not in name.lower(), f"Farmer has test name: {name}"

    def test_create_farmer_duplicate_phone(self, demo_session):
        """POST /api/farmers - duplicate phone should return 409"""
        # Get an existing farmer's phone
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=1")
        assert res.status_code == 200
        farmers = res.json()
        if not farmers:
            pytest.skip("No farmers to test with")
        existing_phone = farmers[0]['phone']
        existing_project_id = farmers[0]['project_id']

        # Try to create a farmer with the same phone
        payload = {
            "name": "TEST_Duplicate Farmer",
            "phone": existing_phone,
            "land_type": "owned",
            "project_id": existing_project_id
        }
        res2 = demo_session.post(f"{BASE_URL}/api/farmers", json=payload)
        assert res2.status_code == 409, f"Expected 409 for duplicate phone, got {res2.status_code}: {res2.text}"

    def test_farmers_pagination_page2(self, demo_session):
        """GET /api/farmers?page=2 - should return different farmers"""
        res1 = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=10")
        res2 = demo_session.get(f"{BASE_URL}/api/farmers?page=2&page_size=10")
        assert res1.status_code == 200
        assert res2.status_code == 200
        page1_ids = {f['farmer_id'] for f in res1.json()}
        page2_ids = {f['farmer_id'] for f in res2.json()}
        # Pages should not overlap
        overlap = page1_ids & page2_ids
        assert len(overlap) == 0, f"Page 1 and Page 2 have overlapping farmer IDs: {overlap}"


# ─── Activities Tests ───

class TestActivities:
    """Activities endpoint tests"""

    def test_list_activities(self, demo_session):
        """GET /api/activities - should return list"""
        res = demo_session.get(f"{BASE_URL}/api/activities")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) >= 50, f"Expected many activities from seed data, got {len(data)}"

    def test_activities_have_statuses(self, demo_session):
        """Activities should have pending/approved/rejected statuses"""
        res = demo_session.get(f"{BASE_URL}/api/activities")
        assert res.status_code == 200
        activities = res.json()
        statuses = {a['status'] for a in activities}
        # Seeded data should have at least pending and approved
        assert 'pending' in statuses or 'approved' in statuses, f"No expected statuses found, only: {statuses}"

    def test_filter_activities_by_status(self, demo_session):
        """GET /api/activities?status=pending - should return only pending"""
        res = demo_session.get(f"{BASE_URL}/api/activities?status=pending")
        assert res.status_code == 200
        activities = res.json()
        for act in activities:
            assert act['status'] == 'pending', f"Got non-pending activity: {act['status']}"

    def test_activity_fields(self, demo_session):
        """Activities should have required fields"""
        res = demo_session.get(f"{BASE_URL}/api/activities?status=pending")
        assert res.status_code == 200
        activities = res.json()
        if not activities:
            pytest.skip("No pending activities to test with")
        required_fields = ['activity_id', 'farmer_id', 'farmer_name', 'project_id',
                           'tree_count', 'species', 'status', 'estimated_credits', 'estimated_payout']
        for act in activities[:3]:
            for field in required_fields:
                assert field in act, f"Missing field '{field}' in activity {act.get('activity_id')}"

    def test_activity_no_old_claim_fields(self, demo_session):
        """Activities should NOT have old 'claim_id' or 'farmer_village' fields"""
        res = demo_session.get(f"{BASE_URL}/api/activities")
        assert res.status_code == 200
        activities = res.json()
        for act in activities[:10]:
            assert 'claim_id' not in act, "Activity still has old 'claim_id' field"
            assert 'farmer_village' not in act, "Activity still has 'farmer_village' field"

    def test_verify_activity_approve(self, demo_session):
        """PUT /api/activities/{id}/verify - approve action"""
        # Get a pending activity
        res = demo_session.get(f"{BASE_URL}/api/activities?status=pending")
        assert res.status_code == 200
        activities = res.json()
        if not activities:
            pytest.skip("No pending activities to test with")
        
        activity_id = activities[0]['activity_id']
        verify_res = demo_session.put(
            f"{BASE_URL}/api/activities/{activity_id}/verify",
            json={"action": "approve", "verifier_notes": "Test approval"}
        )
        assert verify_res.status_code == 200, f"Expected 200, got {verify_res.status_code}: {verify_res.text}"
        updated = verify_res.json()
        assert updated['status'] == 'approved', f"Expected 'approved', got {updated['status']}"


# ─── Credits Tests ───

class TestCredits:
    """Credits lifecycle tests"""

    def test_list_credits(self, demo_session):
        """GET /api/credits - should return seeded credits"""
        res = demo_session.get(f"{BASE_URL}/api/credits")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) >= 4, f"Expected >=4 credits from seed data, got {len(data)}"

    def test_credits_have_all_statuses(self, demo_session):
        """Credits should have ISSUED/APPROVED/SOLD/RETIRED statuses"""
        res = demo_session.get(f"{BASE_URL}/api/credits")
        assert res.status_code == 200
        credits = res.json()
        statuses = {c['status'] for c in credits}
        expected_statuses = {'issued', 'approved', 'sold', 'retired'}
        assert statuses >= expected_statuses, f"Missing statuses. Expected {expected_statuses}, got {statuses}"

    def test_credits_summary_values(self, demo_session):
        """Credits totals should match expected values"""
        res = demo_session.get(f"{BASE_URL}/api/credits")
        assert res.status_code == 200
        credits = res.json()
        
        total_issued = sum(c['credits_issued'] for c in credits)
        total_approved = sum(c['credits_issued'] for c in credits if c['status'] == 'approved')
        total_sold = sum(c['credits_issued'] for c in credits if c['status'] == 'sold')
        total_retired = sum(c['credits_issued'] for c in credits if c['status'] == 'retired')
        
        # Expected seeded values: Total=65.1, Approved=24.3, Sold=18.75, Retired=9.45
        assert abs(total_issued - 65.1) < 1.0, f"Total issued: expected ~65.1, got {total_issued}"
        assert abs(total_approved - 24.3) < 1.0, f"Total approved: expected ~24.3, got {total_approved}"
        assert abs(total_sold - 18.75) < 1.0, f"Total sold: expected ~18.75, got {total_sold}"
        assert abs(total_retired - 9.45) < 1.0, f"Total retired: expected ~9.45, got {total_retired}"

    def test_credits_fields(self, demo_session):
        """Credits should have required fields"""
        res = demo_session.get(f"{BASE_URL}/api/credits")
        assert res.status_code == 200
        credits = res.json()
        required_fields = ['credit_id', 'project_id', 'project_name', 'registry_name',
                           'credits_issued', 'issuance_date', 'status']
        for credit in credits[:2]:
            for field in required_fields:
                assert field in credit, f"Missing field '{field}' in credit {credit.get('credit_id')}"

    def test_log_new_credit_issuance(self, demo_session):
        """POST /api/credits - should create new credit record"""
        # Get a project first
        projects_res = demo_session.get(f"{BASE_URL}/api/projects")
        assert projects_res.status_code == 200
        projects = projects_res.json()
        if not projects:
            pytest.skip("No projects available")
        
        payload = {
            "project_id": projects[0]['project_id'],
            "registry_name": "Other",
            "credits_issued": 5.0,
            "issuance_date": "2026-01-15",
            "vintage_year": 2026,
            "notes": "TEST audit credit"
        }
        res = demo_session.post(f"{BASE_URL}/api/credits", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        credit = res.json()
        assert credit['status'] == 'issued'
        assert credit['credits_issued'] == 5.0
        
        # Clean up
        credit_id = credit['credit_id']
        del_res = demo_session.delete(f"{BASE_URL}/api/credits/{credit_id}")
        assert del_res.status_code == 200, f"Failed to delete test credit: {del_res.status_code}"


# ─── Ledger Tests ───

class TestLedger:
    """Ledger endpoint tests"""

    def test_get_ledger(self, demo_session):
        """GET /api/ledger - should return ledger entries"""
        res = demo_session.get(f"{BASE_URL}/api/ledger")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert isinstance(data, list), "Expected list"

    def test_ledger_fields(self, demo_session):
        """Ledger entries should have required columns"""
        res = demo_session.get(f"{BASE_URL}/api/ledger")
        assert res.status_code == 200
        entries = res.json()
        if not entries:
            pytest.skip("No ledger entries to test with")
        required_fields = ['farmer_id', 'farmer_name', 'farmer_phone', 'project_id',
                           'approved_trees_total', 'approved_credits_total', 'payable_amount', 'paid_amount']
        for entry in entries[:3]:
            for field in required_fields:
                assert field in entry, f"Missing field '{field}' in ledger entry"


# ─── Export Tests ───

class TestExports:
    """Export endpoint tests"""

    def test_export_activity_csv(self, demo_session):
        """GET /api/export/activity-csv - should return CSV"""
        res = demo_session.get(f"{BASE_URL}/api/export/activity-csv")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'text/csv' in res.headers.get('Content-Type', ''), f"Expected CSV content type"

    def test_export_payout_csv(self, demo_session):
        """GET /api/export/payout-csv - should return CSV"""
        res = demo_session.get(f"{BASE_URL}/api/export/payout-csv")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'text/csv' in res.headers.get('Content-Type', ''), f"Expected CSV content type"

    def test_export_calculation_sheet(self, demo_session):
        """GET /api/export/calculation-sheet - should return CSV"""
        res = demo_session.get(f"{BASE_URL}/api/export/calculation-sheet")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'text/csv' in res.headers.get('Content-Type', ''), f"Expected CSV content type"

    def test_export_evidence_json(self, demo_session):
        """GET /api/export/evidence-json - should return JSON"""
        res = demo_session.get(f"{BASE_URL}/api/export/evidence-json")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'application/json' in res.headers.get('Content-Type', ''), f"Expected JSON content type"

    def test_export_audit_log(self, demo_session):
        """GET /api/export/audit-log - should return CSV"""
        res = demo_session.get(f"{BASE_URL}/api/export/audit-log")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'text/csv' in res.headers.get('Content-Type', ''), f"Expected CSV content type"

    def test_export_dossier_pdf(self, demo_session):
        """GET /api/export/dossier-pdf - should return PDF"""
        res = demo_session.get(f"{BASE_URL}/api/export/dossier-pdf")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert 'pdf' in res.headers.get('Content-Type', '').lower() or 'pdf' in res.headers.get('Content-Disposition', '').lower(), f"Expected PDF content"


# ─── Webhook Tests ───

class TestWebhooks:
    """Webhook endpoint tests"""

    def test_webhook_status(self, demo_session):
        """POST /api/webhook/status - should return farmer status"""
        # Get an existing farmer's phone
        res = demo_session.get(f"{BASE_URL}/api/farmers?page=1&page_size=1")
        assert res.status_code == 200
        farmers = res.json()
        if not farmers:
            pytest.skip("No farmers to test with")
        phone = farmers[0]['phone']
        
        # The webhook uses raw POST without auth
        res2 = requests.post(f"{BASE_URL}/api/webhook/status", json={"phone": phone})
        assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.text}"
        data = res2.json()
        assert data.get('success') is True
