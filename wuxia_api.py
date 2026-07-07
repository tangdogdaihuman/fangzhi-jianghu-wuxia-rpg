"""
wuxia_api.py - AI API configuration and client management
Supports any OpenAI-compatible API endpoint with multi-provider fallback
"""
import json, os, sys, urllib.request, ssl, time, uuid
from pathlib import Path

DEFAULT_API_URL = "https://api.stepfun.com/v1"
DEFAULT_MODEL = "step-2-16k"
CONFIG_FILE = "wuxia_config.json"

# ── LLM Diagnostic Dump ─────────────────────────────────────────
# Set WUXIA_DUMP_LLM=1 to write full LLM call logs to logs/llm_calls/
_DUMP_ENABLED = os.environ.get("WUXIA_DUMP_LLM", "0") == "1"
_DUMP_DIR = Path(os.environ.get("WUXIA_DUMP_DIR", "logs/llm_calls"))
_DUMP_DIR.mkdir(parents=True, exist_ok=True)
_CALL_LOG = []


def reset_call_log():
    """Reset per-action call accumulator. Call at start of each action."""
    _CALL_LOG.clear()


def get_call_log():
    """Return accumulated LLM call stats for current action."""
    return list(_CALL_LOG)


def get_call_summary():
    """Return aggregated token/time summary for current action."""
    total_in = sum(c.get("input_tokens", 0) for c in _CALL_LOG)
    total_out = sum(c.get("output_tokens", 0) for c in _CALL_LOG)
    total_time = sum(c.get("elapsed_s", 0) for c in _CALL_LOG)
    return {
        "call_count": len(_CALL_LOG),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "total_time_s": round(total_time, 2),
        "calls": [
            {
                "caller": c.get("caller", "?"),
                "input_tokens": c.get("input_tokens", 0),
                "output_tokens": c.get("output_tokens", 0),
                "max_tokens": c.get("max_tokens", 0),
                "elapsed_s": c.get("elapsed_s", 0),
                "msg_count": c.get("msg_count", 0),
                "system_chars": c.get("system_chars", 0),
            }
            for c in _CALL_LOG
        ],
    }


def _estimate_tokens(text):
    """Rough token estimate: ~4 chars per token for CJK+English mix."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _dump_llm_call(caller, model, messages, response_text, input_tokens, output_tokens, elapsed, streamed=False):
    """Write full LLM call record to disk for debugging."""
    if not _DUMP_ENABLED:
        return
    try:
        ts = time.strftime("%Y%m%dT%H%M%S")
        uid = uuid.uuid4().hex[:6]
        safe_caller = caller.replace(":", "_").replace("/", "_")[:60]
        record = {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "caller": caller,
            "model": model,
            "max_tokens": max_tokens if 'max_tokens' in dir() else 0,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed_s": round(elapsed, 3),
            "streamed": streamed,
            "msg_count": len(messages),
            "messages": messages,
            "response_text": response_text,
        }
        # Fix max_tokens reference
        record["max_tokens"] = max_tokens
        path = _DUMP_DIR / f"{ts}_{uid}_{safe_caller}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _log_call(caller, messages, max_tokens, response_text, elapsed, model=""):
    """Log a completed LLM call with token usage."""
    system_chars = sum(len(m.get("content", "")) for m in messages if m.get("role") == "system")
    total_chars = sum(len(m.get("content", "")) for m in messages)
    input_tokens = _estimate_tokens(total_chars)
    output_tokens = _estimate_tokens(response_text)

    entry = {
        "caller": caller,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "max_tokens": max_tokens,
        "elapsed_s": round(elapsed, 2),
        "msg_count": len(messages),
        "system_chars": system_chars,
    }
    _CALL_LOG.append(entry)

    if os.environ.get("WUXIA_LOG_LLM", "0") == "1":
        print(f"[LLM] {caller}: in={input_tokens} out={output_tokens} max={max_tokens} "
              f"time={elapsed:.1f}s sys_chars={system_chars}")


# ── Multi-Provider Fallback ─────────────────────────────────────
FALLBACK_PROVIDERS = [
    {"name": "stepfun",  "base_url": "https://api.stepfun.com/v1",
     "models": ["step-2-16k", "step-1-32k", "step-1-8k"]},
    {"name": "deepseek", "base_url": "https://api.deepseek.com/v1",
     "models": ["deepseek-chat", "deepseek-coder"]},
    {"name": "openai",   "base_url": "https://api.openai.com/v1",
     "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]},
    {"name": "ollama",   "base_url": "http://localhost:11434/v1",
     "models": ["qwen2.5:7b", "llama3.1:8b"]},
]


def _resolve_provider(base_url, model):
    """Match a base_url/model pair to a known provider, or return custom."""
    for prov in FALLBACK_PROVIDERS:
        if base_url.rstrip("/") == prov["base_url"].rstrip("/"):
            return prov
    return None


def _get_model_string(provider, model):
    """Build model identifier. For known providers use just model name."""
    if provider:
        return model
    return model  # custom providers also use just the model name


# ── Config ──────────────────────────────────────────────────────

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


def _do_call_api(config, messages, temperature, max_tokens, json_mode=False):
    """Single-shot API call. Returns response string or ERROR prefix."""
    if not is_api_available(config):
        return None
    try:
        url = get_chat_url(config)
        model = config.get("model", DEFAULT_MODEL)
        payload = {
            "model": model,
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
        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        elapsed = time.monotonic() - t0
        response_text = result["choices"][0]["message"]["content"]

        # Diagnostics
        caller = _get_caller()
        _log_call(caller, messages, max_tokens, response_text, elapsed, model)
        if _DUMP_ENABLED:
            _dump_llm_call(caller, model, messages, response_text,
                           _estimate_tokens(str(messages)),
                           _estimate_tokens(response_text), elapsed)

        return response_text
    except Exception as e:
        return "ERROR: " + str(e)


def _get_caller():
    """Walk stack to find meaningful caller module."""
    import inspect
    for i in range(2, 8):
        frame = inspect.stack()[i] if i < len(inspect.stack()) else None
        if frame is None:
            break
        module = frame.filename
        if "wuxia_api.py" not in module:
            fname = os.path.basename(module).replace(".py", "")
            return f"{fname}:{frame.function}:{frame.lineno}"
    return "unknown"


def call_api(config, messages, temperature=None, max_tokens=None, json_mode=False,
             allow_fallback=True):
    """Call AI API with optional multi-provider fallback.

    Args:
        config: API config dict with api_key, base_url, model.
        messages: List of message dicts for the LLM.
        temperature: Override temperature (default from config).
        max_tokens: Override max_tokens (default from config).
        json_mode: Request JSON object response.
        allow_fallback: If True, try fallback providers on failure.

    Returns:
        Response string, or None if no API key, or 'ERROR: ...' on failure.
    """
    if not is_api_available(config):
        return None

    # ── Try primary provider ──
    response = _do_call_api(config, messages, temperature, max_tokens, json_mode)
    if response and not response.startswith("ERROR:"):
        return response

    primary_url = config.get("base_url", DEFAULT_API_URL).rstrip("/")
    primary_model = config.get("model", DEFAULT_MODEL)
    primary_prov = _resolve_provider(primary_url, primary_model)

    if not allow_fallback:
        return response

    # ── Try fallback providers ──
    errors = []
    if response and response.startswith("ERROR:"):
        errors.append(f"primary ({primary_url}): {response}")

    for prov in FALLBACK_PROVIDERS:
        prov_base = prov["base_url"].rstrip("/")
        if prov_base == primary_url:
            continue  # skip same provider
        prov_model = prov["models"][0]
        fallback_config = dict(config)
        fallback_config["base_url"] = prov_base
        fallback_config["model"] = prov_model

        # For fallback, use a different key if available in config
        resp = _do_call_api(fallback_config, messages, temperature, max_tokens, json_mode)
        if resp and not resp.startswith("ERROR:"):
            if os.environ.get("WUXIA_LOG_LLM", "0") == "1":
                print(f"[wuxia] Fallback success via {prov['name']} ({prov_base})")
            return resp
        if resp:
            errors.append(f"{prov['name']} ({prov_base}): {resp}")

    error_summary = "; ".join(errors) if errors else "no providers responded"
    return f"ERROR: All providers failed — {error_summary}"


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
