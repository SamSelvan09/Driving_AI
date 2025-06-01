import requests
import unittest
import uuid
import json
import os
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://66ea233c-976f-4fbb-89e8-b49fbe61d6c4.preview.emergentagent.com"

class CarAssistantAPITest(unittest.TestCase):
    """Test suite for the AI Car Assistant API"""

    def setUp(self):
        """Set up test case - create a unique session ID for each test"""
        self.session_id = f"test_session_{uuid.uuid4()}"
        self.api_url = f"{BACKEND_URL}/api"
        print(f"\nUsing API URL: {self.api_url}")
        print(f"Test session ID: {self.session_id}")

    def test_01_health_check(self):
        """Test the API health check endpoint"""
        print("\n🔍 Testing API health check...")
        response = requests.get(f"{self.api_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "AI Car Assistant API")
        print("✅ API health check passed")

    def test_02_chat_functionality_parked(self):
        """Test the chat functionality with 'parked' status"""
        print("\n🔍 Testing chat functionality with 'parked' status...")
        payload = {
            "message": "What should I check before starting my car on a cold morning?",
            "session_id": self.session_id,
            "driving_status": "parked"
        }
        response = requests.post(f"{self.api_url}/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("session_id", data)
        self.assertIn("message_id", data)
        self.assertEqual(data["session_id"], self.session_id)
        print(f"✅ Chat response received: {data['response'][:50]}...")
        return data["message_id"]

    def test_03_chat_functionality_city_driving(self):
        """Test the chat functionality with 'city_driving' status"""
        print("\n🔍 Testing chat functionality with 'city_driving' status...")
        payload = {
            "message": "How can I improve my fuel efficiency?",
            "session_id": self.session_id,
            "driving_status": "city_driving"
        }
        response = requests.post(f"{self.api_url}/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("session_id", data)
        self.assertIn("message_id", data)
        self.assertEqual(data["session_id"], self.session_id)
        print(f"✅ Chat response received: {data['response'][:50]}...")
        return data["message_id"]

    def test_04_chat_functionality_highway(self):
        """Test the chat functionality with 'highway' status"""
        print("\n🔍 Testing chat functionality with 'highway' status...")
        payload = {
            "message": "What's the best way to use cruise control?",
            "session_id": self.session_id,
            "driving_status": "highway"
        }
        response = requests.post(f"{self.api_url}/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("session_id", data)
        self.assertIn("message_id", data)
        self.assertEqual(data["session_id"], self.session_id)
        print(f"✅ Chat response received: {data['response'][:50]}...")
        return data["message_id"]

    def test_05_chat_functionality_traffic(self):
        """Test the chat functionality with 'traffic' status"""
        print("\n🔍 Testing chat functionality with 'traffic' status...")
        payload = {
            "message": "How should I handle my car in stop-and-go traffic?",
            "session_id": self.session_id,
            "driving_status": "traffic"
        }
        response = requests.post(f"{self.api_url}/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("session_id", data)
        self.assertIn("message_id", data)
        self.assertEqual(data["session_id"], self.session_id)
        print(f"✅ Chat response received: {data['response'][:50]}...")
        return data["message_id"]

    def test_06_chat_history(self):
        """Test retrieving chat history for a session"""
        print("\n🔍 Testing chat history retrieval...")
        # First, send a few messages to create history
        self.test_02_chat_functionality_parked()
        self.test_03_chat_functionality_city_driving()
        
        # Then retrieve the history
        response = requests.get(f"{self.api_url}/chat/{self.session_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)  # Should have at least 2 messages
        
        # Verify the structure of each message
        for msg in data:
            self.assertIn("id", msg)
            self.assertIn("session_id", msg)
            self.assertIn("message", msg)
            self.assertIn("response", msg)
            self.assertIn("timestamp", msg)
            self.assertEqual(msg["session_id"], self.session_id)
        
        print(f"✅ Successfully retrieved {len(data)} messages from chat history")

    def test_07_status_check(self):
        """Test the status check endpoint"""
        print("\n🔍 Testing status check endpoint...")
        payload = {
            "client_name": f"test_client_{uuid.uuid4()}"
        }
        response = requests.post(f"{self.api_url}/status", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("client_name", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["client_name"], payload["client_name"])
        print("✅ Status check passed")

    def test_08_get_status_checks(self):
        """Test retrieving status checks"""
        print("\n🔍 Testing status checks retrieval...")
        # First, create a status check
        self.test_07_status_check()
        
        # Then retrieve all status checks
        response = requests.get(f"{self.api_url}/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)  # Should have at least 1 status check
        
        # Verify the structure of each status check
        for status in data:
            self.assertIn("id", status)
            self.assertIn("client_name", status)
            self.assertIn("timestamp", status)
        
        print(f"✅ Successfully retrieved {len(data)} status checks")

    def test_09_error_handling(self):
        """Test error handling with invalid requests"""
        print("\n🔍 Testing error handling...")
        
        # Test with invalid JSON
        response = requests.post(f"{self.api_url}/chat", data="invalid json")
        self.assertNotEqual(response.status_code, 200)
        print(f"✅ Invalid JSON handled with status code: {response.status_code}")
        
        # Test with missing required fields
        response = requests.post(f"{self.api_url}/chat", json={})
        self.assertNotEqual(response.status_code, 200)
        print(f"✅ Missing fields handled with status code: {response.status_code}")
        
        # Test with invalid session ID format
        response = requests.get(f"{self.api_url}/chat/invalid-session-id")
        # This might return 200 with empty list or 4xx error
        print(f"✅ Invalid session ID handled with status code: {response.status_code}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
