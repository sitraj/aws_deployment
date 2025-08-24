import unittest
import json
import os

# Set test environment variables BEFORE importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['APP_NAME'] = 'test-app'
os.environ['APP_VERSION'] = '1.0.0-test'
os.environ['HTTPS_ENABLED'] = 'false'

from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_hello_endpoint(self):
        """Test the hello endpoint"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test-app', response.data.decode('utf-8'))

    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'test-app')
        self.assertEqual(data['version'], '1.0.0-test')
        self.assertEqual(data['environment'], 'testing')
        self.assertIn('timestamp', data)

    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['uptime'], 'running')
        self.assertEqual(data['requests_processed'], 'tracked_in_logs')
        self.assertEqual(data['environment'], 'testing')
        self.assertEqual(data['version'], '1.0.0-test')
        self.assertIn('timestamp', data)

    def test_config_endpoint(self):
        """Test the config endpoint"""
        response = self.app.get('/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['app_name'], 'test-app')
        self.assertEqual(data['version'], '1.0.0-test')
        self.assertEqual(data['environment'], 'testing')
        self.assertIn('debug', data)
        self.assertIn('log_level', data)
        self.assertIn('health_check_enabled', data)
        self.assertIn('cors_enabled', data)
        self.assertIn('https_enabled', data)
        self.assertIn('force_https', data)
        self.assertIn('ssl_cert_path', data)
        self.assertIn('ssl_key_path', data)
        self.assertIn('timestamp', data)

    def test_security_headers_endpoint(self):
        """Test the security headers endpoint"""
        response = self.app.get('/security-headers')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Security headers are active')
        self.assertEqual(data['environment'], 'testing')
        self.assertIn('https_enabled', data)
        self.assertIn('force_https', data)
        self.assertIn('timestamp', data)

    def test_ssl_status_endpoint(self):
        """Test the SSL status endpoint"""
        response = self.app.get('/ssl-status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('https_enabled', data)
        self.assertIn('force_https', data)
        self.assertIn('certificate_path', data)
        self.assertIn('key_path', data)
        self.assertIn('certificate_exists', data)
        self.assertIn('key_exists', data)
        self.assertIn('timestamp', data)

    def test_force_https_test_endpoint(self):
        """Test the force HTTPS test endpoint"""
        response = self.app.get('/force-https-test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'This endpoint should only be accessible via HTTPS')
        self.assertIn('protocol', data)
        self.assertIn('https_enabled', data)
        self.assertIn('force_https', data)
        self.assertIn('timestamp', data)

    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        response = self.app.get('/health')
        
        # Check for common security headers
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        
        # In testing environment, frame options should be SAMEORIGIN
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')

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
            self.assertIn('environment', data)
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
            self.assertIn('environment', data)
            self.assertIn('version', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Metrics endpoint should return valid JSON")

    def test_config_endpoint_structure(self):
        """Test that config endpoint returns proper JSON structure"""
        response = self.app.get('/config')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('app_name', data)
            self.assertIn('version', data)
            self.assertIn('environment', data)
            self.assertIn('debug', data)
            self.assertIn('log_level', data)
            self.assertIn('health_check_enabled', data)
            self.assertIn('cors_enabled', data)
            self.assertIn('https_enabled', data)
            self.assertIn('force_https', data)
            self.assertIn('ssl_cert_path', data)
            self.assertIn('ssl_key_path', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Config endpoint should return valid JSON")

    def test_security_headers_endpoint_structure(self):
        """Test that security headers endpoint returns proper JSON structure"""
        response = self.app.get('/security-headers')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('message', data)
            self.assertIn('environment', data)
            self.assertIn('https_enabled', data)
            self.assertIn('force_https', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Security headers endpoint should return valid JSON")

    def test_ssl_status_endpoint_structure(self):
        """Test that SSL status endpoint returns proper JSON structure"""
        response = self.app.get('/ssl-status')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('https_enabled', data)
            self.assertIn('force_https', data)
            self.assertIn('certificate_path', data)
            self.assertIn('key_path', data)
            self.assertIn('certificate_exists', data)
            self.assertIn('key_exists', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("SSL status endpoint should return valid JSON")

    def test_force_https_test_endpoint_structure(self):
        """Test that force HTTPS test endpoint returns proper JSON structure"""
        response = self.app.get('/force-https-test')
        self.assertEqual(response.status_code, 200)
        
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
            self.assertIn('message', data)
            self.assertIn('protocol', data)
            self.assertIn('https_enabled', data)
            self.assertIn('force_https', data)
            self.assertIn('timestamp', data)
        except json.JSONDecodeError:
            self.fail("Force HTTPS test endpoint should return valid JSON")

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
        self.assertEqual(data1['environment'], data2['environment'])
        
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

    def test_https_configuration_in_testing(self):
        """Test that HTTPS is disabled in testing environment"""
        response = self.app.get('/config')
        data = json.loads(response.data)
        
        # In testing environment, HTTPS should be disabled
        self.assertFalse(data['https_enabled'])
        self.assertFalse(data['force_https'])

    def test_ssl_status_in_testing(self):
        """Test SSL status in testing environment"""
        response = self.app.get('/ssl-status')
        data = json.loads(response.data)
        
        # In testing environment, SSL should be disabled
        self.assertFalse(data['https_enabled'])
        self.assertFalse(data['force_https'])
        self.assertFalse(data['certificate_exists'])
        self.assertFalse(data['key_exists'])

    def test_force_https_in_testing(self):
        """Test force HTTPS in testing environment"""
        response = self.app.get('/force-https-test')
        data = json.loads(response.data)
        
        # In testing environment, HTTPS should be disabled
        self.assertFalse(data['https_enabled'])
        self.assertFalse(data['force_https'])

if __name__ == '__main__':
    unittest.main()
