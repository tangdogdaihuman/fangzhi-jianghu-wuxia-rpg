"""wuxia_ai_client.py - Universal AI API client supporting any OpenAI-compatible API"""
import json, os, sys, time
from datetime import datetime

class AIClient:
    def __init__(self, api_key="", base_url="https://api.stepfun.com/step_plan/v1", model="step-2-16k"):
        self.api_key = api_key or os.environ.get("STEPFUN_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.conversation_history = []
        self.max_history = 20

    def set_api(self, api_key, base_url="https://api.stepfun.com/step_plan/v1", model="step-2-16k"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self):
        return bool(self.api_key)

    def chat(self, system_prompt, user_message, temperature=0.8, max_tokens=500):
        if not self.is_available():
            return None
        try:
            import urllib.request, ssl
            url = self.base_url + "/chat/completions"
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history[-self.max_history:])
            messages.append({"role": "user", "content": user_message})
            payload = json.dumps({
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            result = data["choices"][0]["message"]["content"]
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": result})
            return result
        except Exception as e:
            return "ERROR: " + str(e)

    def clear_history(self):
        self.conversation_history = []

# Global AI client instance
_ai_client = AIClient()

def get_ai_client():
    return _ai_client

def init_ai_client(api_key, base_url="https://api.stepfun.com/step_plan/v1", model="step-2-16k"):
    _ai_client.set_api(api_key, base_url, model)
    return _ai_client
