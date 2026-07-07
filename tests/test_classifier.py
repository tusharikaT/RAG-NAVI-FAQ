import unittest
import sys
import os

# Add parent dir to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.classifier import classify_query

class TestClassifier(unittest.TestCase):
    def test_factual_queries(self):
        factual_queries = [
            "What is the expense ratio of Navi Nifty 50?",
            "What is the exit load for Navi ELSS?",
            "What is the minimum SIP amount for Navi Liquid Fund?",
            "ELSS lock-in period",
            "Riskometer of Navi Flexi Cap",
            "What is the benchmark index of Navi Nifty Bank?"
        ]
        for q in factual_queries:
            with self.subTest(query=q):
                self.assertEqual(classify_query(q), "FACTUAL")
                
    def test_advisory_queries(self):
        advisory_queries = [
            "Should I invest in Navi Flexi Cap?",
            "Which fund has better returns?",
            "Is Navi a safe AMC?",
            "Can you recommend a good fund for retirement?",
            "Is it worth it to buy Navi Nifty 50 now?",
            "Compare the returns of Navi Nifty 50 and Navi ELSS"
        ]
        for q in advisory_queries:
            with self.subTest(query=q):
                self.assertEqual(classify_query(q), "ADVISORY")

if __name__ == "__main__":
    unittest.main()
