#!/usr/bin/env python3
"""
FastAPI Server with Enhanced Performance and Security
===================================================

Modern async web server with:
- FastAPI async/await support
- Database connection pooling with aiomysql
- Redis caching layer
- Async processing for long-running tasks
- Proper error handling and monitoring
- Security improvements
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
from typing import Dict, Any, List, Optional, Union
import warnings

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Async database and Redis imports
import aiomysql
import aioredis
from aiomysql.pool import Pool
from aioredis import Redis

# Data processing imports
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
from io import BytesIO, StringIO
import base64

# External service imports
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class ServerConfig:
    """Enhanced configuration with environment variable support"""
    
    # Database configuration - use environment variables for security
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_secure_password')
    DB_NAME = os.getenv('DB_NAME', 'mystocks')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    
    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_POOL_SIZE = int(os.getenv('REDIS_POOL_SIZE', '10'))
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Async configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '300'))  # 5 minutes
    
    # File upload configuration
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '16777216'))  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'pdf'}

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python code to execute", max_length=10000)
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")

class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol", max_length=10)
    days: Optional[int] = Field(default=30, description="Number of days to analyze")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
    memory_usage: Dict[str, Any]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

# ==============================================================================
# GLOBAL VARIABLES AND POOLS
# ==============================================================================

db_pool: Optional[Pool] = None
redis_client: Optional[Redis] = None
thread_pool = ThreadPoolExecutor(max_workers=ServerConfig.MAX_WORKERS)

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

def setup_logging():
    """Setup async-compatible logging"""
    logging.basicConfig(
        level=logging.INFO if not ServerConfig.DEBUG else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('fastapi_server.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    warnings.filterwarnings('ignore', category=matplotlib.MatplotlibDeprecationWarning)
    return logging.getLogger(__name__)

logger = setup_logging()

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
        logger.error(f"Failed to initialize database pool: {e}")
        raise

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
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    
    async with db_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            await connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise

# ==============================================================================
# REDIS CONNECTION POOL
# ==============================================================================

async def init_redis_pool():
    """Initialize Redis connection pool"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            ServerConfig.REDIS_URL,
            max_connections=ServerConfig.REDIS_POOL_SIZE,
            retry_on_timeout=True,
            decode_responses=True
        )
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis pool: {e}")
        # Continue without Redis if it's not available
        redis_client = None

async def close_redis_pool():
    """Close Redis connection pool"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis pool closed")

async def cache_get(key: str) -> Optional[str]:
    """Get value from cache with error handling"""
    if not redis_client:
        return None
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return None

async def cache_set(key: str, value: str, ttl: int = ServerConfig.CACHE_TTL):
    """Set value in cache with error handling"""
    if not redis_client:
        return
    try:
        await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")

# ==============================================================================
# LIFESPAN MANAGEMENT
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting FastAPI server...")
    await init_db_pool()
    await init_redis_pool()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI server...")
    await close_db_pool()
    await close_redis_pool()
    thread_pool.shutdown(wait=True)

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Enhanced Analytics API",
    description="High-performance async API with caching and connection pooling",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# MIDDLEWARE AND DEPENDENCIES
# ==============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# ==============================================================================
# ASYNC UTILITY FUNCTIONS
# ==============================================================================

async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict]:
    """Execute database query asynchronously"""
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
        data={"message": "Enhanced FastAPI Analytics Server"},
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with service status"""
    services = {}
    
    # Check database
    try:
        async with get_db_connection() as conn:
            services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "unavailable"
    except Exception:
        services["redis"] = "unhealthy"
    
    # Memory usage
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    overall_status = "healthy" if all(
        status in ["healthy", "unavailable"] for status in services.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services,
        memory_usage={
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "percent": process.memory_percent()
        }
    )

@app.post("/execute", response_model=ApiResponse)
async def execute_code(request: CodeExecutionRequest, background_tasks: BackgroundTasks):
    """
    Execute Python code asynchronously with enhanced security
    WARNING: This endpoint should be secured or removed in production
    """
    try:
        # Run code execution in thread pool to avoid blocking
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
    """Get stock data with Redis caching"""
    cache_key = f"stock_data:{symbol}:{days}"
    
    # Try to get from cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return ApiResponse(
            success=True,
            data=json.loads(cached_data),
            timestamp=datetime.now().isoformat()
        )
    
    try:
        # Fetch stock data (this would use your existing stock data logic)
        # For now, using a placeholder
        stock_data = {
            "symbol": symbol,
            "days": days,
            "price": 150.00,  # Placeholder
            "change": 2.5,
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the result
        await cache_set(cache_key, json.dumps(stock_data), ttl=300)  # 5 minutes
        
        return ApiResponse(
            success=True,
            data=stock_data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/rows")
async def get_database_rows(limit: int = 100, offset: int = 0):
    """Get database rows with async query"""
    try:
        query = "SELECT * FROM your_table LIMIT %s OFFSET %s"
        rows = await execute_query(query, (limit, offset))
        
        return ApiResponse(
            success=True,
            data={"rows": rows, "count": len(rows)},
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/stock", response_model=ApiResponse)
async def analyze_stock(request: StockAnalysisRequest, background_tasks: BackgroundTasks):
    """Perform stock analysis asynchronously"""
    try:
        # Start analysis as background task for long-running operations
        def perform_analysis():
            # Placeholder for your existing stock analysis logic
            import time
            time.sleep(2)  # Simulate processing
            return {
                "symbol": request.symbol,
                "analysis": {
                    "recommendation": "BUY",
                    "confidence": 0.85,
                    "price_target": 175.0
                }
            }
        
        # Run analysis in thread pool
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
    import psutil
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Get pool stats
    db_stats = {
        "size": db_pool.size if db_pool else 0,
        "used": (db_pool.size - db_pool.freesize) if db_pool else 0,
        "free": db_pool.freesize if db_pool else 0
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used,
            "memory_available": memory.available
        },
        "database_pool": db_stats,
        "redis_connected": redis_client is not None
    }

# ==============================================================================
# MAIN APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    logger.info(f"Starting server on {ServerConfig.HOST}:{ServerConfig.PORT}")
    
    uvicorn.run(
        "fastapi_server:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        workers=1,  # Single worker for development, increase for production
        access_log=True,
        log_level="info" if not ServerConfig.DEBUG else "debug"
    )