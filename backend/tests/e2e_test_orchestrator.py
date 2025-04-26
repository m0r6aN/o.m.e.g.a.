import requests

payload = {
    "text": "Artificial intelligence is transforming the way humans interact with technology.",
    "target_lang": "es"
}

response = requests.post("http://localhost:8000/run", json=payload)

print("🎉 Final Output:")
print(response.json())
