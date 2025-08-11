# src/groq_manager.py

import os
import requests
from itertools import cycle
from time import sleep
from dotenv import load_dotenv

# Load .env variables if available
load_dotenv()

class GroqAPIManager:
    def __init__(self, model="llama3-70b-8192", max_retries=4):
        keys = os.getenv("GROQ_API_KEYS", "").split(",")
        if not keys or keys == [""]:
            raise ValueError("No GROQ API keys found in GROQ_API_KEYS environment variable.")
        self.keys = cycle(keys)
        self.model = model
        self.max_retries = max_retries
        self.current_key = None
        self._rotate_key()

    def _rotate_key(self):
        self.current_key = next(self.keys)

    def generate(self, prompt, temperature=0.3):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.current_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    print(f"[] Attempt {attempt+1} failed for key: {self.current_key} | Status: {response.status_code}")
                    self._rotate_key()
                    sleep(1)
            except Exception as e:
                print(f"[] Exception with key: {self.current_key} -> {e}")
                self._rotate_key()
                sleep(1)

        raise RuntimeError(" All GROQ API keys failed after multiple attempts.")
