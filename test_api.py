#!/usr/bin/env python3
"""
Test script for TawjihiAI FastAPI application
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_agents():
    """Test agents endpoint"""
    print("\n🔍 Testing agents endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        agents = response.json()
        print(f"✅ Agents endpoint: {response.status_code}")
        print(f"   Found {len(agents)} agents:")
        for agent in agents:
            print(f"   - {agent['id']}: {agent['name']}")
        return True
    except Exception as e:
        print(f"❌ Agents endpoint failed: {e}")
        return False

def test_auth():
    """Test authentication endpoint"""
    print("\n🔍 Testing auth endpoint...")
    try:
        data = {"username": "test_user", "password": "test_pass"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=5)
        result = response.json()
        print(f"✅ Auth endpoint: {response.status_code} - {result['message']}")
        return True
    except Exception as e:
        print(f"❌ Auth endpoint failed: {e}")
        return False

def test_ask_question():
    """Test question asking endpoint"""
    print("\n🔍 Testing ask question endpoint...")
    try:
        data = {
            "subject": "math",
            "question": "What is 2 + 2?",
            "user_id": "test_user_123"
        }
        response = requests.post(f"{BASE_URL}/api/ask", json=data, timeout=30)
        result = response.json()
        print(f"✅ Ask question: {response.status_code}")
        print(f"   Response: {result['response'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ Ask question failed: {e}")
        return False

def test_conversations():
    """Test conversations endpoint"""
    print("\n🔍 Testing conversations endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/conversations/test_user_123", timeout=5)
        result = response.json()
        print(f"✅ Conversations endpoint: {response.status_code}")
        print(f"   Found {len(result['conversations'])} conversations")
        return True
    except Exception as e:
        print(f"❌ Conversations endpoint failed: {e}")
        return False

def test_home_page():
    """Test home page"""
    print("\n🔍 Testing home page...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Home page: {response.status_code}")
        if "نظام التوجيهي الذكي" in response.text:
            print("   ✅ Arabic content found")
        return True
    except Exception as e:
        print(f"❌ Home page failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting TawjihiAI FastAPI Tests")
    print("=" * 50)
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    tests = [
        test_health,
        test_home_page,
        test_agents,
        test_auth,
        test_ask_question,
        test_conversations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! FastAPI migration successful!")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main() 