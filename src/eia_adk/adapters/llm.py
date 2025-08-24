import os
from dataclasses import dataclass
from typing import Optional, Any
import json
import os
from urllib import request as _urlrequest
from urllib.error import URLError as _URLError, HTTPError as _HTTPError


try:
    # Preferred: Google ADK agent
    from google_adk.agents import LlmAgent  # type: ignore
except Exception:  # pragma: no cover
    try:
        from adk.agents import LlmAgent  # type: ignore
    except Exception:
        LlmAgent = None  # type: ignore


@dataclass
class LlmConfig:
    primary: str = os.getenv("EIA_MODEL_PRIMARY", "gemini-2.5-pro")
    fallback: str = os.getenv("EIA_MODEL_FALLBACK", "gemini-2.5-flash")
    json_strict: bool = os.getenv("EIA_JSON_STRICT", "true").lower() == "true"
    temperature: float = 0.2
    top_p: float = 0.95
    max_output_tokens: int = 2048


class _GenAiAgent:
    """Lightweight fallback using google-genai SDK when ADK agent is unavailable."""

    def __init__(self, model: str, temperature: float, top_p: float, max_output_tokens: int):
        from google import genai  # lazy import

        api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GOOGLE_GENAI_API_KEY/.env for GenAI client")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._gen_cfg = {
            "temperature": temperature,
            "top_p": top_p,
            "max_output_tokens": max_output_tokens,
        }

    def run(self, prompt: str) -> str:
        # Some SDK versions don't accept generation_config as a keyword.
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        # google-genai Response has .text for aggregated string
        return getattr(resp, "text", str(resp))


class LlmRunner:
    def __init__(self, cfg: Optional[LlmConfig] = None):
        self.cfg = cfg or LlmConfig()

    def _agent(self, model: str) -> Any:
        if LlmAgent is not None:
            return LlmAgent(model=model, temperature=self.cfg.temperature, top_p=self.cfg.top_p)
        return _GenAiAgent(
            model=model,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            max_output_tokens=self.cfg.max_output_tokens,
        )

    def ask(self, prompt: str, schema: Optional[dict] = None) -> str:
        # 1) Hard mock: return fixed JSON/text from env
        fake = os.getenv("EIA_FAKE_LLM_JSON")
        if fake:
            return fake

        # 2) Local LLM (e.g., Ollama) without cloud credits
        # Configure with EIA_USE_LOCAL_LLM=1 and optional EIA_LOCAL_LLM_URL
        if os.getenv("EIA_USE_LOCAL_LLM") in ("1", "true", "True"):
            url = os.getenv("EIA_LOCAL_LLM_URL", "http://127.0.0.1:11434/api/generate")
            model = os.getenv("EIA_LOCAL_LLM_MODEL", self.cfg.primary)
            payload = {"model": model, "prompt": prompt, "stream": False}
            try:
                req = _urlrequest.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with _urlrequest.urlopen(req, timeout=60) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
                    try:
                        data = json.loads(body)
                        # Ollama: {"response": "..."}
                        if isinstance(data, dict) and "response" in data:
                            return str(data["response"])
                    except Exception:
                        pass
                    return body
            except (_HTTPError, _URLError) as exc:
                # Fall through to cloud if local fails
                last_err = exc  # noqa: F841

        # 3) Cloud models
        last_err: Optional[Exception] = None
        for model in (self.cfg.primary, self.cfg.fallback):
            try:
                agent = self._agent(model)
                # JSON schema hinting is handled within prompt until ADK JSON mode is wired.
                return str(agent.run(prompt))
            except Exception as e:  # pragma: no cover
                last_err = e
                continue
        raise RuntimeError(f"LLM failed on both models: {last_err}")


