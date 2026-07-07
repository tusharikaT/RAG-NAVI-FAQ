import unittest
import sys
import os
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api import app

class TestRAGPipelineIntegration(unittest.TestCase):
    """
    Phase 8: Testing & Validation
    Runs complete integration tests against the RAG pipeline using the FastAPI TestClient.
    This tests the entire flow: API -> Router -> Classifier -> Retriever -> Prompt -> LLM -> Formatter
    """
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def verify_response_format(self, data):
        """Helper to verify Step 8.3 constraints (formatting)."""
        self.assertIn("answer", data)
        self.assertIn("citation", data)
        self.assertIn("footer", data)
        self.assertIn("disclaimer", data)
        
        # Max 3 sentences check. (Very roughly check for period/sentence boundaries)
        # Note: the LLM sometimes uses abbreviations like 'Rs.', 'Ltd.', so this is a heuristic.
        sentences = [s for s in data["answer"].replace("?", ".").replace("!", ".").split(". ") if s.strip()]
        self.assertLessEqual(len(sentences), 4, f"Answer should be <= 3 sentences. Got: {len(sentences)}")
        
        # Exactly one source URL check.
        self.assertTrue(data["citation"].startswith("http"), "Citation must be a valid URL")
        
        # No HTTP links inside the main answer body (regex stripper test)
        self.assertNotIn("http", data["answer"], "URLs should be stripped from the answer body")
        
        # Static footers and disclaimers
        self.assertTrue(data["footer"].startswith("Last updated from sources:"), "Footer missing required text")
        self.assertEqual(data["disclaimer"], "Facts-only. No investment advice.")

    # --- Step 8.1 Factual Query Tests ---
    
    def test_factual_q1_expense_ratio(self):
        res = self.client.post("/api/v1/query", json={"query": "What is the expense ratio of Navi Nifty 50?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q2_exit_load(self):
        res = self.client.post("/api/v1/query", json={"query": "What is the exit load for Navi ELSS?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q3_minimum_sip(self):
        res = self.client.post("/api/v1/query", json={"query": "Minimum SIP amount for Navi Liquid Fund?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q4_elss_lock_in(self):
        res = self.client.post("/api/v1/query", json={"query": "What is the ELSS lock-in period?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q5_riskometer(self):
        res = self.client.post("/api/v1/query", json={"query": "What is the Riskometer of Navi Flexi Cap?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q6_benchmark_index(self):
        res = self.client.post("/api/v1/query", json={"query": "Benchmark index of Navi Nifty Bank?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    def test_factual_q7_capital_gains(self):
        res = self.client.post("/api/v1/query", json={"query": "How to download capital gains report?"})
        self.assertEqual(res.status_code, 200)
        self.verify_response_format(res.json())

    # --- Step 8.2 Refusal Query Tests ---

    def verify_refusal_format(self, data):
        self.assertIn("This assistant provides factual information only", data["answer"])
        self.assertIn("educational_link", data)
        self.assertEqual(data["disclaimer"], "Facts-only. No investment advice.")
        
    def test_refusal_q1_advisory(self):
        res = self.client.post("/api/v1/query", json={"query": "Should I invest in Navi Flexi Cap?"})
        self.assertEqual(res.status_code, 200)
        self.verify_refusal_format(res.json())

    def test_refusal_q2_comparison(self):
        res = self.client.post("/api/v1/query", json={"query": "Which fund has better returns?"})
        self.assertEqual(res.status_code, 200)
        self.verify_refusal_format(res.json())

    def test_refusal_q3_opinion(self):
        res = self.client.post("/api/v1/query", json={"query": "Is Navi a safe AMC?"})
        self.assertEqual(res.status_code, 200)
        self.verify_refusal_format(res.json())


if __name__ == "__main__":
    unittest.main()
