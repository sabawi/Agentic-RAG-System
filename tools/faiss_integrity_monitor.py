#!/usr/bin/env python3
"""
FAISS-SQLite Integrity Monitor
Detects corruption and automatically rebuilds indices in production
"""

import asyncio
import logging
import json
import hashlib
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sqlite3
import numpy as np

logger = logging.getLogger(__name__)

class FAISSIntegrityMonitor:
    """
    Production-grade integrity monitoring for FAISS-SQLite synchronization
    """
    
    def __init__(self, document_store):
        self.store = document_store
        self.metadata_db = document_store.metadata_db
        self.faiss_index = document_store.faiss_index
        self.corruption_threshold = 0.05  # 5% mismatch triggers rebuild (applies to both count sync and lookup corruption)
        self.max_sample_size = 100  # Sample size for integrity checks
        
    async def comprehensive_integrity_check(self) -> Dict[str, any]:
        """
        Comprehensive integrity check between FAISS and SQLite
        Returns detailed status and corruption indicators
        """
        start_time = time.time()
        logger.info("🔍 Starting comprehensive FAISS-SQLite integrity check")
        
        result = {
            'timestamp': time.time(),
            'status': 'HEALTHY',
            'issues_found': [],
            'metrics': {},
            'recommendations': [],
            'corruption_detected': False,
            'rebuild_required': False
        }
        
        try:
            # Check 1: Basic count synchronization
            count_check = await self._check_count_synchronization()
            result['metrics']['count_sync'] = count_check
            
            if not count_check['synchronized']:
                result['issues_found'].append('COUNT_MISMATCH')
                result['status'] = 'CORRUPTED'
                result['corruption_detected'] = True
                
            # Check 2: Index range validation
            range_check = await self._check_index_range_validity()
            result['metrics']['range_validity'] = range_check
            
            if not range_check['valid']:
                result['issues_found'].append('INDEX_RANGE_INVALID')
                result['status'] = 'CORRUPTED'
                result['corruption_detected'] = True
                
            # Check 3: Sample-based lookup verification
            lookup_check = await self._check_sample_lookup_integrity()
            result['metrics']['lookup_integrity'] = lookup_check
            
            if lookup_check['corruption_rate'] > self.corruption_threshold:
                result['issues_found'].append('LOOKUP_CORRUPTION')
                result['status'] = 'CORRUPTED'
                result['corruption_detected'] = True
                
            # Check 4: Embedding consistency validation
            if result['status'] != 'CORRUPTED':  # Only if basic checks pass
                embedding_check = await self._check_embedding_consistency()
                result['metrics']['embedding_consistency'] = embedding_check
                
                if not embedding_check['consistent']:
                    result['issues_found'].append('EMBEDDING_INCONSISTENCY')
                    result['status'] = 'DEGRADED'
            
            # Determine if rebuild is required
            if result['corruption_detected']:
                result['rebuild_required'] = True
                result['recommendations'].append('IMMEDIATE_REBUILD_REQUIRED')
                
            elif result['status'] == 'DEGRADED':
                result['recommendations'].append('SCHEDULED_REBUILD_RECOMMENDED')
                
            else:
                result['recommendations'].append('NO_ACTION_REQUIRED')
                
        except Exception as e:
            logger.error(f"❌ Integrity check failed: {e}")
            result['status'] = 'ERROR'
            result['error'] = str(e)
            result['rebuild_required'] = True
            
        result['check_duration'] = time.time() - start_time
        logger.info(f"✅ Integrity check complete: {result['status']} ({result['check_duration']:.2f}s)")
        
        return result
    
    async def _check_count_synchronization(self) -> Dict[str, any]:
        """Check if FAISS and SQLite have matching record counts"""
        cursor = self.metadata_db.cursor()
        
        # Get SQLite counts
        cursor.execute("SELECT COUNT(*) FROM chunks")
        sqlite_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE faiss_index IS NOT NULL")
        sqlite_indexed = cursor.fetchone()[0]
        
        # Get FAISS count
        faiss_total = self.faiss_index.ntotal
        
        # Calculate count mismatch percentage (use max to avoid division by zero)
        total_count = max(sqlite_indexed, faiss_total, 1)
        mismatch_percentage = abs(sqlite_indexed - faiss_total) / total_count
        
        # Consider synchronized if mismatch is within tolerance (5%)
        synchronized = mismatch_percentage <= self.corruption_threshold
        
        return {
            'sqlite_total_chunks': sqlite_total,
            'sqlite_indexed_chunks': sqlite_indexed,
            'faiss_total_vectors': faiss_total,
            'synchronized': synchronized,
            'mismatch_percentage': mismatch_percentage,
            'missing_in_faiss': max(0, sqlite_indexed - faiss_total),
            'orphaned_in_faiss': max(0, faiss_total - sqlite_indexed)
        }
    
    async def _check_index_range_validity(self) -> Dict[str, any]:
        """Verify FAISS indices in SQLite are within valid range"""
        cursor = self.metadata_db.cursor()
        
        cursor.execute("""
            SELECT MIN(faiss_index), MAX(faiss_index), COUNT(DISTINCT faiss_index)
            FROM chunks WHERE faiss_index IS NOT NULL
        """)
        min_idx, max_idx, unique_count = cursor.fetchone()
        
        faiss_max_valid = self.faiss_index.ntotal - 1
        
        # Check for indices beyond FAISS range
        cursor.execute("""
            SELECT COUNT(*) FROM chunks 
            WHERE faiss_index IS NOT NULL AND faiss_index >= ?
        """, (self.faiss_index.ntotal,))
        invalid_indices = cursor.fetchone()[0]
        
        return {
            'min_index': min_idx,
            'max_index': max_idx,
            'unique_indices': unique_count,
            'faiss_max_valid': faiss_max_valid,
            'invalid_indices_count': invalid_indices,
            'valid': invalid_indices == 0 and (max_idx is None or max_idx <= faiss_max_valid)
        }
    
    async def _check_sample_lookup_integrity(self) -> Dict[str, any]:
        """Sample random FAISS indices and verify SQLite lookups work"""
        cursor = self.metadata_db.cursor()
        
        # Get sample of FAISS indices from SQLite
        cursor.execute("""
            SELECT faiss_index, chunk_id FROM chunks 
            WHERE faiss_index IS NOT NULL 
            ORDER BY RANDOM() 
            LIMIT ?
        """, (self.max_sample_size,))
        
        sample_indices = cursor.fetchall()
        
        if not sample_indices:
            return {'corruption_rate': 1.0, 'sample_size': 0, 'lookups_failed': 0}
        
        failed_lookups = 0
        
        for faiss_idx, expected_chunk_id in sample_indices:
            # Verify reverse lookup works
            cursor.execute("""
                SELECT chunk_id FROM chunks WHERE faiss_index = ?
            """, (faiss_idx,))
            
            result = cursor.fetchone()
            if not result or result[0] != expected_chunk_id:
                failed_lookups += 1
        
        corruption_rate = failed_lookups / len(sample_indices)
        
        return {
            'sample_size': len(sample_indices),
            'lookups_failed': failed_lookups,
            'corruption_rate': corruption_rate,
            'status': 'HEALTHY' if corruption_rate == 0 else 'CORRUPTED'
        }
    
    async def _check_embedding_consistency(self) -> Dict[str, any]:
        """Verify embedding generation produces consistent results"""
        cursor = self.metadata_db.cursor()
        
        # Get a small sample for embedding consistency check
        cursor.execute("""
            SELECT content FROM chunks 
            WHERE LENGTH(content) > 50 
            ORDER BY RANDOM() 
            LIMIT 5
        """)
        
        sample_content = [row[0] for row in cursor.fetchall()]
        
        if not sample_content:
            return {'consistent': True, 'sample_size': 0}
        
        try:
            # Generate embeddings twice and compare
            embeddings1 = await self.store._generate_embeddings(sample_content)
            await asyncio.sleep(0.1)  # Small delay
            embeddings2 = await self.store._generate_embeddings(sample_content)
            
            if not embeddings1 or not embeddings2:
                return {'consistent': False, 'error': 'Embedding generation failed'}
            
            # Check if embeddings are identical (they should be for same input)
            consistent = True
            for emb1, emb2 in zip(embeddings1, embeddings2):
                if not np.allclose(emb1, emb2, rtol=1e-10):
                    consistent = False
                    break
            
            return {
                'consistent': consistent,
                'sample_size': len(sample_content),
                'embedding_dimension': len(embeddings1[0]) if embeddings1 else 0
            }
            
        except Exception as e:
            return {'consistent': False, 'error': str(e)}
    
    async def automatic_rebuild_if_needed(self, integrity_result: Dict[str, any]) -> bool:
        """
        Automatically rebuild FAISS index if corruption is detected
        Returns True if rebuild was performed
        """
        if not integrity_result.get('rebuild_required', False):
            logger.info("✅ No rebuild required - integrity check passed")
            return False
        
        logger.warning("🚨 CORRUPTION DETECTED - Starting automatic rebuild")
        logger.warning(f"Issues found: {integrity_result['issues_found']}")
        
        try:
            rebuild_result = await self._perform_full_rebuild()
            
            if rebuild_result['success']:
                logger.info("✅ Automatic rebuild completed successfully")
                
                # Verify rebuild worked
                post_rebuild_check = await self.comprehensive_integrity_check()
                if post_rebuild_check['status'] == 'HEALTHY':
                    logger.info("✅ Post-rebuild integrity check passed")
                    return True
                else:
                    logger.error("❌ Post-rebuild integrity check failed - manual intervention required")
                    return False
            else:
                logger.error(f"❌ Automatic rebuild failed: {rebuild_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Critical error during automatic rebuild: {e}")
            return False
    
    async def _perform_full_rebuild(self) -> Dict[str, any]:
        """Perform complete FAISS index rebuild from SQLite data"""
        start_time = time.time()
        logger.info("🔄 Starting full FAISS index rebuild")
        
        try:
            # Step 1: Clear existing FAISS index
            logger.info("🧹 Clearing existing FAISS index")
            self.faiss_index.reset()
            
            # Step 2: Get all chunks needing indexing
            cursor = self.metadata_db.cursor()
            cursor.execute("""
                SELECT chunk_id, content 
                FROM chunks 
                ORDER BY chunk_id
            """)
            
            all_chunks = cursor.fetchall()
            total_chunks = len(all_chunks)
            
            if total_chunks == 0:
                return {'success': True, 'chunks_processed': 0, 'duration': 0}
            
            logger.info(f"📊 Rebuilding index for {total_chunks} chunks")
            
            # Step 3: Process in batches
            batch_size = 50  # Smaller batches for stability
            processed = 0
            
            for i in range(0, total_chunks, batch_size):
                batch = all_chunks[i:i + batch_size]
                batch_content = [chunk[1] for chunk in batch]
                
                # Generate embeddings
                embeddings = await self.store._generate_embeddings(batch_content)
                
                if not embeddings or len(embeddings) != len(batch):
                    raise Exception(f"Embedding generation failed for batch {i//batch_size + 1}")
                
                # Add to FAISS index
                embeddings_array = np.array(embeddings).astype('float32')
                start_idx = self.faiss_index.ntotal
                self.faiss_index.add(embeddings_array)
                
                # Update SQLite with new FAISS indices
                for j, (chunk_id, content) in enumerate(batch):
                    new_faiss_idx = start_idx + j
                    cursor.execute("""
                        UPDATE chunks 
                        SET faiss_index = ? 
                        WHERE chunk_id = ?
                    """, (new_faiss_idx, chunk_id))
                
                self.metadata_db.commit()
                processed += len(batch)
                
                if processed % 200 == 0:  # Progress logging
                    logger.info(f"📊 Rebuild progress: {processed}/{total_chunks} ({100*processed/total_chunks:.1f}%)")
            
            # Step 4: Save the rebuilt index
            await self.store._save_index()
            
            duration = time.time() - start_time
            logger.info(f"✅ Rebuild complete: {processed} chunks in {duration:.2f}s")
            
            return {
                'success': True,
                'chunks_processed': processed,
                'final_index_size': self.faiss_index.ntotal,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Rebuild failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_integrity_report(self, check_result: Dict[str, any]) -> str:
        """Generate human-readable integrity report"""
        status_emoji = {
            'HEALTHY': '✅',
            'DEGRADED': '⚠️',
            'CORRUPTED': '🚨',
            'ERROR': '❌'
        }
        
        emoji = status_emoji.get(check_result['status'], '❓')
        
        report = [
            f"{emoji} FAISS-SQLite Integrity Report",
            "=" * 40,
            f"Status: {check_result['status']}",
            f"Check Duration: {check_result.get('check_duration', 0):.2f}s",
            ""
        ]
        
        if check_result.get('metrics'):
            report.append("📊 Metrics:")
            for check_name, metrics in check_result['metrics'].items():
                report.append(f"  {check_name}: {metrics}")
            report.append("")
        
        if check_result.get('issues_found'):
            report.append("🚨 Issues Found:")
            for issue in check_result['issues_found']:
                report.append(f"  - {issue}")
            report.append("")
        
        if check_result.get('recommendations'):
            report.append("💡 Recommendations:")
            for rec in check_result['recommendations']:
                report.append(f"  - {rec}")
        
        return "\\n".join(report)

# Integration function for document_interrogator.py
async def check_and_repair_faiss_integrity(document_store) -> bool:
    """
    Main function to check and repair FAISS integrity
    Returns True if system is healthy after check/repair
    """
    monitor = FAISSIntegrityMonitor(document_store)
    
    # Run comprehensive check
    integrity_result = await monitor.comprehensive_integrity_check()
    
    # Log the report
    report = monitor.get_integrity_report(integrity_result)
    logger.info(f"\\n{report}")
    
    # Auto-repair if needed
    if integrity_result.get('rebuild_required', False):
        rebuild_success = await monitor.automatic_rebuild_if_needed(integrity_result)
        return rebuild_success
    
    return integrity_result['status'] in ['HEALTHY', 'DEGRADED']