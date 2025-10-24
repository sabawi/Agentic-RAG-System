# Log Interpretation Guide for Embedding Scans
## Understanding What's Happening v1.0.3.24+

**Quick Reference:** What to look for in logs when running document scans

---

## ✅ Healthy Scan - What Good Logs Look Like

```
10/24/2025 09:11:49 AM - 🔄 Processing 1961 embeddings in 197 batches of 10 (adaptive mode: True)
10/24/2025 09:11:58 AM - ✅ Completed batch: 10 embeddings (progress: 10/1961)
10/24/2025 09:12:07 AM - ✅ Completed batch: 10 embeddings (progress: 20/1961)
10/24/2025 09:12:16 AM - ✅ Completed batch: 10 embeddings (progress: 30/1961)
...
10/24/2025 09:38:45 AM - ✅ Completed batch: 10 embeddings (progress: 1950/1961)
10/24/2025 09:38:54 AM - ✅ Completed batch: 1 embeddings (progress: 1961/1961)
10/24/2025 09:38:54 AM - ✅ Generated 1961 embeddings across all batches (final batch_size=10)
```

**Interpretation:**
- ✅ Consistent batch completions every 9-10 seconds
- ✅ Progress increases steadily
- ✅ Final batch_size remains at 10 (no failures)
- ✅ **SUCCESS**: All 1961 embeddings processed

---

## ⚠️ Ollama Restart Scenario - What Recovery Looks Like

```
10/24/2025 09:35:42 AM - ✅ Completed batch: 10 embeddings (progress: 1650/1961)
10/24/2025 09:35:51 AM - ✅ Completed batch: 10 embeddings (progress: 1660/1961)
10/24/2025 09:36:00 AM - ❌ Embedding generation failed: 500
10/24/2025 09:36:00 AM - ❌ Batch failure: task 7 returned None
🔍 Ollama health check: ❌ UNHEALTHY
🚨 EMBEDDING SERVICE UNHEALTHY - Attempting restart
   Progress: 1660/1961 embeddings processed
   Current batch_size: 10
🔄 Ollama restart attempt 1/2...
✅ Ollama restarted successfully
⏳ Waiting 15 seconds for Ollama to stabilize...
📈 Service recovered - resetting batch_size to 10
10/24/2025 09:36:25 AM - ✅ Completed batch: 10 embeddings (progress: 1670/1961)
10/24/2025 09:36:34 AM - ✅ Completed batch: 10 embeddings (progress: 1680/1961)
...continues successfully...
10/24/2025 09:39:08 AM - ✅ Generated 1961 embeddings across all batches (final batch_size=10)
```

**Interpretation:**
- ⚠️ Failure detected at ~1660 embeddings (similar to before)
- 🔍 Health check shows Ollama UNHEALTHY
- 🔄 System attempts restart
- ✅ Restart succeeds
- ✅ **SUCCESS**: Scan resumes and completes

---

## ❌ Failure Scenario 1: Ollama Cannot Restart

```
10/24/2025 09:36:00 AM - ❌ Embedding generation failed: 500
❌ Batch failure: task 7 returned None
🔍 Ollama health check: ❌ UNHEALTHY
🚨 EMBEDDING SERVICE UNHEALTHY - Attempting restart
   Progress: 1660/1961 embeddings processed
🔄 Ollama restart attempt 1/2...
❌ Restart attempt 1 failed
🔄 Ollama restart attempt 2/2...
❌ Restart attempt 2 failed
❌ Failed to restart Ollama after 2 attempts
🛑 RECOMMENDATION: Manually restart Ollama service
   Command: systemctl restart ollama
   Or check: ps aux | grep ollama
❌ Failed to generate embeddings
❌ Failed to add chunks (likely embedding service issue)
```

**Interpretation:**
- ❌ Ollama becomes unhealthy
- ❌ Automatic restart fails (2/2 attempts)
- 🛑 **ACTION REQUIRED**: Admin must manually restart Ollama
- **NEXT STEP**: `systemctl restart ollama` then retry scan

---

## ⚠️ Failure Scenario 2: Batch Fails But Ollama OK (Graceful Degradation)

```
10/24/2025 09:35:51 AM - ❌ Embedding generation failed: 500
❌ Batch failure: task 5 returned None
🔍 Ollama health check: ✅ HEALTHY
⚠️ Service healthy but batch failed - reducing batch_size: 10 → 5
10/24/2025 09:35:58 AM - ✅ Completed batch: 5 embeddings (progress: 1655/1961)
10/24/2025 09:36:05 AM - ✅ Completed batch: 5 embeddings (progress: 1660/1961)
⚠️ Service healthy but batch failed - reducing batch_size: 5 → 2
10/24/2025 09:36:10 AM - ✅ Completed batch: 2 embeddings (progress: 1662/1961)
```

**Interpretation:**
- ⚠️ Single batch fails
- ✅ Ollama still healthy (responsive)
- 📉 System gracefully reduces batch size
- ✅ Processing continues at slower rate
- ✅ **Success expected**: Will eventually complete

---

## 🏥 Periodic Health Checks - What They Look Like

```
10/24/2025 09:25:15 AM - ✅ Completed batch: 10 embeddings (progress: 100/1961)
🏥 Periodic health check at batch 10...
   ✅ Ollama service healthy
10/24/2025 09:25:24 AM - ✅ Completed batch: 10 embeddings (progress: 110/1961)
...
10/24/2025 09:30:18 AM - ✅ Completed batch: 10 embeddings (progress: 200/1961)
🏥 Periodic health check at batch 20...
   ✅ Ollama service healthy
...
10/24/2025 09:35:51 AM - ✅ Completed batch: 10 embeddings (progress: 1660/1961)
🏥 Periodic health check at batch 166...
   ⚠️ Ollama service degrading at batch 166
   This may indicate upcoming failures - monitoring closely
```

**Interpretation:**
- Every 10 batches (every ~100 embeddings), system checks Ollama
- ✅ If healthy: Just logs and continues
- ⚠️ If degrading: Warns that failures may come next
- **Useful for:** Early detection of problems

---

## 📊 Key Log Messages to Watch

### During Normal Processing

| Message | Meaning | Action |
|---------|---------|--------|
| `🔄 Processing X embeddings in Y batches` | Starting scan | NONE - monitor |
| `✅ Completed batch: 10 embeddings` | Batch succeeded | NONE - expected |
| `🏥 Periodic health check at batch X` | Routine check | NONE - expected |

### If Failures Occur

| Message | Meaning | Action |
|---------|---------|--------|
| `❌ Embedding generation failed: 500` | Ollama returned error | CHECK NEXT message |
| `🔍 Ollama health check: ❌ UNHEALTHY` | Service not responding | System will restart |
| `🔄 Ollama restart attempt 1/2` | Attempting automatic restart | WAIT - recovery in progress |
| `✅ Ollama restarted successfully` | Recovery worked | ✅ Scan continues |
| `❌ Failed to restart Ollama` | Recovery failed | 🛑 Must restart manually |
| `⚠️ Service healthy but batch failed` | Transient error | System reducing batch size |

---

## 🔍 How to Monitor Logs in Real-Time

**Option 1: Watch for errors only**
```bash
tail -f logs/server_complete.log | grep -E "ERROR|Failed|Unhealthy|❌"
```

**Option 2: Watch for batch progress**
```bash
tail -f logs/server_complete.log | grep "Completed batch"
```

**Option 3: Watch for health updates**
```bash
tail -f logs/server_complete.log | grep -E "health|restart|progress"
```

**Option 4: Full log (recommended for first test)**
```bash
tail -f logs/server_complete.log
```

---

## 📈 Expected Progress Pattern

**Normal healthy processing:**
```
09:11:58 - Progress: 10/1961    ← Every ~9 seconds
09:12:07 - Progress: 20/1961    ← Consistent timing
09:12:16 - Progress: 30/1961
09:12:25 - Progress: 40/1961
...pattern continues...
09:38:45 - Progress: 1950/1961
09:38:54 - Progress: 1961/1961  ← Done! ~27 minutes total
```

**With single restart:**
```
09:35:51 - Progress: 1660/1961  ← Error here
09:36:00 - [Restart Ollama - 15 sec delay]
09:36:25 - Progress: 1670/1961  ← Resumes
09:38:54 - Progress: 1961/1961  ← Done! ~29 minutes total
```

---

## 🎯 Troubleshooting Checklist

**If scan stops with errors:**

1. Check for the phrase: `UNHEALTHY` or `Failed to restart`
   - YES: Ollama crashed, needs manual restart
   - NO: Different issue

2. Check final batch_size in last message:
   - `batch_size=10`: Processed at normal speed
   - `batch_size=5`: Some failures but recovering
   - `batch_size=1`: Many failures but still trying
   - Not present: Process was interrupted

3. Check progress number at failure:
   - ~1650-1700: Consistent with previous failures (Ollama hitting limit)
   - Earlier: Something different happening
   - Much later: Close to success, try again

4. Check system resources during scan:
   ```bash
   # Run in separate terminal during scan
   watch -n 2 'free -h && echo "---" && ps aux | grep ollama | grep -v grep | awk "{print \$6/1024\" MB\"}"'
   ```

---

## ✅ What Success Looks Like

Final log message should be:
```
✅ Generated 1961 embeddings across all batches (final batch_size=10)
```

Followed by:
```
✅ Added 1961 vectors to FAISS index
✅ Processing complete
```

**Total time:** 27-35 minutes (depending on if restart happened)

---

## 📞 Getting Help

If logs show something unexpected:

1. **Save the logs:**
   ```bash
   cp logs/server_complete.log logs/server_complete_failure_$(date +%Y%m%d_%H%M%S).log
   ```

2. **Provide:**
   - The last 50 lines of the log
   - The final `progress: X/1961` number
   - Any error messages
   - System info: `free -h`, `df -h`

3. **Check docs:**
   - `docs/OLLAMA_HEALTH_MONITORING_v1.0.3.24.md`
   - `docs/production/ADMINISTRATOR_GUIDE.md`

---

**Version:** v1.0.3.24+
**Last Updated:** October 24, 2025
