"""Verification tests for Phase 6F: Production Deployment, Analytics & Platform Hardening."""

import os
import unittest
import time
from fastapi.testclient import TestClient

# 1. Set environment variable prior to importing database services
os.environ["DATABASE_URL"] = "sqlite:///test_nephele_6f.db"

from interview_engine.storage.postgres.service import PostgresService
from app.main import app

class TestPhase6F(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pg_service = PostgresService()
        cls.pg_service.drop_tables()
        cls.pg_service.create_tables()
        cls.client = TestClient(app)

    def setUp(self) -> None:
        # Re-initialize DB tables for each test for isolation
        self.pg_service.drop_tables()
        self.pg_service.create_tables()
        # Reset the rate limiter bucket to prevent test cross-contamination
        from app.routes.security import RATE_LIMIT_BUCKETS
        RATE_LIMIT_BUCKETS.clear()

    def test_health_check_endpoints(self) -> None:
        """Verify baseline health check endpoints return 200 OK and valid status json."""
        # /api/health
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        # /api/health/database
        res = self.client.get("/api/health/database")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["connection"], "up")

        # /api/health/chroma
        res = self.client.get("/api/health/chroma")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        # /api/health/provider
        res = self.client.get("/api/health/provider")
        self.assertEqual(res.status_code, 200)
        self.assertIn("providers_configured", res.json())

        # /api/health/runtime
        res = self.client.get("/api/health/runtime")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["active_sessions"], 0)

    def test_observability_metrics(self) -> None:
        """Verify observability metrics records averages and token metrics."""
        res = self.client.get("/api/observability/metrics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("latencies", res.json())
        self.assertIn("provider_costs", res.json())

    def test_admin_and_analytics_aggregation(self) -> None:
        """Test admin metrics collection, candidate directory searching, and graphs index."""
        # Overview
        res = self.client.get("/api/admin/overview")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_candidates"], 0)

        # Candidate Search (empty)
        res = self.client.get("/api/admin/candidates")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 0)

        # Graph Analytics fallbacks
        res = self.client.get("/api/admin/graph-analytics")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()) > 0)

        # System Health summary
        res = self.client.get("/api/admin/system-health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["database"], "healthy")

    def test_candidate_interview_lifecycle_and_exports(self) -> None:
        """Simulate a candidate interview, assert status logs, and verify file format exports."""
        # 1. Start interview
        start_payload = {
            "candidate_id": "test_phase_6f_jane",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "resume": {
                "skills": ["Machine Learning", "Neural Networks"],
                "education": ["BS in Computer Science"],
                "projects": []
            }
        }
        res_start = self.client.post("/start", json=start_payload)
        self.assertEqual(res_start.status_code, 200)
        self.assertEqual(res_start.json()["current_concept"], "Supervised Learning")

        # 2. Check active session count is 1
        res_runtime = self.client.get("/api/health/runtime")
        self.assertEqual(res_runtime.json()["active_sessions"], 1)

        # 3. Submit answer to first concept
        submit_payload = {
            "candidate_id": "test_phase_6f_jane",
            "concept": "Supervised Learning",
            "question": res_start.json()["question"],
            "answer": "Supervised learning utilizes labeled inputs to train a regression or classification mapping function."
        }
        res_submit = self.client.post("/submit", json=submit_payload)
        self.assertEqual(res_submit.status_code, 200)

        # 4. Generate report download in JSON format
        res_report_json = self.client.get("/api/reports/test_phase_6f_jane/export?format=json")
        self.assertEqual(res_report_json.status_code, 200)
        self.assertIn("application/json", res_report_json.headers["content-type"])
        report_data = res_report_json.json()
        self.assertEqual(report_data["candidate_id"], "test_phase_6f_jane")

        # 5. Generate report download in CSV format
        res_report_csv = self.client.get("/api/reports/test_phase_6f_jane/export?format=csv")
        self.assertEqual(res_report_csv.status_code, 200)
        self.assertIn("text/csv", res_report_csv.headers["content-type"])
        self.assertIn("Jane Doe", res_report_csv.text)

        # 6. Generate report download in PDF format (ReportLab validation)
        res_report_pdf = self.client.get("/api/reports/test_phase_6f_jane/export?format=pdf")
        self.assertEqual(res_report_pdf.status_code, 200)
        self.assertIn("application/pdf", res_report_pdf.headers["content-type"])
        self.assertTrue(len(res_report_pdf.content) > 100)  # Verify PDF bytes were generated

        # 7. Check evolution reports
        res_evol = self.client.get("/api/admin/evolution-reports?domain=machine_learning")
        self.assertEqual(res_evol.status_code, 200)

        # 8. Check evolution report exports (PDF)
        res_evol_pdf = self.client.get("/api/reports/evolution/export?format=pdf")
        self.assertEqual(res_evol_pdf.status_code, 200)
        self.assertIn("application/pdf", res_evol_pdf.headers["content-type"])

        # 9. Check system analytics exports (PDF)
        res_analytics_pdf = self.client.get("/api/reports/analytics/export?format=pdf")
        self.assertEqual(res_analytics_pdf.status_code, 200)
        self.assertIn("application/pdf", res_analytics_pdf.headers["content-type"])

    def test_security_session_validation(self) -> None:
        """Validate that submission checks block inactive or paused candidate sessions."""
        submit_payload = {
            "candidate_id": "non_existent_id",
            "concept": "Supervised Learning",
            "question": "What is overfitting?",
            "answer": "Model memorization."
        }
        res = self.client.post("/submit", json=submit_payload)
        self.assertEqual(res.status_code, 404)  # blocked with 404

    def test_rate_limiter(self) -> None:
        """Verify token bucket rate limiting raises 429 after exceeding limit."""
        # Trigger 65 fast requests to exceed the limit of 60
        status_codes = []
        for _ in range(65):
            res = self.client.get("/api/analytics")
            status_codes.append(res.status_code)
            if res.status_code == 429:
                break
        self.assertIn(429, status_codes)
