"""
Phase 2B Streaming Fallback Wrapper System
Intelligent streaming optimization with automatic fallback to safe processing
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, AsyncIterator, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json
from phase2b_rollback_controller import is_phase2b_feature_enabled, FeatureFlag
from phase2b_performance_monitor import record_performance_metric

logger = logging.getLogger(__name__)


class StreamingStrategy(Enum):
    """Streaming processing strategies"""
    DISABLED = "disabled"          # No streaming - original processing
    BUFFER_OPTIMIZED = "buffered"  # Buffered streaming with optimization
    CHUNKED = "chunked"            # Chunk-based streaming
    ADAPTIVE = "adaptive"          # Adaptive strategy based on content


@dataclass 
class StreamingConfig:
    """Configuration for streaming processing"""
    strategy: StreamingStrategy = StreamingStrategy.DISABLED
    buffer_size: int = 4096        # Buffer size in bytes
    chunk_size: int = 1024         # Chunk size for streaming
    timeout_ms: int = 30000        # Timeout in milliseconds
    enable_compression: bool = True # Enable response compression
    max_memory_mb: int = 50        # Max memory usage in MB


class Phase2BStreamingWrapper:
    """
    Intelligent streaming wrapper with automatic fallback.
    Provides enhanced response processing with safety guarantees.
    """
    
    def __init__(self):
        self.config = StreamingConfig()
        self._fallback_active = False
        self._performance_metrics = {}
        self._streaming_stats = {
            "total_requests": 0,
            "streaming_successes": 0,
            "fallback_triggers": 0,
            "avg_processing_time": 0.0,
            "memory_peak_mb": 0.0
        }
        
        logger.info("🔄 Streaming Fallback Wrapper initialized")
    
    async def process_response(self, 
                              response_data: Union[str, Dict[str, Any]], 
                              request_context: Optional[Dict[str, Any]] = None) -> AsyncIterator[str]:
        """
        Process response with intelligent streaming and fallback.
        
        Args:
            response_data: The response content to stream
            request_context: Optional context for processing decisions
            
        Yields:
            Processed response chunks
        """
        start_time = time.time()
        self._streaming_stats["total_requests"] += 1
        
        try:
            # Check if streaming features are enabled
            if not is_phase2b_feature_enabled(FeatureFlag.STREAMING_FALLBACK):
                logger.debug("🔄 Streaming disabled - using fallback processing")
                async for chunk in self._fallback_processing(response_data):
                    yield chunk
                return
            
            # Determine streaming strategy
            strategy = self._determine_strategy(response_data, request_context)
            
            if strategy == StreamingStrategy.DISABLED or self._fallback_active:
                async for chunk in self._fallback_processing(response_data):
                    yield chunk
            else:
                try:
                    async for chunk in self._streaming_processing(response_data, strategy, request_context):
                        yield chunk
                    
                    self._streaming_stats["streaming_successes"] += 1
                    
                except Exception as streaming_error:
                    logger.warning(f"⚠️ Streaming failed: {streaming_error}")
                    logger.info("🔄 Falling back to safe processing")
                    
                    self._streaming_stats["fallback_triggers"] += 1
                    
                    # Automatic fallback to safe processing
                    async for chunk in self._fallback_processing(response_data):
                        yield chunk
        
        except Exception as e:
            logger.error(f"❌ Response processing failed: {e}")
            # Emergency fallback - return response as-is
            if isinstance(response_data, str):
                yield response_data
            else:
                yield json.dumps(response_data) if response_data else ""
        
        finally:
            # Record performance metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            record_performance_metric("streaming_processing_time", processing_time)
            
            # Update stats
            self._update_performance_stats(processing_time)
    
    def _determine_strategy(self, 
                           response_data: Union[str, Dict[str, Any]], 
                           context: Optional[Dict[str, Any]]) -> StreamingStrategy:
        """Determine optimal streaming strategy based on content and context"""
        try:
            # Default to disabled if not explicitly enabled
            if not is_phase2b_feature_enabled(FeatureFlag.BUFFER_OPTIMIZATION):
                return StreamingStrategy.DISABLED
            
            # Analyze response content
            content_size = len(str(response_data)) if response_data else 0
            
            # Strategy selection based on content characteristics
            if content_size < 1000:
                # Small responses - no streaming benefit
                return StreamingStrategy.DISABLED
            elif content_size < 10000:
                # Medium responses - buffered streaming
                return StreamingStrategy.BUFFER_OPTIMIZED
            elif content_size < 100000:
                # Large responses - chunked streaming
                return StreamingStrategy.CHUNKED
            else:
                # Very large responses - adaptive streaming
                return StreamingStrategy.ADAPTIVE
                
        except Exception as e:
            logger.warning(f"⚠️ Strategy determination failed: {e}")
            return StreamingStrategy.DISABLED
    
    async def _streaming_processing(self, 
                                   response_data: Union[str, Dict[str, Any]], 
                                   strategy: StreamingStrategy,
                                   context: Optional[Dict[str, Any]]) -> AsyncIterator[str]:
        """Enhanced streaming processing based on strategy"""
        
        if strategy == StreamingStrategy.BUFFER_OPTIMIZED:
            async for chunk in self._buffer_optimized_streaming(response_data):
                yield chunk
                
        elif strategy == StreamingStrategy.CHUNKED:
            async for chunk in self._chunked_streaming(response_data):
                yield chunk
                
        elif strategy == StreamingStrategy.ADAPTIVE:
            async for chunk in self._adaptive_streaming(response_data, context):
                yield chunk
                
        else:
            # Fallback for unknown strategies
            async for chunk in self._fallback_processing(response_data):
                yield chunk
    
    async def _buffer_optimized_streaming(self, response_data: Union[str, Dict[str, Any]]) -> AsyncIterator[str]:
        """Buffer-optimized streaming processing"""
        try:
            content = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
            buffer_size = self.config.buffer_size
            
            # Process in optimized buffer chunks
            for i in range(0, len(content), buffer_size):
                chunk = content[i:i + buffer_size]
                
                # Add minimal processing delay to prevent overwhelming
                if i > 0:
                    await asyncio.sleep(0.001)  # 1ms delay
                
                yield chunk
                
        except Exception as e:
            logger.warning(f"⚠️ Buffer optimization failed: {e}")
            raise
    
    async def _chunked_streaming(self, response_data: Union[str, Dict[str, Any]]) -> AsyncIterator[str]:
        """Chunked streaming processing"""
        try:
            content = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
            chunk_size = self.config.chunk_size
            
            # Process in smaller chunks with flow control
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                
                # Flow control - prevent memory pressure
                if i > 0 and i % (chunk_size * 10) == 0:
                    await asyncio.sleep(0.005)  # 5ms pause every 10 chunks
                
                yield chunk
                
        except Exception as e:
            logger.warning(f"⚠️ Chunked streaming failed: {e}")
            raise
    
    async def _adaptive_streaming(self, 
                                 response_data: Union[str, Dict[str, Any]], 
                                 context: Optional[Dict[str, Any]]) -> AsyncIterator[str]:
        """Adaptive streaming with dynamic adjustment"""
        try:
            content = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
            
            # Adaptive chunk sizing based on content and system state
            base_chunk_size = self.config.chunk_size
            content_length = len(content)
            
            # Adjust chunk size based on content length
            if content_length > 50000:
                adaptive_chunk_size = min(base_chunk_size * 2, 8192)  # Larger chunks for big content
            else:
                adaptive_chunk_size = base_chunk_size
            
            # Stream with adaptive chunking
            for i in range(0, len(content), adaptive_chunk_size):
                chunk = content[i:i + adaptive_chunk_size]
                
                # Dynamic backpressure based on processing speed
                if i > 0:
                    # Adaptive delay based on chunk size
                    delay = min(0.01, adaptive_chunk_size / 100000)  # Max 10ms delay
                    await asyncio.sleep(delay)
                
                yield chunk
                
        except Exception as e:
            logger.warning(f"⚠️ Adaptive streaming failed: {e}")
            raise
    
    async def _fallback_processing(self, response_data: Union[str, Dict[str, Any]]) -> AsyncIterator[str]:
        """Safe fallback processing - guaranteed to work"""
        try:
            # Simple, reliable processing
            if isinstance(response_data, dict):
                yield json.dumps(response_data)
            else:
                yield str(response_data) if response_data else ""
                
        except Exception as e:
            logger.error(f"❌ Even fallback processing failed: {e}")
            # Ultimate fallback
            yield ""
    
    def _update_performance_stats(self, processing_time_ms: float):
        """Update internal performance statistics"""
        try:
            total = self._streaming_stats["total_requests"]
            current_avg = self._streaming_stats["avg_processing_time"]
            
            # Calculate running average
            new_avg = ((current_avg * (total - 1)) + processing_time_ms) / total
            self._streaming_stats["avg_processing_time"] = new_avg
            
        except Exception as e:
            logger.warning(f"⚠️ Stats update failed: {e}")
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get current streaming performance statistics"""
        return {
            **self._streaming_stats.copy(),
            "fallback_rate": (
                self._streaming_stats["fallback_triggers"] / 
                max(self._streaming_stats["total_requests"], 1) * 100
            ),
            "success_rate": (
                self._streaming_stats["streaming_successes"] / 
                max(self._streaming_stats["total_requests"], 1) * 100
            ),
            "config": {
                "strategy": self.config.strategy.value,
                "buffer_size": self.config.buffer_size,
                "chunk_size": self.config.chunk_size,
            }
        }
    
    def enable_emergency_fallback(self):
        """Enable emergency fallback mode"""
        self._fallback_active = True
        logger.warning("🚨 Emergency fallback mode activated")
    
    def disable_emergency_fallback(self):
        """Disable emergency fallback mode"""
        self._fallback_active = False
        logger.info("✅ Emergency fallback mode deactivated")
    
    def update_config(self, new_config: StreamingConfig):
        """Update streaming configuration"""
        try:
            self.config = new_config
            logger.info(f"🔧 Streaming config updated: strategy={new_config.strategy.value}")
        except Exception as e:
            logger.error(f"❌ Config update failed: {e}")


# Global streaming wrapper instance
streaming_wrapper = Phase2BStreamingWrapper()


# Convenience functions for integration
async def process_response_with_streaming(response_data: Union[str, Dict[str, Any]], 
                                         context: Optional[Dict[str, Any]] = None) -> AsyncIterator[str]:
    """Process response with intelligent streaming and fallback"""
    async for chunk in streaming_wrapper.process_response(response_data, context):
        yield chunk


def get_streaming_statistics() -> Dict[str, Any]:
    """Get current streaming performance statistics"""
    return streaming_wrapper.get_streaming_stats()


def enable_streaming_fallback():
    """Enable emergency streaming fallback"""
    streaming_wrapper.enable_emergency_fallback()


def disable_streaming_fallback():
    """Disable emergency streaming fallback"""
    streaming_wrapper.disable_emergency_fallback()