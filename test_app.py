import unittest
import json
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_hello_endpoint(self):
        """Test the hello endpoint"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'Hello, World!!!')

    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'flask-app')
        self.assertEqual(data['version'], '1.0.0')
        self.assertIn('timestamp', data)

    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['uptime'], 'running')
        self.assertEqual(data['requests_processed'], 'tracked_in_logs')
        self.assertIn('timestamp', data)

    def test_nonexistent_endpoint(self):
        """Test 404 for non-existent endpoint"""
        response = self.app.get('/nonexistent')
        # Flask test client returns 404 for non-existent routes
        self.assertEqual(response.status_code, 404)

    def test_health_endpoint_structure(self):
        """Test that health endpoint returns proper JSON structure"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('status', data)
            self.assertIn('service', data)
            self.assertIn('version', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Health endpoint should return valid JSON")

if __name__ == '__main__':
    unittest.main()
