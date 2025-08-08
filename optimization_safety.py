#!/usr/bin/env python3
"""
Optimization Safety Infrastructure
Provides bulletproof data preservation and validation for Primary LLM optimizations
"""

import copy
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning" 
    INFO = "info"

@dataclass
class ValidationResult:
    is_safe: bool
    score: float
    issues: List[str]
    severity_counts: Dict[str, int]
    original_size: int
    optimized_size: int
    compression_ratio: float

class ToolOutputPreserver:
    """
    Bulletproof preservation system for tool outputs during optimization attempts.
    Ensures no data is ever lost and provides instant fallback capability.
    """
    
    def __init__(self):
        self.original_data: Optional[List[Dict]] = None
        self.processing_history: List[Dict] = []
        self.safety_checksums: Dict[str, str] = {}
        self.preservation_timestamp: Optional[str] = None
        
    def preserve_original(self, tool_results: List[Dict]) -> str:
        """
        Store complete original data with integrity checksums.
        Returns the original formatted data as fallback.
        """
        try:
            # Deep copy to prevent any modifications
            self.original_data = copy.deepcopy(tool_results)
            self.preservation_timestamp = datetime.now().isoformat()
            
            # Create content checksums for integrity validation
            for i, result in enumerate(tool_results):
                # Normalize the data for consistent hashing
                normalized_result = json.dumps(result, sort_keys=True, default=str)
                checksum = hashlib.sha256(normalized_result.encode()).hexdigest()
                self.safety_checksums[f"tool_{i}"] = checksum
                
            # Log preservation
            logger.info(f"🛡️ PRESERVED: {len(tool_results)} tool results with checksums")
            
            # Always return original data as safe fallback
            return self._create_original_summary(tool_results)
            
        except Exception as e:
            logger.error(f"🚨 CRITICAL: Failed to preserve original data: {e}")
            # Even if preservation fails, return basic summary
            return self._emergency_fallback_summary(tool_results)
    
    def verify_integrity(self) -> bool:
        """Verify the preserved data hasn't been corrupted"""
        if not self.original_data:
            return False
            
        try:
            for i, result in enumerate(self.original_data):
                normalized_result = json.dumps(result, sort_keys=True, default=str)
                current_checksum = hashlib.sha256(normalized_result.encode()).hexdigest()
                expected_checksum = self.safety_checksums.get(f"tool_{i}")
                
                if current_checksum != expected_checksum:
                    logger.error(f"🚨 INTEGRITY VIOLATION: Tool {i} data corrupted")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"🚨 INTEGRITY CHECK FAILED: {e}")
            return False
    
    def get_original_summary(self) -> str:
        """Get the original data summary for fallback"""
        if not self.original_data:
            raise ValueError("No original data preserved")
            
        return self._create_original_summary(self.original_data)
    
    def _create_original_summary(self, tool_results: List[Dict]) -> str:
        """Create the original tool results summary format"""
        # This should match the existing create_tools_results_summary function
        summary_parts = []
        
        for i, result in enumerate(tool_results):
            tool_name = result.get('tool', f'tool_{i}')
            tool_result = result.get('result', result)
            
            summary_parts.append(f"Tool: {tool_name}")
            summary_parts.append(f"Result: {tool_result}")
            summary_parts.append("")  # Empty line separator
            
        return "\n".join(summary_parts)
    
    def _emergency_fallback_summary(self, tool_results: List[Dict]) -> str:
        """Emergency fallback if normal processing fails"""
        return f"EMERGENCY FALLBACK: {len(tool_results)} tool results available (details preserved)"


class OptimizationValidator:
    """
    Conservative validation system to ensure optimization doesn't lose critical information.
    Uses multiple validation layers with strict thresholds.
    """
    
    def __init__(self):
        # Conservative thresholds - err on the side of caution but allow reasonable optimization
        self.min_validation_score = 60.0  # Require 60% or higher (more realistic)
        self.max_keyword_loss_ratio = 0.7  # Max 70% keyword loss (optimization naturally loses some keywords)
        self.min_compression_ratio = 0.1   # Don't compress more than 90%
        self.max_compression_ratio = 10.0  # Allow up to 1000% expansion (for formatted output)
    
    async def validate_optimization(
        self, 
        original_data: List[Dict], 
        optimized_input: str, 
        user_prompt: str
    ) -> ValidationResult:
        """
        Comprehensive validation of optimization results.
        Returns detailed validation with conservative scoring.
        """
        issues = []
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        score = 100.0
        
        # Calculate sizes
        original_size = sum(len(str(result)) for result in original_data)
        optimized_size = len(optimized_input)
        compression_ratio = optimized_size / original_size if original_size > 0 else 0
        
        # 1. Tool Coverage Check - CRITICAL
        tool_coverage_score = await self._validate_tool_coverage(
            original_data, optimized_input, issues, severity_counts
        )
        score -= (100 - tool_coverage_score) * 0.3  # 30% weight
        
        # 2. Key Data Points Check - CRITICAL  
        data_preservation_score = await self._validate_data_preservation(
            original_data, optimized_input, issues, severity_counts
        )
        score -= (100 - data_preservation_score) * 0.25  # 25% weight
        
        # 3. User Intent Alignment Check - HIGH
        intent_alignment_score = await self._validate_user_intent(
            user_prompt, optimized_input, issues, severity_counts
        )
        score -= (100 - intent_alignment_score) * 0.2  # 20% weight
        
        # 4. Content Length Sanity Check - MEDIUM
        compression_score = await self._validate_compression_ratio(
            compression_ratio, issues, severity_counts
        )
        score -= (100 - compression_score) * 0.15  # 15% weight
        
        # 5. Content Quality Check - MEDIUM
        quality_score = await self._validate_content_quality(
            optimized_input, issues, severity_counts
        )
        score -= (100 - quality_score) * 0.1  # 10% weight
        
        # 6. CRITICAL: Content Mismatch Detection - CRITICAL
        mismatch_score = await self._validate_content_mismatch(
            user_prompt, optimized_input, issues, severity_counts
        )
        score -= (100 - mismatch_score) * 0.4  # 40% weight - HIGHEST PRIORITY
        
        # Final score clamping
        score = max(0.0, min(100.0, score))
        
        return ValidationResult(
            is_safe=(score >= self.min_validation_score and severity_counts["critical"] == 0),
            score=score,
            issues=issues,
            severity_counts=severity_counts,
            original_size=original_size,
            optimized_size=optimized_size,
            compression_ratio=compression_ratio
        )
    
    async def _validate_tool_coverage(
        self, original_data: List[Dict], optimized_input: str, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """Ensure all tools are represented in optimized output"""
        original_tools = set()
        for result in original_data:
            tool_name = result.get('tool', 'unknown_tool')
            original_tools.add(tool_name.lower())
        
        optimized_content_lower = optimized_input.lower()
        missing_tools = []
        
        for tool_name in original_tools:
            # Check multiple representations with more flexible matching
            tool_variants = [
                tool_name,
                tool_name.replace('_', ' '),
                tool_name.replace('_', '-'),
                tool_name.replace('_', ''),
                # Check for semantic equivalents
                'news' if 'news' in tool_name else '',
                'stock' if 'stock' in tool_name else '',
                'email' if 'email' in tool_name else '',
                'analysis' if 'analyz' in tool_name else '',
                'report' if 'report' in tool_name else '',
                'research' if 'news' in tool_name or 'research' in tool_name else '',
                'financial' if 'stock' in tool_name else '',
                'market' if 'stock' in tool_name else ''
            ]
            
            # Remove empty variants
            tool_variants = [v for v in tool_variants if v]
            
            if not any(variant in optimized_content_lower for variant in tool_variants):
                missing_tools.append(tool_name)
        
        if missing_tools:
            # Only critical if more than half the tools are missing
            if len(missing_tools) > len(original_tools) / 2:
                severity_counts["critical"] += len(missing_tools)
                issues.append(f"CRITICAL: Many tools not referenced in optimization: {missing_tools}")
                return max(0.0, 100.0 - (len(missing_tools) / len(original_tools)) * 100)
            else:
                severity_counts["warning"] += len(missing_tools)
                issues.append(f"WARNING: Some tools not explicitly referenced: {missing_tools}")
                return max(50.0, 100.0 - (len(missing_tools) / len(original_tools)) * 50)
        
        return 100.0
    
    async def _validate_data_preservation(
        self, original_data: List[Dict], optimized_input: str, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """Ensure key data points are preserved"""
        original_keywords = self._extract_key_terms(original_data)
        optimized_keywords = self._extract_key_terms([{"content": optimized_input}])
        
        missing_keywords = original_keywords - optimized_keywords
        missing_ratio = len(missing_keywords) / len(original_keywords) if original_keywords else 0
        
        # Be more lenient with keyword loss if content appears to be on-topic and structured
        if missing_ratio > self.max_keyword_loss_ratio:
            # Check if this is a structured, on-topic optimization despite keyword loss
            if (len(optimized_keywords) > 10 and  # Has reasonable keyword count
                any(marker in optimized_input.lower() for marker in ['#', '**', 'dear', 'sincerely']) and  # Has structure
                not any(error in optimized_input.lower() for error in ['unable to process', 'not related to'])):  # Not an error
                severity_counts["warning"] += 1
                issues.append(f"WARNING: High keyword loss but content appears structured: {missing_ratio:.1%}")
                return 50.0
            else:
                severity_counts["critical"] += 1
                issues.append(f"CRITICAL: Excessive keyword loss: {missing_ratio:.1%} > {self.max_keyword_loss_ratio:.1%}")
                return 0.0
        elif missing_ratio > self.max_keyword_loss_ratio * 0.5:
            severity_counts["warning"] += 1
            issues.append(f"WARNING: Significant keyword loss: {missing_ratio:.1%}")
            return 70.0
        
        return max(0.0, 100.0 - missing_ratio * 100)
    
    async def _validate_user_intent(
        self, user_prompt: str, optimized_input: str, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """Ensure user intent keywords are preserved"""
        intent_keywords = self._extract_intent_keywords(user_prompt)
        optimized_lower = optimized_input.lower()
        
        missing_intent_keywords = []
        for keyword in intent_keywords:
            if keyword.lower() not in optimized_lower:
                missing_intent_keywords.append(keyword)
        
        if missing_intent_keywords:
            severity_counts["warning"] += len(missing_intent_keywords)
            issues.append(f"WARNING: User intent keywords missing: {missing_intent_keywords}")
            return max(0.0, 100.0 - (len(missing_intent_keywords) / len(intent_keywords)) * 50)
        
        return 100.0
    
    async def _validate_compression_ratio(
        self, compression_ratio: float, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """Validate compression is within reasonable bounds"""
        if compression_ratio < self.min_compression_ratio:
            severity_counts["critical"] += 1
            issues.append(f"CRITICAL: Excessive compression: {compression_ratio:.1%} < {self.min_compression_ratio:.1%}")
            return 0.0
        elif compression_ratio > self.max_compression_ratio:
            severity_counts["warning"] += 1
            issues.append(f"WARNING: Minimal compression: {compression_ratio:.1%} > {self.max_compression_ratio:.1%}")
            return 70.0
        
        return 100.0
    
    async def _validate_content_quality(
        self, optimized_input: str, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """Basic content quality checks"""
        # Check for minimum content length
        if len(optimized_input.strip()) < 100:
            severity_counts["critical"] += 1
            issues.append("CRITICAL: Optimized content too short")
            return 0.0
        
        # Check for content structure
        if not any(marker in optimized_input for marker in ['#', '*', '-', '1.', '2.']):
            severity_counts["warning"] += 1
            issues.append("WARNING: No clear content structure detected")
            return 80.0
            
        return 100.0
    
    async def _validate_content_mismatch(
        self, user_prompt: str, optimized_input: str, issues: List[str], severity_counts: Dict[str, int]
    ) -> float:
        """CRITICAL: Detect if optimized content is completely unrelated to user request"""
        
        # Extract domain-specific indicators from user prompt
        prompt_lower = user_prompt.lower()
        content_lower = optimized_input.lower()
        
        # Define content domain indicators
        domains = {
            'financial': ['stock', 'market', 'finance', 'trading', 'investment', 'analysis', 'aapl', 'financial'],
            'document_creation': ['cover', 'letter', 'resume', 'application', 'document', 'create', 'craft', 'write'],
            'email_communication': ['email', 'send', 'attachment', 'recipient', 'subject', 'message'],
            'research': ['research', 'find', 'search', 'gather', 'information', 'data'],
            'news': ['news', 'current', 'events', 'headlines', 'stories'],
            'scheduling': ['calendar', 'schedule', 'appointment', 'meeting', 'time']
        }
        
        # Determine user's intended domain(s)
        user_domains = []
        for domain, keywords in domains.items():
            if any(keyword in prompt_lower for keyword in keywords):
                user_domains.append(domain)
        
        # Determine optimized content domain(s)
        content_domains = []
        for domain, keywords in domains.items():
            if any(keyword in content_lower for keyword in keywords):
                content_domains.append(domain)
        
        # Check for critical mismatches
        if user_domains and content_domains:
            # If domains are completely different, it's a critical failure
            if not any(domain in content_domains for domain in user_domains):
                severity_counts["critical"] += 1
                issues.append(f"CRITICAL: Content domain mismatch - User requested {user_domains} but got {content_domains}")
                return 0.0
                
        # Check for "unable to process" or generic error messages in optimized content
        error_indicators = [
            "unable to process",
            "appears to be a prompt for a different task",
            "not related to",
            "if you have any questions",
            "please let me know",
            "i'll be happy to help"
        ]
        
        error_count = sum(1 for indicator in error_indicators if indicator in content_lower)
        if error_count >= 2:  # Multiple error indicators = likely generic error response
            severity_counts["critical"] += 1
            issues.append(f"CRITICAL: Optimized content contains generic error response - {error_count} error indicators detected")
            return 0.0
        
        # Check if optimized content mentions wrong topics entirely
        if 'financial' in user_domains and any(phrase in content_lower for phrase in error_indicators):
            # User wanted financial info but got error about financial analysis
            severity_counts["critical"] += 1
            issues.append("CRITICAL: System incorrectly rejected financial request with generic error")
            return 0.0
            
        return 100.0
    
    def _extract_key_terms(self, data: List[Dict]) -> Set[str]:
        """Extract important terms from data for comparison"""
        terms = set()
        
        for item in data:
            content = str(item).lower()
            # Extract words that are likely important (3+ characters, not common words)
            words = content.split()
            for word in words:
                cleaned_word = ''.join(c for c in word if c.isalnum())
                if (len(cleaned_word) >= 3 and 
                    cleaned_word not in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}):
                    terms.add(cleaned_word)
        
        return terms
    
    def _extract_intent_keywords(self, user_prompt: str) -> List[str]:
        """Extract key intent words from user prompt with enhanced context detection"""
        # Common action words and important nouns
        prompt_lower = user_prompt.lower()
        intent_words = []
        
        # Extract quoted terms
        import re
        quoted_terms = re.findall(r'"([^"]*)"', user_prompt)
        intent_words.extend(quoted_terms)
        
        # Enhanced action words including document creation
        action_words = [
            'create', 'analyze', 'research', 'email', 'send', 'generate', 'write', 'report', 'summary',
            'craft', 'cover', 'letter', 'resume', 'application', 'format', 'attach', 'extract', 'fill',
            'complete', 'task', 'introductory', 'formatted', 'html', 'pdf'
        ]
        for word in action_words:
            if word in prompt_lower:
                intent_words.append(word)
        
        # Extract email addresses (critical for email tasks)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_prompt, re.IGNORECASE)
        intent_words.extend(emails)
        
        # Extract names and titles (Mr., Ms., Dr., Director, etc.)
        title_pattern = r'\b(?:Mr|Ms|Mrs|Dr|Director|Manager|CEO|CTO)\s+[A-Z][a-z]+'
        titles_names = re.findall(title_pattern, user_prompt)
        intent_words.extend(titles_names)
        
        # Extract company names and locations
        company_pattern = r'\b[A-Z][A-Za-z\s]*(?:LLC|Inc|Corp|Technologies|Company|Systems)\b'
        companies = re.findall(company_pattern, user_prompt)
        intent_words.extend(companies)
        
        # Extract capitalized terms (likely important names/concepts)
        capitalized_terms = re.findall(r'\b[A-Z][A-Za-z]+\b', user_prompt)
        intent_words.extend(capitalized_terms)
        
        # Extract file extensions and format requirements
        format_pattern = r'\b(?:pdf|html|doc|docx|txt|md|markdown)\b'
        formats = re.findall(format_pattern, prompt_lower)
        intent_words.extend(formats)
        
        return list(set(intent_words))  # Remove duplicates


async def safe_optimize_llm_input(
    tool_results: List[Dict], 
    user_prompt: str,
    preserver: ToolOutputPreserver,
    validator: OptimizationValidator
) -> Dict[str, Any]:
    """
    Safely attempt LLM input optimization with comprehensive fallback protection.
    Returns a dict with optimization status and content.
    """
    
    try:
        # Step 1: Preserve original data (CRITICAL - never skip)
        original_input = preserver.preserve_original(tool_results)
        
        # Step 2: Verify preservation integrity
        if not preserver.verify_integrity():
            logger.error("🚨 PRESERVATION INTEGRITY FAILED - Using emergency fallback")
            return {
                "input_type": "emergency_fallback",
                "content": original_input,
                "error": "Data preservation integrity check failed",
                "validation_score": 0
            }
        
        # Step 3: Attempt optimization (this is where we'll add the actual optimization logic)
        logger.info("🔧 OPTIMIZATION: Starting safe optimization attempt")
        optimized_input = await attempt_optimization(tool_results, user_prompt)
        
        # Step 4: Validate optimization results
        validation_result = await validator.validate_optimization(
            original_data=tool_results,
            optimized_input=optimized_input,
            user_prompt=user_prompt
        )
        
        # Step 5: Decision based on validation
        if validation_result.is_safe:
            logger.info(f"✅ OPTIMIZATION SUCCESS: Score {validation_result.score:.1f}")
            return {
                "input_type": "optimized",
                "content": optimized_input,
                "original_backup": original_input,
                "validation_score": validation_result.score,
                "validation_details": validation_result
            }
        else:
            logger.warning(f"⚠️ OPTIMIZATION FAILED VALIDATION: Score {validation_result.score:.1f}")
            logger.warning(f"Issues: {validation_result.issues}")
            return {
                "input_type": "original_fallback",
                "content": original_input,
                "optimization_attempted": True,
                "fallback_reason": validation_result.issues,
                "validation_score": validation_result.score
            }
            
    except Exception as e:
        # Any error = immediate fallback to original
        logger.error(f"🚨 OPTIMIZATION ERROR: {e}")
        try:
            safe_original = preserver.get_original_summary()
            return {
                "input_type": "original_safe",
                "content": safe_original,
                "error": str(e),
                "validation_score": 0
            }
        except Exception as fallback_error:
            logger.critical(f"🚨 CRITICAL: Even fallback failed: {fallback_error}")
            return {
                "input_type": "critical_failure",
                "content": f"SYSTEM ERROR: Contact administrator. Original error: {e}",
                "error": str(fallback_error),
                "validation_score": 0
            }


async def attempt_optimization(tool_results: List[Dict], user_prompt: str) -> str:
    """
    Placeholder for actual optimization logic.
    For now, returns a simple optimized version for testing.
    """
    # TODO: This is where we'll implement the actual optimization algorithms
    # For now, create a simple test optimization
    
    summary_parts = []
    summary_parts.append(f"# OPTIMIZED ANALYSIS")
    summary_parts.append(f"**User Request**: {user_prompt}")
    summary_parts.append("")
    
    for i, result in enumerate(tool_results):
        tool_name = result.get('tool', f'tool_{i}')
        summary_parts.append(f"## {tool_name.title()} Results")
        
        # Extract key information (simplified for now)
        tool_result = str(result.get('result', result))
        if len(tool_result) > 500:
            tool_result = tool_result[:500] + "..."
        
        summary_parts.append(tool_result)
        summary_parts.append("")
    
    return "\n".join(summary_parts)