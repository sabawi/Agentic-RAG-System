#!/bin/bash
# Complete Image-to-Text Tool Usage Example

echo "🖼️ Image-to-Text Tool Usage Guide"
echo "=================================="

echo
echo "Step 1: Configure Image Processing LLM"
echo "--------------------------------------"
echo "# Run this to set up vision models:"
echo "echo '9' | python llm_config_tool.py"
echo
echo "# Choose from:"
echo "# - Local: llava:7b (recommended for development)"
echo "# - Cloud: OpenAI Vision (best quality)"

echo
echo "Step 2: Test with OpenAI Compatible API"
echo "--------------------------------------"

echo
echo "# Example 1: Natural language request"
echo "curl -X POST http://localhost:5000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer test-key' \\"
echo "  -d '{"
echo "    \"model\": \"Agentic-RAG-Model1\","
echo "    \"messages\": [{"
echo "      \"role\": \"user\","
echo "      \"content\": \"Please analyze this uploaded image and describe what you see\""
echo "    }],"
echo "    \"stream\": false"
echo "  }'"

echo
echo "# Example 2: Request with specific image analysis instructions"
echo "curl -X POST http://localhost:5000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer test-key' \\"
echo "  -d '{"
echo "    \"model\": \"Agentic-RAG-Model1\","
echo "    \"messages\": [{"
echo "      \"role\": \"user\","
echo "      \"content\": \"Please analyze this base64 encoded image: data:image/jpeg;base64,/9j/4AAQ... using the image_to_text tool\""
echo "    }],"
echo "    \"stream\": false"
echo "  }'"

echo
echo "Step 3: Use with any OpenAI Compatible Client"
echo "--------------------------------------------"
echo "1. Use any OpenAI compatible client library"
echo "2. Point to http://localhost:5000 as the base URL"
echo "3. Use 'Agentic-RAG-Model1' as the model name"
echo "4. Send messages requesting image analysis"
echo "5. The system automatically handles image_to_text tool calls"
echo "6. Get detailed image descriptions in standard OpenAI format"

echo
echo "Step 4: Advanced Usage"
echo "---------------------"
echo "# Multiple images analysis:"
echo "curl -X POST http://localhost:5000/v1/chat/completions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer test-key' \\"
echo "  -d '{"
echo "    \"model\": \"Agentic-RAG-Model1\","
echo "    \"messages\": [{"
echo "      \"role\": \"user\","
echo "      \"content\": \"Please analyze multiple images: /path/to/image.jpg and https://example.com/chart.png using the image_to_text tool in batch processing mode\""
echo "    }],"
echo "    \"stream\": false"
echo "  }'"

echo
echo "Expected Response Format (OpenAI Compatible):"
echo "------------------------------------------"
echo "{"
echo "  \"id\": \"chatcmpl-...\","
echo "  \"object\": \"chat.completion\","
echo "  \"created\": 1699000000,"
echo "  \"model\": \"Agentic-RAG-Model1\","
echo "  \"choices\": [{"
echo "    \"index\": 0,"
echo "    \"message\": {"
echo "      \"role\": \"assistant\","
echo "      \"content\": \"I'll analyze the image(s) for you...\\n\\n[Detailed image analysis and results from image_to_text tool]\""
echo "    },"
echo "    \"finish_reason\": \"stop\""
echo "  }],"
echo "  \"usage\": {"
echo "    \"prompt_tokens\": 15,"
echo "    \"completion_tokens\": 200,"
echo "    \"total_tokens\": 215"
echo "  }"
echo "}"

echo
echo "🎉 Ready to analyze images!"
echo "=========================="