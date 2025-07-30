#!/usr/bin/env python3
"""
Simplified FastAPI Server - Working Version
==========================================

A working FastAPI server with essential features:
- Async database connection pooling
- Background task processing
- Health monitoring
- Basic caching (in-memory fallback)
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
from concurrent.futures import ThreadPoolExecutor

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Async database
import aiomysql
from aiomysql.pool import Pool

# Data processing
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class ServerConfig:
    """Server configuration with environment variable support"""
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Down2earth!')
    DB_NAME = os.getenv('DB_NAME', 'mystocks')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Performance configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '300'))

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python code to execute", max_length=10000)
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")

class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol", max_length=10)
    days: Optional[int] = Field(default=30, description="Number of days to analyze")

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================

db_pool: Optional[Pool] = None
thread_pool = ThreadPoolExecutor(max_workers=ServerConfig.MAX_WORKERS)
simple_cache = {}  # Simple in-memory cache

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fastapi_simple.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# DATABASE CONNECTION POOL
# ==============================================================================

async def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=ServerConfig.DB_HOST,
            port=3306,
            user=ServerConfig.DB_USER,
            password=ServerConfig.DB_PASSWORD,
            db=ServerConfig.DB_NAME,
            minsize=5,
            maxsize=ServerConfig.DB_POOL_SIZE,
            autocommit=True,
            charset='utf8mb4'
        )
        logger.info(f"Database pool initialized with {ServerConfig.DB_POOL_SIZE} connections")
    except Exception as e:
        logger.warning(f"Database pool initialization failed: {e}")
        db_pool = None

async def close_db_pool():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        logger.info("Database pool closed")

@asynccontextmanager
async def get_db_connection():
    """Async context manager for database connections"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    async with db_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            await connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise

# ==============================================================================
# SIMPLE CACHE FUNCTIONS
# ==============================================================================

def cache_get(key: str) -> Optional[str]:
    """Get value from simple cache"""
    if key in simple_cache:
        entry = simple_cache[key]
        if time.time() < entry['expires']:
            return entry['value']
        else:
            del simple_cache[key]
    return None

def cache_set(key: str, value: str, ttl: int = 3600):
    """Set value in simple cache"""
    simple_cache[key] = {
        'value': value,
        'expires': time.time() + ttl
    }

# ==============================================================================
# LIFESPAN MANAGEMENT
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting FastAPI server...")
    await init_db_pool()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI server...")
    await close_db_pool()
    thread_pool.shutdown(wait=True)

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Simplified Analytics API",
    description="High-performance async API with connection pooling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict]:
    """Execute database query asynchronously"""
    if not db_pool:
        return []
    
    async with get_db_connection() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params or ())
            result = await cursor.fetchall()
            return result

async def run_cpu_intensive_task(func, *args, **kwargs):
    """Run CPU-intensive tasks in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args, **kwargs)

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return ApiResponse(
        success=True,
        data={"message": "FastAPI Analytics Server is running!"},
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {"database": "unknown", "cache": "memory"}
    
    # Check database
    if db_pool:
        try:
            async with get_db_connection() as conn:
                services["database"] = "healthy"
        except Exception:
            services["database"] = "unhealthy"
    else:
        services["database"] = "unavailable"
    
    overall_status = "healthy" if services["database"] != "unhealthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "cache_size": len(simple_cache)
    }

@app.post("/execute", response_model=ApiResponse)
async def execute_code(request: CodeExecutionRequest):
    """Execute Python code asynchronously"""
    try:
        result = await asyncio.wait_for(
            run_cpu_intensive_task(
                subprocess.run,
                ['python3', '-c', request.code],
                capture_output=True,
                text=True
            ),
            timeout=request.timeout
        )
        
        return ApiResponse(
            success=True,
            data={
                'output': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            },
            timestamp=datetime.now().isoformat()
        )
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Code execution timed out")
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}", response_model=ApiResponse)
async def get_stock_data(symbol: str, days: int = 30):
    """Get stock data with simple caching"""
    cache_key = f"stock_data:{symbol}:{days}"
    
    # Try cache first
    cached_data = cache_get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return ApiResponse(
            success=True,
            data=json.loads(cached_data),
            timestamp=datetime.now().isoformat()
        )
    
    try:
        # Simulate stock data fetch
        stock_data = {
            "symbol": symbol,
            "days": days,
            "price": 150.00 + hash(symbol) % 100,  # Mock price
            "change": (hash(symbol) % 20) - 10,
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the result
        cache_set(cache_key, json.dumps(stock_data), ttl=300)
        
        return ApiResponse(
            success=True,
            data=stock_data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/test")
async def test_database():
    """Test database connection"""
    try:
        if not db_pool:
            return ApiResponse(
                success=False,
                error="Database pool not initialized",
                timestamp=datetime.now().isoformat()
            )
        
        # Simple test query
        results = await execute_query("SELECT 1 as test_value")
        
        return ApiResponse(
            success=True,
            data={"connection": "ok", "results": results},
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.post("/analyze/stock", response_model=ApiResponse)
async def analyze_stock(request: StockAnalysisRequest):
    """Perform mock stock analysis"""
    try:
        def perform_analysis():
            import time
            time.sleep(1)  # Simulate processing
            return {
                "symbol": request.symbol,
                "analysis": {
                    "recommendation": ["BUY", "SELL", "HOLD"][hash(request.symbol) % 3],
                    "confidence": 0.70 + (hash(request.symbol) % 30) / 100,
                    "price_target": 150 + (hash(request.symbol) % 50)
                }
            }
        
        analysis_result = await run_cpu_intensive_task(perform_analysis)
        
        return ApiResponse(
            success=True,
            data=analysis_result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Stock analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get server metrics"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
    except:
        cpu_percent = 0
        memory = None
    
    db_stats = {
        "available": db_pool is not None,
        "size": db_pool.size if db_pool else 0,
        "free": db_pool.freesize if db_pool else 0
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent if memory else 0,
        },
        "database_pool": db_stats,
        "cache": {
            "type": "memory",
            "size": len(simple_cache)
        }
    }

# ==============================================================================
# MAIN APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    logger.info(f"Starting server on {ServerConfig.HOST}:{ServerConfig.PORT}")
    
    uvicorn.run(
        "fastapi_server_simple:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        access_log=True,
        log_level="info"
    )