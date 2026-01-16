import requests
import json

OLLAMA_URL = "http://172.18.96.1:11434/api/generate"
OLLAMA_MODEL = "qwen3-vl:4b"

print("[TEST] Testing Ollama API connection...", flush=True)
print(f"[TEST] URL: {OLLAMA_URL}", flush=True)
print(f"[TEST] Model: {OLLAMA_MODEL}", flush=True)

# Test simple prompt - use direct instruction to avoid thinking
prompt = "Just answer: What is 2+2?"

try:
    print("\n[TEST] Sending test prompt...", flush=True)
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500,  # More tokens for response
                "top_p": 0.9
            }
        },
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get('response', '').strip()
        thinking = result.get('thinking', '').strip()
        done_reason = result.get('done_reason', '')
        
        print(f"\n[TEST] ✓ Status: {response.status_code}")
        print(f"[TEST] Done reason: {done_reason}")
        if thinking:
            print(f"[TEST] Thinking (first 200 chars): {thinking[:200]}...")
        print(f"[TEST] Answer: {answer if answer else '(empty response)'}")
    else:
        print(f"✗ API error: {response.status_code}")
        print(f"✗ Response: {response.text}")
except Exception as e:
    print(f"✗ Connection failed: {e}")