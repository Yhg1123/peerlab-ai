"""Minimal first-party API client. No SDK, retries, or credential logging."""

from dataclasses import dataclass, field
import http.client
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request


class APIError(Exception):
    """A safe, user-facing error that never includes server bodies or headers."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError("API redirect refused; check the official endpoint.")


def load_env(path=Path(".env")):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep and key.strip() in {
            "DEEPSEEK_API_KEY", "KIMI_API_KEY", "DEEPSEEK_MODEL", "KIMI_MODEL"
        }:
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass
class Client:
    name: str
    model: str
    api_key: str = field(repr=False)
    base_url: str = ""
    max_tokens: int = 700
    timeout: int = 90

    def _request(self, path, payload=None):
        if not self.api_key or self.api_key.startswith("your_"):
            raise APIError(f"Missing {self.name.upper()}_API_KEY in .env or environment.")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json", "User-Agent": "PeerLab/0.1"},
        )
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            hints = {400: "Invalid request or incompatible model parameters.",
                     401: "Authentication failed; check your API key.",
                     402: "Insufficient API balance.", 403: "Access denied.",
                     404: "Model or endpoint unavailable.", 429: "Rate limit or quota reached."}
            raise APIError(f"HTTP {exc.code}: {hints.get(exc.code, 'Provider request failed.')} No retry was made.") from None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            raise APIError("Network error or timeout. No retry was made; provider billing may still apply.") from None
        except (ValueError, UnicodeError):
            raise APIError("Provider returned invalid JSON.") from None

    def models(self):
        body = self._request("/models")
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise APIError("Provider returned an invalid model list.")
        return [item["id"] for item in body["data"] if isinstance(item, dict) and isinstance(item.get("id"), str)]

    def complete(self, messages):
        payload = {"model": self.model, "messages": messages, "max_tokens": self.max_tokens,
                   "stream": False, "thinking": {"type": "disabled"}, "temperature": 0.6}
        started = time.perf_counter()
        body = self._request("/chat/completions", payload)
        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError
            usage = body.get("usage") or {}
            if not isinstance(usage, dict):
                raise ValueError
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if key in usage and (type(usage[key]) is not int or usage[key] < 0):
                    raise ValueError
            # Reasoning traces, response headers and credentials are deliberately not persisted.
            return {"content": content, "model": body.get("model", self.model),
                    "finish_reason": choice.get("finish_reason", "unknown"),
                    "usage": usage,
                    "latency_ms": round((time.perf_counter() - started) * 1000)}
        except (KeyError, IndexError, TypeError, ValueError):
            raise APIError("Provider returned no usable answer.") from None


def clients(max_tokens=700, timeout=90):
    load_env()
    return [
        Client("deepseek", os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
               os.getenv("DEEPSEEK_API_KEY", ""), "https://api.deepseek.com", max_tokens, timeout),
        Client("kimi", os.getenv("KIMI_MODEL", "kimi-k2.6"),
               os.getenv("KIMI_API_KEY", ""), "https://api.moonshot.cn/v1", max_tokens, timeout),
    ]
