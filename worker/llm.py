"""LLM abstraction: OpenAI-compatible API when key exists, else offline heuristic."""
import os, json, urllib.request

class LLM:
    def __init__(self, model=None):
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @property
    def available(self):
        return bool(self.api_key)

    def chat(self, system: str, user: str) -> str:
        if not self.available:
            raise RuntimeError("no-llm-key")
        url = self.base.rstrip("/") + "/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read().decode())
        return body["choices"][0]["message"]["content"]
