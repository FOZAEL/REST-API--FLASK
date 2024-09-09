import unittest
from unittest.mock import patch, MagicMock
import json
from app import app

class AppTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_root(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)
        self.assertIn('date', data)
        self.assertIn('kubernetes', data)

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'OK')

    # @patch('app.dns_lookup')
    # def test_lookup_valid_domain(self, mock_dns_lookup):
    #     mock_dns_lookup.return_value = (['93.184.216.34'], 0.123)
        
    #     response = self.client.get('/v1/tools/lookup?domain=example.com')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertIn('addresses', data)
    #     self.assertEqual(data['domain'], 'example.com')
    #     self.assertEqual(data['addresses'][0]['ip'], '93.184.216.34')

    # def test_lookup_invalid_domain(self):
    #     response = self.client.get('/v1/tools/lookup?domain=invalid-domain')
    #     self.assertEqual(response.status_code, 400)
    #     data = json.loads(response.data)
    #     self.assertEqual(data['message'], 'Domain parameter is Not Valid or Provided')

    # @patch('app.dns_lookup')
    # def test_lookup_non_existent_domain(self, mock_dns_lookup):
    #     mock_dns_lookup.return_value = ([], None)
        
    #     response = self.client.get('/v1/tools/lookup?domain=nonexistentdomain.xyz')
    #     self.assertEqual(response.status_code, 404)
    #     data = json.loads(response.data)
    #     self.assertEqual(data['message'], 'The Host IP Not Found')

    def test_validate_valid_ip(self):
        response = self.client.post('/v1/tools/validate', json={"ip": "192.168.0.1"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['ip'], 'is a Valid IP V4')

    def test_validate_invalid_ip(self):
        response = self.client.post('/v1/tools/validate', json={"ip": "999.999.999.999"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['ip'], 'is NOT a Valid ipV4')

    # @patch('app.DomainLookup.query')
    # def test_history_no_queries(self, mock_query):
    #     mock_query.order_by().limit().all.return_value = []
        
    #     response = self.client.get('/v1/history')
    #     self.assertEqual(response.status_code, 400)
    #     data = json.loads(response.data)
    #     self.assertEqual(data['message'], 'Database is empty, do some query first')

if __name__ == '__main__':
    unittest.main()
