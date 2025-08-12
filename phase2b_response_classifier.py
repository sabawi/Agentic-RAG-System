"""
Phase 2B Response Classification Engine
Intelligent response analysis for optimal processing strategy selection
"""

import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from phase2b_rollback_controller import is_phase2b_feature_enabled, FeatureFlag
from phase2b_performance_monitor import record_performance_metric

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Types of responses that can be classified"""
    SIMPLE_TEXT = "simple_text"           # Plain text responses
    JSON_DATA = "json_data"               # JSON structured data
    TOOL_RESULTS = "tool_results"         # Tool execution results
    ERROR_RESPONSE = "error_response"     # Error responses
    STREAMING_CANDIDATE = "streaming"     # Good for streaming
    LARGE_CONTENT = "large_content"       # Large responses
    MIXED_CONTENT = "mixed_content"       # Mixed content types


class ProcessingPriority(Enum):
    """Processing priority levels"""
    LOW = "low"           # Background processing
    NORMAL = "normal"     # Standard processing
    HIGH = "high"         # Priority processing
    CRITICAL = "critical" # Immediate processing


@dataclass
class ResponseClassification:
    """Classification result for a response"""
    response_type: ResponseType
    priority: ProcessingPriority
    confidence: float  # 0.0 to 1.0
    characteristics: Dict[str, Any] = field(default_factory=dict)
    processing_hints: Dict[str, Any] = field(default_factory=dict)
    estimated_processing_time: float = 0.0  # in seconds
    memory_requirements: int = 0  # in bytes


class Phase2BResponseClassifier:
    """
    Intelligent response classifier for optimal processing strategy.
    Analyzes response content and provides processing recommendations.
    """
    
    def __init__(self):
        self._classification_cache: Dict[str, ResponseClassification] = {}
        self._stats = {
            "total_classifications": 0,
            "cache_hits": 0,
            "processing_time_ms": 0.0,
            "accuracy_feedback": []
        }
        
        # Classification patterns
        self._patterns = {
            "json_indicators": [
                r'^\s*[\{\[]',  # Starts with { or [
                r'^\s*"[^"]+"\s*:',  # JSON key pattern
                r'^\s*\{\s*"',  # Clear JSON object start
            ],
            "tool_result_indicators": [
                r'tool:\s*\w+',  # "tool: toolname"
                r'result:\s*',   # "result: "
                r'###\s*TOOLS\s*RESULTS',  # Tool results header
                r'==============',  # Tool result separators
            ],
            "error_indicators": [
                r'\b[Ee]rror\b',
                r'\bException\b',
                r'\bFailed\b',
                r'\b[Tt]imeout\b',
                r'❌',  # Error emoji
            ],
            "streaming_friendly": [
                r'\n\n',  # Multiple paragraphs
                r'###\s',  # Markdown headers
                r'\d+\.',  # Numbered lists
                r'-\s+',   # Bullet points
            ]
        }
        
        logger.info("🧠 Response Classifier initialized")
    
    def classify_response(self, 
                         response_data: Union[str, Dict[str, Any]], 
                         context: Optional[Dict[str, Any]] = None) -> ResponseClassification:
        """
        Classify response content and provide processing recommendations.
        
        Args:
            response_data: The response content to classify
            context: Optional context information
            
        Returns:
            ResponseClassification with processing recommendations
        """
        start_time = time.time()
        
        try:
            # Check if classification is enabled
            if not is_phase2b_feature_enabled(FeatureFlag.RESPONSE_CLASSIFICATION):
                return self._default_classification()
            
            # Create cache key
            cache_key = self._create_cache_key(response_data, context)
            
            # Check cache
            if cache_key in self._classification_cache:
                self._stats["cache_hits"] += 1
                return self._classification_cache[cache_key]
            
            # Perform classification
            classification = self._perform_classification(response_data, context)
            
            # Cache result
            self._classification_cache[cache_key] = classification
            
            # Update stats
            self._stats["total_classifications"] += 1
            processing_time = (time.time() - start_time) * 1000
            self._stats["processing_time_ms"] += processing_time
            
            # Record performance metric
            record_performance_metric("response_classification_time", processing_time)
            
            return classification
            
        except Exception as e:
            logger.error(f"❌ Response classification failed: {e}")
            return self._default_classification()
    
    def _perform_classification(self, 
                               response_data: Union[str, Dict[str, Any]], 
                               context: Optional[Dict[str, Any]]) -> ResponseClassification:
        """Perform the actual response classification"""
        
        # Convert to string for analysis
        if isinstance(response_data, dict):
            content = json.dumps(response_data)
            initial_type = ResponseType.JSON_DATA
            confidence = 0.9
        else:
            content = str(response_data) if response_data else ""
            initial_type = ResponseType.SIMPLE_TEXT
            confidence = 0.7
        
        # Analyze content characteristics
        content_length = len(content)
        word_count = len(content.split()) if content else 0
        line_count = content.count('\n') + 1
        
        characteristics = {
            "content_length": content_length,
            "word_count": word_count,
            "line_count": line_count,
            "has_unicode": any(ord(c) > 127 for c in content),
            "has_structured_data": False,
            "complexity_score": 0.0
        }
        
        # Pattern-based classification
        response_type, type_confidence = self._classify_by_patterns(content, initial_type)
        characteristics["has_structured_data"] = response_type in [
            ResponseType.JSON_DATA, ResponseType.TOOL_RESULTS
        ]
        
        # Determine processing priority
        priority = self._determine_priority(response_type, content_length, context)
        
        # Calculate complexity score
        complexity = self._calculate_complexity(content, characteristics)
        characteristics["complexity_score"] = complexity
        
        # Generate processing hints
        processing_hints = self._generate_processing_hints(response_type, characteristics, context)
        
        # Estimate processing requirements
        processing_time = self._estimate_processing_time(response_type, content_length, complexity)
        memory_req = self._estimate_memory_requirements(response_type, content_length)
        
        return ResponseClassification(
            response_type=response_type,
            priority=priority,
            confidence=min(confidence * type_confidence, 1.0),
            characteristics=characteristics,
            processing_hints=processing_hints,
            estimated_processing_time=processing_time,
            memory_requirements=memory_req
        )
    
    def _classify_by_patterns(self, content: str, initial_type: ResponseType) -> Tuple[ResponseType, float]:
        """Classify response type using pattern matching"""
        
        if not content.strip():
            return ResponseType.SIMPLE_TEXT, 0.9
        
        # Check for JSON patterns
        json_score = sum(1 for pattern in self._patterns["json_indicators"] 
                        if re.search(pattern, content, re.MULTILINE))
        
        # Check for tool result patterns
        tool_score = sum(1 for pattern in self._patterns["tool_result_indicators"] 
                        if re.search(pattern, content, re.MULTILINE))
        
        # Check for error patterns
        error_score = sum(1 for pattern in self._patterns["error_indicators"] 
                         if re.search(pattern, content, re.MULTILINE))
        
        # Check for streaming-friendly patterns
        streaming_score = sum(1 for pattern in self._patterns["streaming_friendly"] 
                             if re.search(pattern, content, re.MULTILINE))
        
        # Determine type based on scores
        if error_score >= 2:
            return ResponseType.ERROR_RESPONSE, 0.8
        elif tool_score >= 2:
            return ResponseType.TOOL_RESULTS, 0.85
        elif json_score >= 2 and initial_type == ResponseType.JSON_DATA:
            return ResponseType.JSON_DATA, 0.9
        elif len(content) > 10000:
            return ResponseType.LARGE_CONTENT, 0.8
        elif streaming_score >= 3:
            return ResponseType.STREAMING_CANDIDATE, 0.7
        elif json_score >= 1 and tool_score >= 1:
            return ResponseType.MIXED_CONTENT, 0.6
        else:
            return ResponseType.SIMPLE_TEXT, 0.7
    
    def _determine_priority(self, 
                           response_type: ResponseType, 
                           content_length: int, 
                           context: Optional[Dict[str, Any]]) -> ProcessingPriority:
        """Determine processing priority"""
        
        # Error responses need immediate attention
        if response_type == ResponseType.ERROR_RESPONSE:
            return ProcessingPriority.CRITICAL
        
        # Large content may need priority processing
        if content_length > 50000:
            return ProcessingPriority.HIGH
        
        # Tool results are usually important
        if response_type == ResponseType.TOOL_RESULTS:
            return ProcessingPriority.HIGH
        
        # Context-based priority
        if context:
            if context.get("urgent", False):
                return ProcessingPriority.CRITICAL
            elif context.get("background", False):
                return ProcessingPriority.LOW
        
        return ProcessingPriority.NORMAL
    
    def _calculate_complexity(self, content: str, characteristics: Dict[str, Any]) -> float:
        """Calculate content complexity score (0.0 to 1.0)"""
        
        score = 0.0
        
        # Length-based complexity
        length_complexity = min(len(content) / 100000, 0.3)  # Max 0.3 for length
        score += length_complexity
        
        # Structure-based complexity
        if characteristics["has_structured_data"]:
            score += 0.2
        
        # Unicode complexity
        if characteristics["has_unicode"]:
            score += 0.1
        
        # Line count complexity
        line_complexity = min(characteristics["line_count"] / 1000, 0.2)  # Max 0.2 for lines
        score += line_complexity
        
        # Pattern complexity - check for complex patterns
        complex_patterns = [
            r'\{[^}]*\{[^}]*\}[^}]*\}',  # Nested structures
            r'https?://[^\s]+',  # URLs
            r'\b\w+@\w+\.\w+\b',  # Email addresses
            r'\d{4}-\d{2}-\d{2}',  # Dates
        ]
        
        pattern_score = sum(0.05 for pattern in complex_patterns 
                           if re.search(pattern, content))
        score += min(pattern_score, 0.2)
        
        return min(score, 1.0)
    
    def _generate_processing_hints(self, 
                                  response_type: ResponseType, 
                                  characteristics: Dict[str, Any], 
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate processing hints for optimal handling"""
        
        hints = {
            "use_streaming": False,
            "use_compression": False,
            "buffer_size": 4096,
            "chunk_size": 1024,
            "enable_caching": False,
            "parallel_processing": False
        }
        
        content_length = characteristics["content_length"]
        complexity = characteristics["complexity_score"]
        
        # Streaming recommendations
        if response_type == ResponseType.STREAMING_CANDIDATE or content_length > 5000:
            hints["use_streaming"] = True
            hints["chunk_size"] = min(2048, max(512, content_length // 50))
        
        # Compression recommendations
        if content_length > 2000 or complexity > 0.5:
            hints["use_compression"] = True
        
        # Buffer size recommendations
        if content_length > 10000:
            hints["buffer_size"] = min(32768, content_length // 4)
        elif content_length < 1000:
            hints["buffer_size"] = 1024
        
        # Caching recommendations
        if response_type in [ResponseType.JSON_DATA, ResponseType.TOOL_RESULTS] and complexity < 0.3:
            hints["enable_caching"] = True
        
        # Parallel processing for large structured data
        if (response_type in [ResponseType.TOOL_RESULTS, ResponseType.MIXED_CONTENT] and 
            content_length > 20000):
            hints["parallel_processing"] = True
        
        return hints
    
    def _estimate_processing_time(self, 
                                 response_type: ResponseType, 
                                 content_length: int, 
                                 complexity: float) -> float:
        """Estimate processing time in seconds"""
        
        base_time = 0.001  # 1ms base
        
        # Type-based multipliers
        type_multipliers = {
            ResponseType.SIMPLE_TEXT: 1.0,
            ResponseType.JSON_DATA: 1.5,
            ResponseType.TOOL_RESULTS: 2.0,
            ResponseType.ERROR_RESPONSE: 0.5,
            ResponseType.STREAMING_CANDIDATE: 1.2,
            ResponseType.LARGE_CONTENT: 3.0,
            ResponseType.MIXED_CONTENT: 2.5
        }
        
        type_mult = type_multipliers.get(response_type, 1.0)
        
        # Length-based processing time (roughly 1ms per 1000 characters)
        length_time = content_length / 1000000  # 1 second per million chars
        
        # Complexity multiplier
        complexity_mult = 1.0 + complexity * 2  # Up to 3x for high complexity
        
        total_time = (base_time + length_time) * type_mult * complexity_mult
        
        return max(total_time, 0.001)  # Minimum 1ms
    
    def _estimate_memory_requirements(self, 
                                     response_type: ResponseType, 
                                     content_length: int) -> int:
        """Estimate memory requirements in bytes"""
        
        base_memory = 1024  # 1KB base
        
        # Content memory (assume 2x for processing overhead)
        content_memory = content_length * 2
        
        # Type-based multipliers
        type_multipliers = {
            ResponseType.SIMPLE_TEXT: 1.0,
            ResponseType.JSON_DATA: 1.5,  # JSON parsing overhead
            ResponseType.TOOL_RESULTS: 2.0,  # Complex processing
            ResponseType.ERROR_RESPONSE: 0.5,  # Simpler handling
            ResponseType.STREAMING_CANDIDATE: 1.2,  # Streaming buffers
            ResponseType.LARGE_CONTENT: 1.8,  # Additional buffers
            ResponseType.MIXED_CONTENT: 2.2  # Multiple processing paths
        }
        
        type_mult = type_multipliers.get(response_type, 1.0)
        
        total_memory = int((base_memory + content_memory) * type_mult)
        
        return max(total_memory, 1024)  # Minimum 1KB
    
    def _create_cache_key(self, 
                         response_data: Union[str, Dict[str, Any]], 
                         context: Optional[Dict[str, Any]]) -> str:
        """Create cache key for response classification"""
        try:
            # Create hash-like key based on content characteristics
            if isinstance(response_data, dict):
                content_key = f"dict_{len(json.dumps(response_data))}"
            else:
                content = str(response_data) if response_data else ""
                content_key = f"str_{len(content)}_{hash(content[:100]) % 10000}"
            
            context_key = ""
            if context:
                context_key = f"_ctx_{hash(str(sorted(context.items()))) % 1000}"
            
            return f"{content_key}{context_key}"
            
        except Exception:
            # Fallback to simple key
            return f"fallback_{int(time.time() * 1000) % 100000}"
    
    def _default_classification(self) -> ResponseClassification:
        """Return default classification when classification fails"""
        return ResponseClassification(
            response_type=ResponseType.SIMPLE_TEXT,
            priority=ProcessingPriority.NORMAL,
            confidence=0.5,
            characteristics={"content_length": 0, "word_count": 0, "complexity_score": 0.0},
            processing_hints={"use_streaming": False, "buffer_size": 4096},
            estimated_processing_time=0.01,
            memory_requirements=4096
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get classifier statistics"""
        return {
            **self._stats.copy(),
            "cache_size": len(self._classification_cache),
            "cache_hit_rate": (
                self._stats["cache_hits"] / 
                max(self._stats["total_classifications"], 1) * 100
            ),
            "avg_processing_time": (
                self._stats["processing_time_ms"] / 
                max(self._stats["total_classifications"], 1)
            )
        }
    
    def clear_cache(self):
        """Clear classification cache"""
        self._classification_cache.clear()
        logger.info("🧹 Response classification cache cleared")
    
    def provide_feedback(self, cache_key: str, accuracy: float):
        """Provide feedback on classification accuracy"""
        try:
            self._stats["accuracy_feedback"].append({
                "cache_key": cache_key,
                "accuracy": accuracy,
                "timestamp": time.time()
            })
            
            # Keep only recent feedback
            if len(self._stats["accuracy_feedback"]) > 1000:
                self._stats["accuracy_feedback"] = self._stats["accuracy_feedback"][-500:]
                
        except Exception as e:
            logger.warning(f"⚠️ Feedback recording failed: {e}")


# Global response classifier instance
response_classifier = Phase2BResponseClassifier()


# Convenience functions for integration
def classify_response(response_data: Union[str, Dict[str, Any]], 
                     context: Optional[Dict[str, Any]] = None) -> ResponseClassification:
    """Classify response content"""
    return response_classifier.classify_response(response_data, context)


def get_classification_statistics() -> Dict[str, Any]:
    """Get classification statistics"""
    return response_classifier.get_statistics()


def clear_classification_cache():
    """Clear classification cache"""
    response_classifier.clear_cache()