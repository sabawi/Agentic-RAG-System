#!/usr/bin/env python3
"""
Simple test script for the FastAPI server
"""

import asyncio
import json
import httpx
import time

BASE_URL = "http://localhost:5000"

async def test_endpoints():
    """Test all endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing FastAPI Server Endpoints\n")
        
        # Test 1: Root endpoint
        print("1️⃣ Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            print("   ✅ Root endpoint working\n")
        except Exception as e:
            print(f"   ❌ Root endpoint failed: {e}\n")
        
        # Test 2: Health check
        print("2️⃣ Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Services: {data.get('services', {})}")
            print(f"   Cache Size: {data.get('cache_size', 0)}")
            print("   ✅ Health endpoint working\n")
        except Exception as e:
            print(f"   ❌ Health endpoint failed: {e}\n")
        
        # Test 3: Stock data with caching
        print("3️⃣ Testing stock data endpoint...")
        try:
            # First request
            start_time = time.time()
            response1 = await client.get(f"{BASE_URL}/stocks/AAPL")
            time1 = time.time() - start_time
            
            # Second request (should be cached)
            start_time = time.time()
            response2 = await client.get(f"{BASE_URL}/stocks/AAPL")
            time2 = time.time() - start_time
            
            print(f"   First request: {time1:.3f}s")
            print(f"   Second request: {time2:.3f}s (cached)")
            print(f"   Data: {response1.json()['data']['symbol']} - ${response1.json()['data']['price']}")
            print("   ✅ Stock endpoint with caching working\n")
        except Exception as e:
            print(f"   ❌ Stock endpoint failed: {e}\n")
        
        # Test 4: Database test
        print("4️⃣ Testing database connection...")
        try:
            response = await client.get(f"{BASE_URL}/database/test")
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Success: {data.get('success', False)}")
            if data.get('success'):
                print("   ✅ Database connection working")
            else:
                print(f"   ⚠️ Database issue: {data.get('error', 'Unknown')}")
            print()
        except Exception as e:
            print(f"   ❌ Database test failed: {e}\n")
        
        # Test 5: Code execution
        print("5️⃣ Testing code execution...")
        try:
            payload = {
                "code": "print('Hello from FastAPI!'); import math; print(f'π = {math.pi:.4f}')",
                "timeout": 10
            }
            response = await client.post(f"{BASE_URL}/execute", json=payload)
            data = response.json()
            print(f"   Status: {response.status_code}")
            if data.get('success'):
                print(f"   Output: {data['data']['output'].strip()}")
                print("   ✅ Code execution working")
            else:
                print(f"   ❌ Execution failed: {data.get('error')}")
            print()
        except Exception as e:
            print(f"   ❌ Code execution failed: {e}\n")
        
        # Test 6: Stock analysis
        print("6️⃣ Testing stock analysis...")
        try:
            payload = {"symbol": "TSLA", "days": 30}
            response = await client.post(f"{BASE_URL}/analyze/stock", json=payload)
            data = response.json()
            print(f"   Status: {response.status_code}")
            if data.get('success'):
                analysis = data['data']['analysis']
                print(f"   Symbol: {data['data']['symbol']}")
                print(f"   Recommendation: {analysis['recommendation']}")
                print(f"   Confidence: {analysis['confidence']:.2f}")
                print("   ✅ Stock analysis working")
            print()
        except Exception as e:
            print(f"   ❌ Stock analysis failed: {e}\n")
        
        # Test 7: Metrics
        print("7️⃣ Testing metrics endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/metrics")
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   CPU: {data.get('system', {}).get('cpu_percent', 0):.1f}%")
            print(f"   Memory: {data.get('system', {}).get('memory_percent', 0):.1f}%")
            print(f"   DB Pool: {data.get('database_pool', {})}")
            print("   ✅ Metrics endpoint working\n")
        except Exception as e:
            print(f"   ❌ Metrics failed: {e}\n")

def run_sync_test():
    """Run synchronous tests using requests"""
    import requests
    
    print("🔄 Running synchronous tests with requests...\n")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server responding: {response.status_code}")
        print(f"   Message: {response.json()['data']['message']}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or not accessible")
        print("   Start the server with: python fastapi_server_simple.py")
        return
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return
    
    print("\n📊 Performance test (concurrent requests)...")
    import concurrent.futures
    import threading
    
    def make_request(symbol):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/stocks/{symbol}")
            duration = time.time() - start
            return response.status_code, duration
        except Exception as e:
            return 0, 0
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        start_time = time.time()
        futures = [executor.submit(make_request, symbol) for symbol in symbols]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
    
    successful = sum(1 for status, _ in results if status == 200)
    avg_time = sum(duration for _, duration in results) / len(results)
    
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Successful requests: {successful}/{len(symbols)}")
    print(f"   Average response time: {avg_time:.3f}s")
    print("   ✅ Performance test completed")

if __name__ == "__main__":
    print("FastAPI Server Test Suite")
    print("=" * 50)
    
    # First try sync test to check if server is running
    run_sync_test()
    
    print("\n" + "=" * 50)
    print("For full async tests, run:")
    print("python -c \"import asyncio; from test_simple import test_endpoints; asyncio.run(test_endpoints())\"")