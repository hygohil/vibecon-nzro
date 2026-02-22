#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class VanaLedgerAPITester:
    def __init__(self, base_url: str, session_token: str):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = session_token
        self.tests_run = 0
        self.tests_passed = 0
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {session_token}'
        }
        
        # Store created IDs for cleanup and further testing
        self.created_program_id = None
        self.created_farmer_id = None
        self.created_claim_id = None

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        self.tests_run += 1
        
        self.log(f"Testing {name}...")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                self.log(f"❌ Unsupported method: {method}", "ERROR")
                return False, {}

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}", "ERROR")
                except:
                    self.log(f"   Response text: {response.text[:200]}", "ERROR")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}", "ERROR")
            return False, {}

    def test_auth_endpoints(self) -> bool:
        """Test authentication endpoints"""
        self.log("=== AUTHENTICATION TESTS ===")
        
        # Test /auth/me endpoint
        success, user_data = self.run_test(
            "Auth - Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        if success and user_data:
            self.log(f"   User: {user_data.get('name', 'N/A')} ({user_data.get('email', 'N/A')})")
        
        return success

    def test_programs_crud(self) -> bool:
        """Test Programs CRUD operations"""
        self.log("=== PROGRAMS TESTS ===")
        
        # Test GET programs (empty initially)
        success, programs = self.run_test(
            "Programs - List Programs",
            "GET", 
            "programs",
            200
        )
        
        if success:
            self.log(f"   Found {len(programs)} existing programs")
        
        # Test CREATE program
        program_data = {
            "name": "Test Carbon Program",
            "region": "Gujarat, Saurashtra",
            "description": "Test program for API validation",
            "species_list": [
                {"name": "Neem", "growth_rate": "medium"},
                {"name": "Eucalyptus", "growth_rate": "fast_growing"}
            ],
            "payout_rule_type": "per_tree",
            "payout_rate": 60.0,
            "survival_rate": 0.75,
            "conservative_discount": 0.15,
            "max_trees_per_acre": 350,
            "cooldown_days": 30,
            "required_proofs": ["location", "photo"],
            "monitoring_frequency_days": 90
        }
        
        success, created_program = self.run_test(
            "Programs - Create Program",
            "POST",
            "programs",
            200,
            program_data
        )
        
        if success and created_program:
            self.created_program_id = created_program.get("program_id")
            self.log(f"   Created program ID: {self.created_program_id}")
        
        # Test GET single program
        if self.created_program_id:
            success, program = self.run_test(
                "Programs - Get Single Program",
                "GET",
                f"programs/{self.created_program_id}",
                200
            )
            
            if success and program:
                self.log(f"   Program name: {program.get('name')}")
                self.log(f"   Program region: {program.get('region')}")
        
        return bool(self.created_program_id)

    def test_farmers_crud(self) -> bool:
        """Test Farmers CRUD operations"""
        self.log("=== FARMERS TESTS ===")
        
        if not self.created_program_id:
            self.log("❌ Cannot test farmers - no program created", "ERROR")
            return False
        
        # Test LIST farmers
        success, farmers = self.run_test(
            "Farmers - List Farmers",
            "GET",
            "farmers",
            200
        )
        
        if success:
            self.log(f"   Found {len(farmers)} existing farmers")
        
        # Test CREATE farmer
        farmer_data = {
            "name": "Ramesh Kumar",
            "phone": "+919876543210",
            "village": "Vadodara",
            "district": "Vadodara",
            "land_type": "owned",
            "acres": 2.5,
            "upi_id": "ramesh@paytm",
            "program_id": self.created_program_id
        }
        
        success, created_farmer = self.run_test(
            "Farmers - Create Farmer",
            "POST",
            "farmers",
            200,
            farmer_data
        )
        
        if success and created_farmer:
            self.created_farmer_id = created_farmer.get("farmer_id")
            self.log(f"   Created farmer ID: {self.created_farmer_id}")
        
        # Test GET single farmer
        if self.created_farmer_id:
            success, farmer = self.run_test(
                "Farmers - Get Single Farmer",
                "GET",
                f"farmers/{self.created_farmer_id}",
                200
            )
            
            if success and farmer:
                self.log(f"   Farmer name: {farmer.get('name')}")
                self.log(f"   Farmer phone: {farmer.get('phone')}")
        
        return bool(self.created_farmer_id)

    def test_claims_crud(self) -> bool:
        """Test Claims CRUD operations"""
        self.log("=== CLAIMS TESTS ===")
        
        if not self.created_program_id or not self.created_farmer_id:
            self.log("❌ Cannot test claims - missing program or farmer", "ERROR")
            return False
        
        # Test LIST claims
        success, claims = self.run_test(
            "Claims - List Claims",
            "GET",
            "claims",
            200
        )
        
        if success:
            self.log(f"   Found {len(claims)} existing claims")
        
        # Test CREATE claim
        claim_data = {
            "farmer_id": self.created_farmer_id,
            "program_id": self.created_program_id,
            "tree_count": 150,
            "species": "Neem",
            "planted_date": "2024-01-15",
            "lat": 21.1702,
            "lng": 72.8311,
            "photo_urls": [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg"
            ],
            "notes": "First batch of saplings planted near the well"
        }
        
        success, created_claim = self.run_test(
            "Claims - Create Claim",
            "POST",
            "claims",
            200,
            claim_data
        )
        
        if success and created_claim:
            self.created_claim_id = created_claim.get("claim_id")
            self.log(f"   Created claim ID: {self.created_claim_id}")
            self.log(f"   Estimated credits: {created_claim.get('estimated_credits')} tCO2e")
            self.log(f"   Estimated payout: ₹{created_claim.get('estimated_payout')}")
        
        return bool(self.created_claim_id)

    def test_claim_actions(self) -> bool:
        """Test claim approval/rejection"""
        self.log("=== CLAIM ACTIONS TESTS ===")
        
        if not self.created_claim_id:
            self.log("❌ Cannot test claim actions - no claim created", "ERROR")
            return False
        
        # Test APPROVE claim
        approve_data = {
            "action": "approve",
            "verifier_notes": "Verified through satellite imagery and field visit"
        }
        
        success, updated_claim = self.run_test(
            "Claims - Approve Claim",
            "PUT",
            f"claims/{self.created_claim_id}/action",
            200,
            approve_data
        )
        
        if success and updated_claim:
            self.log(f"   Claim status: {updated_claim.get('status')}")
            self.log(f"   Approved at: {updated_claim.get('approved_at')}")
        
        return success

    def test_ledger_endpoints(self) -> bool:
        """Test ledger endpoints"""
        self.log("=== LEDGER TESTS ===")
        
        # Test GET ledger
        success, ledger = self.run_test(
            "Ledger - Get Ledger",
            "GET",
            "ledger",
            200
        )
        
        if success and ledger:
            self.log(f"   Found {len(ledger)} ledger entries")
            if ledger:
                entry = ledger[0]
                self.log(f"   Sample entry - Farmer: {entry.get('farmer_name')}, Payable: ₹{entry.get('payable_amount', 0)}")
        
        return success

    def test_dashboard_stats(self) -> bool:
        """Test dashboard stats"""
        self.log("=== DASHBOARD TESTS ===")
        
        success, stats = self.run_test(
            "Dashboard - Get Stats",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success and stats:
            self.log(f"   Programs: {stats.get('total_programs', 0)}")
            self.log(f"   Farmers: {stats.get('total_farmers', 0)}")
            self.log(f"   Claims: {stats.get('total_claims', 0)}")
            self.log(f"   Approved Trees: {stats.get('approved_trees', 0)}")
            self.log(f"   Estimated Credits: {stats.get('estimated_credits', 0)} tCO2e")
        
        return success

    def test_export_endpoints(self) -> bool:
        """Test export endpoints"""
        self.log("=== EXPORT TESTS ===")
        
        endpoints = [
            "export/activity-csv",
            "export/payout-csv", 
            "export/calculation-sheet",
            "export/dossier-pdf",
            "export/evidence-json",
            "export/audit-log"
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            try:
                url = f"{self.api_url}/{endpoint}"
                response = requests.get(url, headers=self.headers)
                
                # For exports, we expect 200 and streaming response
                if response.status_code == 200:
                    self.tests_passed += 1
                    self.log(f"✅ Export - {endpoint}")
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    self.log(f"   Content-Type: {content_type}")
                else:
                    self.log(f"❌ Export - {endpoint} - Status: {response.status_code}", "ERROR")
                    all_passed = False
                    
                self.tests_run += 1
                    
            except Exception as e:
                self.log(f"❌ Export - {endpoint} - Error: {str(e)}", "ERROR")
                self.tests_run += 1
                all_passed = False
        
        return all_passed

    def test_webhook_endpoints(self) -> bool:
        """Test WhatsApp webhook endpoints"""
        self.log("=== WEBHOOK TESTS ===")
        
        if not self.created_program_id:
            self.log("❌ Cannot test webhooks - no program created", "ERROR")
            return False
        
        # Test JOIN webhook
        join_data = {
            "phone": "+919876543211",
            "name": "WhatsApp Test Farmer",
            "village": "Test Village",
            "district": "Test District", 
            "land_type": "owned",
            "acres": 1.5,
            "upi_id": "test@upi",
            "program_id": self.created_program_id
        }
        
        success, join_response = self.run_test(
            "Webhook - Join Farmer",
            "POST",
            "webhook/join", 
            200,
            join_data
        )
        
        webhook_farmer_id = None
        if success and join_response:
            webhook_farmer_id = join_response.get("farmer_id")
            self.log(f"   Join success: {join_response.get('success')}")
            self.log(f"   Message: {join_response.get('message')}")
        
        # Test CLAIM webhook
        if webhook_farmer_id:
            claim_data = {
                "phone": "+919876543211",
                "program_id": self.created_program_id,
                "tree_count": 75,
                "species": "Mango",
                "planted_date": "2024-01-20",
                "lat": 22.1234,
                "lng": 73.5678,
                "photo_urls": ["https://example.com/webhook_photo.jpg"]
            }
            
            success, claim_response = self.run_test(
                "Webhook - Submit Claim",
                "POST",
                "webhook/claim",
                200,
                claim_data
            )
            
            if success and claim_response:
                self.log(f"   Claim success: {claim_response.get('success')}")
                self.log(f"   Claim ID: {claim_response.get('claim_id')}")
                self.log(f"   Estimated payout: ₹{claim_response.get('estimated_payout', 0)}")
        
        # Test STATUS webhook
        status_data = {
            "phone": "+919876543211"
        }
        
        success, status_response = self.run_test(
            "Webhook - Check Status", 
            "POST",
            "webhook/status",
            200,
            status_data
        )
        
        if success and status_response:
            self.log(f"   Status success: {status_response.get('success')}")
            self.log(f"   Farmer: {status_response.get('farmer_name')}")
            self.log(f"   Total trees: {status_response.get('total_trees', 0)}")
        
        return True

    def run_all_tests(self) -> bool:
        """Run all API tests"""
        self.log("🚀 Starting VanaLedger API Tests")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Session Token: {self.session_token[:20]}...")
        
        test_results = []
        
        # Run all test suites
        test_results.append(self.test_auth_endpoints())
        test_results.append(self.test_programs_crud())
        test_results.append(self.test_farmers_crud())
        test_results.append(self.test_claims_crud())
        test_results.append(self.test_claim_actions())
        test_results.append(self.test_ledger_endpoints())
        test_results.append(self.test_dashboard_stats())
        test_results.append(self.test_export_endpoints())
        test_results.append(self.test_webhook_endpoints())
        
        # Print summary
        self.log("=" * 50)
        self.log(f"📊 TEST SUMMARY")
        self.log(f"Tests Passed: {self.tests_passed}/{self.tests_run}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        overall_success = all(test_results)
        if overall_success:
            self.log("🎉 ALL TESTS PASSED!")
        else:
            self.log("❌ SOME TESTS FAILED")
            failed_suites = [i for i, result in enumerate(test_results) if not result]
            self.log(f"Failed test suites: {failed_suites}")
        
        return overall_success

def main():
    # Configuration
    BACKEND_URL = "https://add-farmer-ux.preview.emergentagent.com"
    SESSION_TOKEN = "test_session_1771669663710"  # Using the token we just created
    
    # Initialize tester
    tester = VanaLedgerAPITester(BACKEND_URL, SESSION_TOKEN)
    
    # Run tests
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())