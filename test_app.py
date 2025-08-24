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
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['status_code'], 404)
        self.assertIn('error', data)

    def test_method_not_allowed(self):
        """Test 405 for unsupported HTTP method"""
        # Try POST to GET-only endpoint
        response = self.app.post('/health')
        self.assertEqual(response.status_code, 405)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['status_code'], 405)
        self.assertIn('error', data)

    def test_put_method_not_allowed(self):
        """Test 405 for PUT method"""
        response = self.app.put('/metrics')
        self.assertEqual(response.status_code, 405)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['status_code'], 405)

    def test_delete_method_not_allowed(self):
        """Test 405 for DELETE method"""
        response = self.app.delete('/')
        self.assertEqual(response.status_code, 405)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['status_code'], 405)

    def test_head_method(self):
        """Test HEAD method (should work for GET endpoints)"""
        response = self.app.head('/health')
        self.assertEqual(response.status_code, 200)
        # HEAD responses typically have no body
        self.assertEqual(response.data, b'')

    def test_options_method(self):
        """Test OPTIONS method"""
        response = self.app.options('/health')
        self.assertEqual(response.status_code, 200)

    def test_different_nonexistent_paths(self):
        """Test various non-existent paths return 404"""
        paths = ['/api', '/admin', '/user/123', '/v1/health', '/api/v1/users']
        for path in paths:
            with self.subTest(path=path):
                response = self.app.get(path)
                self.assertEqual(response.status_code, 404)
                data = json.loads(response.data)
                self.assertEqual(data['status_code'], 404)

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

    def test_metrics_endpoint_structure(self):
        """Test that metrics endpoint returns proper JSON structure"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('uptime', data)
            self.assertIn('requests_processed', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Metrics endpoint should return valid JSON")

    def test_error_response_structure(self):
        """Test that error responses have consistent structure"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('status', data)
        self.assertIn('status_code', data)
        self.assertEqual(data['status'], 'error')

    def test_content_type_headers(self):
        """Test that responses have correct content type headers"""
        # Test JSON endpoints
        response = self.app.get('/health')
        self.assertIn('application/json', response.headers.get('Content-Type', ''))
        
        # Test text endpoint
        response = self.app.get('/')
        self.assertIn('text/html', response.headers.get('Content-Type', ''))

    def test_response_consistency(self):
        """Test that multiple requests to same endpoint return consistent responses"""
        # Test health endpoint consistency
        response1 = self.app.get('/health')
        response2 = self.app.get('/health')
        
        self.assertEqual(response1.status_code, response2.status_code)
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Static fields should be identical
        self.assertEqual(data1['status'], data2['status'])
        self.assertEqual(data1['service'], data2['service'])
        self.assertEqual(data1['version'], data2['version'])
        
        # Timestamp should be different (unless requests are very fast)
        self.assertIn('timestamp', data1)
        self.assertIn('timestamp', data2)

    def test_empty_path(self):
        """Test root path handling"""
        response = self.app.get('')
        # Flask redirects empty path to / with 308 status
        self.assertEqual(response.status_code, 308)

    def test_slash_path(self):
        """Test slash path handling"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
