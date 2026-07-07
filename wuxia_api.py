"""
wuxia_api.py - AI API configuration and client management
Supports any OpenAI-compatible API endpoint
"""
import json, os, sys, urllib.request, ssl, time

DEFAULT_API_URL = "https://api.stepfun.com/v1"
DEFAULT_MODEL = "step-2-16k"
CONFIG_FILE = "wuxia_config.json"

def load_config():
    config = {
        "api_key": os.environ.get("STEPFUN_API_KEY", ""),
        "base_url": DEFAULT_API_URL,
        "model": DEFAULT_MODEL,
        "temperature": 0.8,
        "max_tokens": 500,
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
    except Exception:
        pass
    return config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_chat_url(config):
    base = config.get("base_url", DEFAULT_API_URL).rstrip("/")
    return base + "/chat/completions"

def is_api_available(config):
    return bool(config.get("api_key", "").strip())

def call_api(config, messages, temperature=None, max_tokens=None, json_mode=False):
    if not is_api_available(config):
        return None
    try:
        url = get_chat_url(config)
        payload = {
            "model": config.get("model", DEFAULT_MODEL),
            "messages": messages,
            "temperature": temperature if temperature is not None else config.get("temperature", 0.8),
            "max_tokens": max_tokens if max_tokens is not None else config.get("max_tokens", 500),
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.get("api_key", ""),
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "ERROR: " + str(e)

_config_cache = None

def get_config():
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache

def init_config(api_key=None, base_url=None, model=None):
    global _config_cache
    config = load_config()
    if api_key is not None:
        config["api_key"] = api_key
    if base_url is not None:
        config["base_url"] = base_url
    if model is not None:
        config["model"] = model
    save_config(config)
    _config_cache = config
    return config
