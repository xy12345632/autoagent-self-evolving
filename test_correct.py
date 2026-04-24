import httpx

api_key = "sk-vywf6uSEFrUsrDur4Va0nvbF2lQGmfZZZkGM5JcoaMoYanc6BDeKQI5mctSy8h1j"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "MiniMax-M2.5",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
}

try:
    r = httpx.post(
        "https://opencode.ai/zen/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30.0
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
