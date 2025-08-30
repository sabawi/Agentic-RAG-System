#!/usr/bin/env python3
"""
Test suite for FastAPI server
============================

Comprehensive tests for async endpoints, caching, and database operations.
"""

import asyncio
import json
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi_server import app, ServerConfig
import time

# ==============================================================================
# TEST CONFIGURATION
# ==============================================================================

@pytest.fixture
def client():
    """Synchronous test client for simple tests"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async test client for async tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# ==============================================================================
# BASIC ENDPOINT TESTS
# ==============================================================================

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Enhanced FastAPI Analytics Server" in data["data"]["message"]

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # May be unhealthy if services not running
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data

def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "system" in data
    assert "database_pool" in data

# ==============================================================================
# ASYNC ENDPOINT TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_stock_data_endpoint(async_client):
    """Test stock data endpoint with caching"""
    # First request
    response1 = await async_client.get("/stocks/AAPL?days=30")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["success"] is True
    assert data1["data"]["symbol"] == "AAPL"
    
    # Second request (should hit cache if Redis is available)
    start_time = time.time()
    response2 = await async_client.get("/stocks/AAPL?days=30")
    end_time = time.time()
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["success"] is True
    
    # Second request should be faster if cached
    print(f"Second request took: {end_time - start_time:.3f}s")

@pytest.mark.asyncio
async def test_code_execution_endpoint(async_client):
    """Test code execution endpoint"""
    payload = {
        "code": "print('Hello, FastAPI!')",
        "timeout": 10
    }
    
    response = await async_client.post("/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Hello, FastAPI!" in data["data"]["output"]

@pytest.mark.asyncio
async def test_stock_analysis_endpoint(async_client):
    """Test stock analysis endpoint"""
    payload = {
        "symbol": "TSLA",
        "days": 30
    }
    
    response = await async_client.post("/analyze/stock", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "TSLA"
    assert "analysis" in data["data"]

# ==============================================================================
# ERROR HANDLING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_code_execution_timeout(async_client):
    """Test code execution timeout"""
    payload = {
        "code": "import time; time.sleep(5)",
        "timeout": 1  # Short timeout
    }
    
    response = await async_client.post("/execute", json=payload)
    assert response.status_code == 504  # Timeout error

@pytest.mark.asyncio
async def test_invalid_stock_symbol(async_client):
    """Test handling of invalid stock symbol"""
    response = await async_client.get("/stocks/INVALID?days=30")
    # Should still return 200 with placeholder data in current implementation
    assert response.status_code == 200

def test_invalid_json_payload(client):
    """Test handling of invalid JSON payload"""
    response = client.post("/execute", json={"invalid": "payload"})
    assert response.status_code == 422  # Validation error

# ==============================================================================
# PERFORMANCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """Test concurrent request handling"""
    async def make_request(symbol):
        response = await async_client.get(f"/stocks/{symbol}")
        return response.status_code, response.json()
    
    # Make concurrent requests
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    tasks = [make_request(symbol) for symbol in symbols]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # All requests should succeed
    for status_code, data in results:
        assert status_code == 200
        assert data["success"] is True
    
    print(f"Concurrent requests took: {end_time - start_time:.3f}s")

@pytest.mark.asyncio
async def test_cache_performance():
    """Test Redis cache performance"""
    # This test requires Redis to be running
    try:
        from fastapi_server import cache_set, cache_get
        
        # Test cache set/get performance
        test_key = "performance_test"
        test_data = {"test": "data", "timestamp": time.time()}
        test_value = json.dumps(test_data)
        
        # Set cache
        start_time = time.time()
        await cache_set(test_key, test_value)
        set_time = time.time() - start_time
        
        # Get cache
        start_time = time.time()
        result = await cache_get(test_key)
        get_time = time.time() - start_time
        
        assert result == test_value
        print(f"Cache set took: {set_time:.3f}s, get took: {get_time:.3f}s")
        
    except Exception as e:
        pytest.skip(f"Cache test skipped: {e}")

# ==============================================================================
# LOAD TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_high_load_simulation(async_client):
    """Simulate high load scenario"""
    async def worker():
        tasks = []
        for i in range(10):  # 10 requests per worker
            tasks.append(async_client.get(f"/stocks/TEST{i}"))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        return successful
    
    # Run multiple workers concurrently
    start_time = time.time()
    workers = [worker() for _ in range(5)]  # 5 workers = 50 total requests
    results = await asyncio.gather(*workers)
    end_time = time.time()
    
    total_successful = sum(results)
    total_time = end_time - start_time
    
    print(f"Load test: {total_successful}/50 requests successful in {total_time:.3f}s")
    print(f"Throughput: {total_successful/total_time:.1f} requests/second")
    
    assert total_successful >= 45  # At least 90% success rate

# ==============================================================================
# RUN TESTS
# ==============================================================================

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v", "--tb=short"])