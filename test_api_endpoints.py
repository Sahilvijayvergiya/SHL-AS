import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health endpoint."""
    print("\n--- Testing GET /health ---")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✓ Health endpoint accessible")
        return True
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False

def test_chat_endpoint():
    """Test chat endpoint."""
    print("\n--- Testing POST /chat ---")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Reply: {data['reply'][:100]}...")
        assert response.status_code == 200
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        print("✓ Chat endpoint accessible")
        return True
    except Exception as e:
        print(f"✗ Chat endpoint failed: {e}")
        return False

def test_response_time():
    """Test response time is under 30 seconds."""
    print("\n--- Testing Response Time ---")
    try:
        import time
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"messages": [{"role": "user", "content": "I need a Java developer assessment"}]},
            timeout=30
        )
        elapsed = time.time() - start
        print(f"Response time: {elapsed:.2f} seconds")
        assert elapsed < 30, "Response time exceeds 30 second limit"
        print("✓ Response time within 30 second limit")
        return True
    except Exception as e:
        print(f"✗ Response time test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing API Endpoint Accessibility")
    print("=" * 60)
    
    health_ok = test_health_endpoint()
    chat_ok = test_chat_endpoint()
    time_ok = test_response_time()
    
    print("\n" + "=" * 60)
    if health_ok and chat_ok and time_ok:
        print("✓ All API endpoints accessible and functional")
    else:
        print("✗ Some endpoints failed")
    print("=" * 60)
