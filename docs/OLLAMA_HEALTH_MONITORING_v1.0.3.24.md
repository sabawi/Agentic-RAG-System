# Ollama Health Monitoring & Auto-Recovery
## Comprehensive Embedding Service Stability v1.0.3.24

**System Version:** v1.0.3.24+
**Date:** October 24, 2025
**Status:** ✅ IMPLEMENTED

---

## 🚨 Problem Identification

During document scanning, the system was experiencing failures at approximately **1650-1657 embeddings** processed:

```
Progress: 1640 → 1650 → 1655 → 1657 → HTTP 500 error
Batch sizes tested: 10 → 5 → 2 → 1 → ALL FAILED

Key Finding: Even single embedding requests (batch_size=1) failed
Conclusion: NOT batch size issue - Ollama service becoming unhealthy
```

**Root Cause:** Ollama embedding service was degrading after processing ~1650-1700 embeddings, likely due to:
- Memory accumulation/leak
- Internal state corruption
- Connection pool exhaustion
- Resource limit being hit

---

## ✅ Solution Implemented (v1.0.3.24)

### **Component 1: Ollama Health Detection**

**Location:** `document_interrogator.py` - Batch failure handler

```python
# When a batch fails, immediately check if Ollama is healthy
is_service_healthy = await self._check_embedding_service_health()
logger.warning(f"🔍 Ollama health check: {'✅ HEALTHY' if is_service_healthy else '❌ UNHEALTHY'}")
```

**What it does:**
- Makes HTTP request to Ollama health endpoint
- Detects if service is responsive
- Distinguishes between "batch failed" vs "service unhealthy"

---

### **Component 2: Automatic Ollama Restart**

**Location:** `document_interrogator.py` - Lines 1026-1062

**Behavior:**
```
Batch fails → Check Ollama health
  ↓
If UNHEALTHY:
  → Attempt restart (up to 2 times)
  → Wait 15 seconds for stabilization
  → Reset batch_size to original value
  → Retry the failed batch
  → If restart succeeds: CONTINUE PROCESSING
  → If restart fails: ABORT with recommendations
  ↓
If HEALTHY:
  → Reduce batch_size (10 → 5 → 2 → 1)
  → Retry with smaller batch
  → Eventually abort if batch_size=1 still fails
```

**Restart Logic:**
```python
for restart_attempt in range(2):  # Try 2 times
    logger.info(f"🔄 Ollama restart attempt {restart_attempt + 1}/2...")
    if await self._restart_embedding_service():
        logger.info(f"✅ Ollama restarted successfully")
        restart_success = True
        break
```

---

### **Component 3: Periodic Health Checks**

**Location:** `document_interrogator.py` - Lines 1086-1098

**Behavior:**
- Every 10 successful batches, check Ollama health
- Detects degradation BEFORE it causes batch failure
- Provides early warning to admin

**Example Log:**
```
✅ Completed batch: 100 embeddings (progress: 1000/1961)
🏥 Periodic health check at batch 100...
   ⚠️ Ollama service degrading at batch 100
   This may indicate upcoming failures - monitoring closely
```

---

## 📊 New Processing Flow

```
[Start Scan]
  ↓
[Process Batch] (size=10)
  ↓
[Success?]
  ├─ YES: Add to results
  │        ├─ Every 10 batches: Health check (periodic)
  │        ├─ Sleep 5 seconds
  │        └─ Next batch
  │
  └─ NO: Check Ollama Health
           ├─ UNHEALTHY?
           │  └─ Restart Ollama
           │     ├─ Success? Reset size to 10, retry
           │     └─ Fail? Abort with recommendations
           │
           └─ HEALTHY?
              └─ Reduce batch_size
                 ├─ 10 → 5 (retry)
                 ├─ 5 → 2 (retry)
                 ├─ 2 → 1 (retry)
                 └─ 1: Still failed? Abort
```

---

## 🎯 Expected Behavior

### **Scenario 1: Ollama Becomes Unhealthy (Most Likely)**

```
✅ Completed batch: 10 embeddings (progress: 1650/1961)
✅ Completed batch: 10 embeddings (progress: 1660/1961)
❌ Embedding generation failed: 500
❌ Batch failure: task 3 returned None
🔍 Ollama health check: ❌ UNHEALTHY
🚨 EMBEDDING SERVICE UNHEALTHY - Attempting restart
   Progress: 1660/1961 embeddings processed
   Current batch_size: 10
🔄 Ollama restart attempt 1/2...
✅ Ollama restarted successfully
⏳ Waiting 15 seconds for Ollama to stabilize...
📈 Service recovered - resetting batch_size to 10
✅ Completed batch: 10 embeddings (progress: 1670/1961)
✅ Completed batch: 10 embeddings (progress: 1680/1961)
... continues to completion
```

**Result:** ✅ **SCAN COMPLETES SUCCESSFULLY**

---

### **Scenario 2: Batch Fails But Ollama Still Healthy**

```
❌ Embedding generation failed: 500
❌ Batch failure: task 5 returned None
🔍 Ollama health check: ✅ HEALTHY
⚠️ Service healthy but batch failed - reducing batch_size: 10 → 5
✅ Completed batch: 5 embeddings (progress: 1655/1961)
```

**Result:** ✅ Graceful degradation, scan continues

---

### **Scenario 3: Ollama Cannot Restart**

```
🚨 EMBEDDING SERVICE UNHEALTHY - Attempting restart
🔄 Ollama restart attempt 1/2...
❌ Restart attempt 1 failed
🔄 Ollama restart attempt 2/2...
❌ Restart attempt 2 failed
❌ Failed to restart Ollama after 2 attempts
🛑 RECOMMENDATION: Manually restart Ollama service
   Command: systemctl restart ollama
   Or check: ps aux | grep ollama
```

**Result:** ⚠️ **SCAN ABORTS** (admin must manually restart Ollama)

---

## 🔧 Admin Actions Required

### **If Scan Fails with Ollama Issue**

**Check 1: Is Ollama running?**
```bash
ps aux | grep ollama
# Should show: ollama serve process
```

**Check 2: Manual Ollama restart**
```bash
# Option A: Using systemctl
sudo systemctl restart ollama
sleep 10

# Option B: Manual restart
OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

**Check 3: Verify Ollama is responding**
```bash
curl http://localhost:11434/api/tags
# Should return list of models
```

**Check 4: Restart the scan**
```bash
# Server will automatically retry on next scan interval (60 min)
# Or manually restart
./stop_complete.sh && ./start_complete.sh
```

### **If Issues Persist**

Check Ollama logs:
```bash
# Ollama logs location depends on installation
# Ubuntu/Linux: journalctl -u ollama -f
journalctl -u ollama -f | tail -100

# Or check Ollama's own logs
# Usually in ~/.ollama/logs/
```

---

## 📈 Testing the New Behavior

### **Test 1: Normal Completion**

```bash
# 1. Start fresh scan
./stop_complete.sh && ./start_complete.sh

# 2. Monitor logs
tail -f logs/server_complete.log | grep -E "batch|health|progress"

# 3. Expected: Should see periodic health checks and completion
```

### **Test 2: Simulate Ollama Failure** (for testing restart logic)

```bash
# 1. Start scan
# 2. When it reaches batch 66-67, manually stop Ollama
sudo systemctl stop ollama

# 3. Observe logs - system should detect unhealthy service
# 4. System should attempt restart
# 5. After Ollama restarts, scan should resume
```

### **Test 3: Verify Health Checks Work**

```bash
# Watch logs for periodic health checks
tail -f logs/server_complete.log | grep "Periodic health check\|health"

# Every 10 batches (at batch 10, 20, 30, etc.), should see:
# 🏥 Periodic health check at batch 10...
#    ✅ Ollama service healthy
```

---

## 🛡️ Safeguards Included

| Safeguard | Implementation | Benefit |
|-----------|---|---|
| **Health Detection** | HTTP check to `/api/tags` | Detects service issues immediately |
| **Auto-Restart** | Runs `ollama serve` command | Recovers from transient failures |
| **Retry Logic** | 2 restart attempts | Handles temporary issues |
| **Stabilization Wait** | 15-second delay after restart | Allows Ollama to fully initialize |
| **Batch Recovery** | Reset to original size after restart | Doesn't give up on progress |
| **Periodic Checks** | Health check every 10 batches | Early detection of degradation |
| **Clear Logging** | Detailed error messages | Admin knows exactly what happened |

---

## 📊 Impact on Processing

### **Timeline for 1961 Chunks**

**Without Ollama Issues:**
```
Total time: ~27-30 minutes
Batches: 196 batches of 10
No interruptions
```

**With Ollama Restart (once):**
```
Processing: 1650 embeddings (~24 min)
Ollama unhealthy: Restart (2-3 min)
Resume: Remaining 311 embeddings (~4 min)
Total time: ~31-34 minutes
Result: ✅ STILL COMPLETES
```

**With Multiple Ollama Restarts:**
- Each restart adds 2-3 minutes
- System can recover from up to several failures
- Eventually aborts only if restart fails

---

## 📝 Log Message Reference

### **Success Messages**
```
✅ Ollama restarted successfully
✅ Completed batch: N embeddings (progress: X/1961)
✅ Ollama service healthy (from periodic check)
```

### **Warning Messages**
```
⚠️ Ollama service degrading at batch X
⚠️ Service healthy but batch failed - reducing batch_size
⏳ Waiting 15 seconds for Ollama to stabilize
```

### **Error Messages**
```
🚨 EMBEDDING SERVICE UNHEALTHY - Attempting restart
❌ Restart attempt X failed
❌ Failed to restart Ollama after 2 attempts
🛑 RECOMMENDATION: Manually restart Ollama service
```

---

## 🔄 Recovery Scenarios

### **Scenario A: Transient Ollama Timeout**
- **Cause:** Ollama becomes temporarily unresponsive
- **Detection:** Health check fails
- **Recovery:** Automatic restart
- **Result:** ✅ Scan resumes

### **Scenario B: Batch Fails But Service OK**
- **Cause:** Single embedding fails despite healthy service
- **Detection:** Health check passes
- **Recovery:** Reduce batch size and retry
- **Result:** ✅ Continues with smaller batches

### **Scenario C: Ollama Restart Fails**
- **Cause:** Critical Ollama issue
- **Detection:** 2 restart attempts fail
- **Recovery:** Abort with clear recommendations
- **Result:** ⚠️ Admin must manually intervene

---

## 🎯 Next Steps if Still Failing

**If you're still seeing failures at ~1650 embeddings even with auto-restart:**

1. **Check if Ollama is actually restarting:**
   ```bash
   # Monitor Ollama process
   watch -n 1 'ps aux | grep "ollama serve" | grep -v grep'
   ```

2. **Check Ollama logs during restart:**
   ```bash
   journalctl -u ollama -f
   # Watch for startup messages
   ```

3. **Check system resources during scan:**
   ```bash
   # Monitor memory/CPU
   watch -n 2 'free -h && echo "---" && df -h'
   ```

4. **Consider Ollama itself has a bug/limitation:**
   - Ollama may not be designed for 1961+ embeddings in one session
   - May need periodic breaks or document grouping
   - May need to limit concurrent requests differently

---

## 🚀 Version Information

**System Version:** v1.0.3.24+
**Features Added:**
- ✅ Ollama health detection on batch failure
- ✅ Automatic restart capability
- ✅ Periodic health monitoring
- ✅ Clear diagnostic logging
- ✅ Graceful failure handling

**Configuration:** All configurable in `config/llm_config.yaml`
- `embedding.timeout.embedding_request`: Request timeout
- `embedding.timeout.service_restart`: Wait after restart
- `embedding.retry.max_service_restart_attempts`: Retry count
- `embedding.batch_processing.batch_size`: Batch size
- `embedding.batch_processing.batch_delay_seconds`: Delay between batches

---

## ✅ Summary

**Before v1.0.3.24:**
- Batch size reduction didn't help at ~1657 embeddings
- No insight into why Ollama was failing
- No automatic recovery

**After v1.0.3.24:**
- ✅ Detects Ollama health immediately
- ✅ Restarts Ollama automatically (if possible)
- ✅ Resumes scan after recovery
- ✅ Clear diagnostic logging
- ✅ Graceful degradation if service recovers

**Expected Result:** Scans should now complete even with temporary Ollama issues, OR fail gracefully with clear recommendations for manual intervention.

---

**Last Updated:** October 24, 2025
**Status:** Ready for testing with 1961-chunk PDF
