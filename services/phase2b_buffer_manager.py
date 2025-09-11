"""
Phase 2B Buffer Management System
Advanced buffer pooling and memory optimization for response processing
"""

import asyncio
import logging
import time
import gc
from typing import Dict, Any, Optional, List, Union, Deque
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import threading
import weakref
from phase2b_rollback_controller import is_phase2b_feature_enabled, FeatureFlag
from phase2b_performance_monitor import record_performance_metric

logger = logging.getLogger(__name__)


class BufferStrategy(Enum):
    """Buffer management strategies"""
    DISABLED = "disabled"      # No buffer management
    BASIC_POOL = "basic_pool"  # Basic buffer pooling
    ADAPTIVE = "adaptive"      # Adaptive sizing
    MEMORY_AWARE = "memory_aware"  # Memory-aware optimization


@dataclass
class BufferConfig:
    """Configuration for buffer management"""
    strategy: BufferStrategy = BufferStrategy.DISABLED
    initial_pool_size: int = 10       # Initial buffer pool size
    max_pool_size: int = 50          # Maximum pool size
    buffer_size: int = 8192          # Default buffer size in bytes
    growth_factor: float = 1.5       # Pool growth factor
    max_memory_mb: int = 100         # Maximum memory usage
    cleanup_interval: int = 300      # Cleanup interval in seconds


class BufferPool:
    """Memory-efficient buffer pool with automatic management"""
    
    def __init__(self, config: BufferConfig):
        self.config = config
        self._buffers: Deque[bytearray] = deque()
        self._in_use: Dict[int, bytearray] = {}  # Track buffers in use
        self._lock = threading.RLock()
        self._total_allocated = 0
        self._peak_usage = 0
        self._stats = {
            "total_allocations": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "memory_reclaimed_mb": 0.0,
            "peak_pool_size": 0
        }
        
        # Initialize pool if strategy requires it
        if config.strategy != BufferStrategy.DISABLED:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the buffer pool"""
        try:
            with self._lock:
                for _ in range(self.config.initial_pool_size):
                    buffer = bytearray(self.config.buffer_size)
                    self._buffers.append(buffer)
                    self._total_allocated += self.config.buffer_size
                
                logger.info(f"📦 Buffer pool initialized: {self.config.initial_pool_size} buffers, "
                           f"{self._total_allocated} bytes")
                
        except Exception as e:
            logger.error(f"❌ Buffer pool initialization failed: {e}")
    
    def get_buffer(self, size: Optional[int] = None) -> bytearray:
        """Get a buffer from the pool or create new one"""
        start_time = time.time()
        
        try:
            with self._lock:
                requested_size = size or self.config.buffer_size
                
                # Try to get from pool first
                if self._buffers and self.config.strategy != BufferStrategy.DISABLED:
                    buffer = self._buffers.popleft()
                    
                    # Resize if needed
                    if len(buffer) < requested_size:
                        # Grow buffer if strategy allows
                        if self.config.strategy in [BufferStrategy.ADAPTIVE, BufferStrategy.MEMORY_AWARE]:
                            buffer = bytearray(requested_size)
                        else:
                            # Return to pool and create new
                            self._buffers.appendleft(buffer)
                            buffer = bytearray(requested_size)
                    
                    self._stats["pool_hits"] += 1
                else:
                    # Pool miss - create new buffer
                    buffer = bytearray(requested_size)
                    self._stats["pool_misses"] += 1
                
                # Track buffer usage
                buffer_id = id(buffer)
                self._in_use[buffer_id] = buffer
                self._total_allocated += len(buffer)
                self._peak_usage = max(self._peak_usage, self._total_allocated)
                self._stats["total_allocations"] += 1
                
                # Record performance
                allocation_time = (time.time() - start_time) * 1000
                record_performance_metric("buffer_allocation_time", allocation_time)
                
                return buffer
                
        except Exception as e:
            logger.error(f"❌ Buffer allocation failed: {e}")
            # Emergency fallback
            return bytearray(size or self.config.buffer_size)
    
    def return_buffer(self, buffer: bytearray):
        """Return buffer to pool"""
        try:
            with self._lock:
                buffer_id = id(buffer)
                
                # Remove from in-use tracking
                if buffer_id in self._in_use:
                    del self._in_use[buffer_id]
                    self._total_allocated -= len(buffer)
                
                # Return to pool if strategy allows and pool has space
                if (self.config.strategy != BufferStrategy.DISABLED and 
                    len(self._buffers) < self.config.max_pool_size):
                    
                    # Clear buffer content for reuse
                    buffer[:] = b'\x00' * len(buffer)
                    self._buffers.append(buffer)
                    
                    # Update peak pool size stat
                    self._stats["peak_pool_size"] = max(
                        self._stats["peak_pool_size"], 
                        len(self._buffers)
                    )
                else:
                    # Let buffer be garbage collected
                    self._stats["memory_reclaimed_mb"] += len(buffer) / (1024 * 1024)
                
        except Exception as e:
            logger.warning(f"⚠️ Buffer return failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer pool statistics"""
        with self._lock:
            return {
                **self._stats.copy(),
                "pool_size": len(self._buffers),
                "buffers_in_use": len(self._in_use),
                "total_allocated_mb": self._total_allocated / (1024 * 1024),
                "peak_usage_mb": self._peak_usage / (1024 * 1024),
                "hit_rate": (
                    self._stats["pool_hits"] / 
                    max(self._stats["pool_hits"] + self._stats["pool_misses"], 1) * 100
                )
            }
    
    def cleanup(self):
        """Cleanup unused buffers"""
        try:
            with self._lock:
                initial_count = len(self._buffers)
                initial_memory = sum(len(buf) for buf in self._buffers)
                
                # Keep minimum pool size
                min_keep = max(1, self.config.initial_pool_size // 2)
                
                if len(self._buffers) > min_keep:
                    excess_count = len(self._buffers) - min_keep
                    
                    # Remove excess buffers
                    for _ in range(excess_count):
                        if self._buffers:
                            buffer = self._buffers.pop()
                            self._stats["memory_reclaimed_mb"] += len(buffer) / (1024 * 1024)
                
                final_count = len(self._buffers)
                final_memory = sum(len(buf) for buf in self._buffers)
                reclaimed_mb = (initial_memory - final_memory) / (1024 * 1024)
                
                if reclaimed_mb > 0:
                    logger.info(f"🧹 Buffer cleanup: {initial_count} -> {final_count} buffers, "
                               f"reclaimed {reclaimed_mb:.1f}MB")
                
                # Force garbage collection
                gc.collect()
                
        except Exception as e:
            logger.error(f"❌ Buffer cleanup failed: {e}")


class Phase2BBufferManager:
    """
    Advanced buffer management system with intelligent pooling and memory optimization.
    Provides efficient memory usage for response processing.
    """
    
    def __init__(self):
        self.config = BufferConfig()
        self._buffer_pool: Optional[BufferPool] = None
        self._memory_monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._active = False
        
        logger.info("🗂️ Buffer Manager initialized")
    
    async def start(self):
        """Start buffer management system"""
        try:
            if not is_phase2b_feature_enabled(FeatureFlag.BUFFER_OPTIMIZATION):
                logger.info("🗂️ Buffer optimization disabled by feature flag")
                return
            
            # Initialize buffer pool
            if self.config.strategy != BufferStrategy.DISABLED:
                self._buffer_pool = BufferPool(self.config)
            
            # Start background tasks
            self._memory_monitor_task = asyncio.create_task(self._memory_monitor())
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            self._active = True
            logger.info("🗂️ Buffer management system started")
            
        except Exception as e:
            logger.error(f"❌ Buffer manager startup failed: {e}")
    
    async def stop(self):
        """Stop buffer management system"""
        try:
            self._active = False
            
            # Cancel background tasks
            if self._memory_monitor_task:
                self._memory_monitor_task.cancel()
                
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # Final cleanup
            if self._buffer_pool:
                self._buffer_pool.cleanup()
            
            logger.info("🗂️ Buffer management system stopped")
            
        except Exception as e:
            logger.error(f"❌ Buffer manager shutdown failed: {e}")
    
    def get_managed_buffer(self, size: Optional[int] = None) -> 'ManagedBuffer':
        """Get a managed buffer with automatic cleanup"""
        if self._buffer_pool and is_phase2b_feature_enabled(FeatureFlag.BUFFER_OPTIMIZATION):
            buffer = self._buffer_pool.get_buffer(size)
            return ManagedBuffer(buffer, self._buffer_pool)
        else:
            # Fallback to regular buffer
            buffer = bytearray(size or self.config.buffer_size)
            return ManagedBuffer(buffer, None)
    
    def process_with_buffer(self, data: Union[str, bytes, Dict[str, Any]], 
                           context: Optional[Dict[str, Any]] = None) -> bytes:
        """Process data using managed buffers"""
        start_time = time.time()
        
        try:
            # Convert input to bytes
            if isinstance(data, str):
                input_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                import json
                input_bytes = json.dumps(data).encode('utf-8')
            else:
                input_bytes = bytes(data)
            
            # Get buffer for processing
            with self.get_managed_buffer(len(input_bytes) * 2) as buffer:
                # Simple processing - copy input to buffer
                buffer.write(input_bytes)
                result = bytes(buffer.get_data())
            
            # Record performance
            processing_time = (time.time() - start_time) * 1000
            record_performance_metric("buffer_processing_time", processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Buffer processing failed: {e}")
            # Fallback processing
            if isinstance(data, str):
                return data.encode('utf-8')
            elif isinstance(data, dict):
                import json
                return json.dumps(data).encode('utf-8')
            else:
                return bytes(data)
    
    async def _memory_monitor(self):
        """Monitor memory usage and adjust strategy"""
        while self._active:
            try:
                if self._buffer_pool:
                    stats = self._buffer_pool.get_stats()
                    
                    # Check memory usage
                    if stats["total_allocated_mb"] > self.config.max_memory_mb:
                        logger.warning(f"⚠️ High memory usage: {stats['total_allocated_mb']:.1f}MB")
                        
                        # Trigger cleanup
                        self._buffer_pool.cleanup()
                        
                        # Record memory pressure
                        record_performance_metric("buffer_memory_pressure", stats["total_allocated_mb"])
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Memory monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _periodic_cleanup(self):
        """Periodic buffer pool cleanup"""
        while self._active:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                
                if self._buffer_pool:
                    self._buffer_pool.cleanup()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Periodic cleanup error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get buffer management statistics"""
        if self._buffer_pool:
            return {
                "buffer_pool": self._buffer_pool.get_stats(),
                "config": {
                    "strategy": self.config.strategy.value,
                    "max_pool_size": self.config.max_pool_size,
                    "buffer_size": self.config.buffer_size,
                    "max_memory_mb": self.config.max_memory_mb
                },
                "active": self._active
            }
        else:
            return {
                "buffer_pool": {"status": "disabled"},
                "active": self._active
            }
    
    def update_config(self, new_config: BufferConfig):
        """Update buffer management configuration"""
        try:
            self.config = new_config
            
            # Recreate buffer pool if needed
            if self._buffer_pool and new_config.strategy != BufferStrategy.DISABLED:
                self._buffer_pool = BufferPool(new_config)
            
            logger.info(f"🔧 Buffer config updated: strategy={new_config.strategy.value}")
            
        except Exception as e:
            logger.error(f"❌ Buffer config update failed: {e}")


class ManagedBuffer:
    """Context manager for automatic buffer lifecycle management"""
    
    def __init__(self, buffer: bytearray, pool: Optional[BufferPool]):
        self._buffer = buffer
        self._pool = pool
        self._position = 0
        self._closed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def write(self, data: bytes):
        """Write data to buffer"""
        if self._closed:
            raise ValueError("Buffer is closed")
        
        data_len = len(data)
        end_pos = self._position + data_len
        
        # Extend buffer if needed
        if end_pos > len(self._buffer):
            self._buffer.extend(b'\x00' * (end_pos - len(self._buffer)))
        
        # Copy data
        self._buffer[self._position:end_pos] = data
        self._position = end_pos
    
    def get_data(self) -> bytes:
        """Get buffer data up to current position"""
        if self._closed:
            raise ValueError("Buffer is closed")
        
        return bytes(self._buffer[:self._position])
    
    def reset(self):
        """Reset buffer position"""
        self._position = 0
    
    def close(self):
        """Close buffer and return to pool"""
        if not self._closed and self._pool:
            self._pool.return_buffer(self._buffer)
        
        self._closed = True


# Global buffer manager instance
buffer_manager = Phase2BBufferManager()


# Convenience functions for integration
async def start_buffer_management():
    """Start buffer management system"""
    await buffer_manager.start()


async def stop_buffer_management():
    """Stop buffer management system"""
    await buffer_manager.stop()


def get_managed_buffer(size: Optional[int] = None) -> ManagedBuffer:
    """Get a managed buffer"""
    return buffer_manager.get_managed_buffer(size)


def process_with_buffers(data: Union[str, bytes, Dict[str, Any]], 
                        context: Optional[Dict[str, Any]] = None) -> bytes:
    """Process data using managed buffers"""
    return buffer_manager.process_with_buffer(data, context)


def get_buffer_statistics() -> Dict[str, Any]:
    """Get buffer management statistics"""
    return buffer_manager.get_statistics()