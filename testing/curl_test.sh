# Basic curl command with required fields (streaming enabled by default)
# Note: -X POST is optional since POST is inferred from -d
curl http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Explain quantum computing in simple terms."
  }'

# Curl command with streaming explicitly enabled
curl -X POST http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Write a short story about a robot learning to paint.",
    "stream": true
  }'

# Curl command with streaming disabled (returns complete JSON response)
curl -X POST http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "What are the benefits of renewable energy?",
    "stream": false
  }'

# Curl command with verbose output and error handling
curl -v -X POST http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Describe the process of photosynthesis step by step.",
    "stream": false
  }' \
  --connect-timeout 30 \
  --max-time 300

# Curl command with additional headers and timeout settings
curl -X POST http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -H "Accept: */*" \
  -H "User-Agent: curl/8.0.0" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Generate a Python function to calculate fibonacci numbers.",
    "stream": true
  }' \
  --connect-timeout 10 \
  --max-time 600 \
  --retry 3 \
  --retry-delay 2

# Optimized one-liner (most commonly used) - POST inferred from -d
curl http://localhost:5000/llama3_1b/prompt -H "Content-Type: application/json" -d '{"model": "llama3.2:1b", "prompt": "Hello, how are you today?", "stream": false}'

# For longer responses, increase timeout (your response took ~15 seconds)
curl http://localhost:5000/llama3_1b/prompt \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:1b", "prompt": "Write a detailed essay on climate change.", "stream": false}' \
  --max-time 60