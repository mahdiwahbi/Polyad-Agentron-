import unittest
from polyad import Polyad
from resource_manager import ResourceManager

class TestPolyad(unittest.TestCase):
    def setUp(self):
        self.agent = Polyad()
        
    def test_model_selection(self):
        model = self.agent.resource_manager.get_optimal_model()
        self.assertIn(model, ["gemma3:12b-q4_0", "gemma3:12b-q2_K"])
        
    def test_parallel_processing(self):
        result = self.agent.run("Test parallel processing")
        self.assertIsNotNone(result)
        
    def test_error_handling(self):
        with self.assertRaises(Exception):
            self.agent.run("" * 1000)  # Should trigger error

if __name__ == '__main__':
    unittest.main()
