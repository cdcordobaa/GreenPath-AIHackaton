import os
from dataclasses import dataclass
from typing import Optional, Any
import json
import time
import random
import logging
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
    max_retries: int = int(os.getenv("EIA_MAX_RETRIES", "3"))
    base_delay: float = float(os.getenv("EIA_BASE_DELAY", "1.0"))
    max_delay: float = float(os.getenv("EIA_MAX_DELAY", "60.0"))


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

    def run(self, prompt: str, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> str:
        """Run with exponential backoff retry logic for rate limiting."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Some SDK versions don't accept generation_config as a keyword.
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                # google-genai Response has .text for aggregated string
                return getattr(resp, "text", str(resp))
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                    if attempt < max_retries:
                        # Extract retry delay from error if available
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        if "retrydelay" in error_str and "40s" in error_str:
                            delay = max(delay, 40)  # Respect the API's suggested delay
                        delay = min(delay, max_delay)
                        
                        logging.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logging.error(f"Rate limit exceeded after {max_retries} retries")
                        raise
                else:
                    # Non-rate-limit error, don't retry
                    raise
        
        raise last_exception or RuntimeError("Failed after retries")


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

        # 3) Cloud models with retry logic
        last_err: Optional[Exception] = None
        for model in (self.cfg.primary, self.cfg.fallback):
            try:
                agent = self._agent(model)
                # Use retry logic for cloud models
                if hasattr(agent, 'run') and hasattr(self.cfg, 'max_retries'):
                    if isinstance(agent, _GenAiAgent):
                        return str(agent.run(prompt, self.cfg.max_retries, self.cfg.base_delay, self.cfg.max_delay))
                    else:
                        # ADK agent - wrap with retry logic
                        return str(self._run_with_retry(agent, prompt))
                else:
                    # Fallback to simple run
                    return str(agent.run(prompt))
            except Exception as e:  # pragma: no cover
                last_err = e
                error_str = str(e).lower()
                # If rate limited, try local fallback immediately
                if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                    logging.warning(f"Rate limit hit on {model}, trying local LLM fallback")
                    try:
                        return self._try_local_fallback(prompt)
                    except Exception as local_err:
                        logging.warning(f"Local LLM fallback failed: {local_err}")
                continue
        
        # Final fallback to local LLM if all cloud models failed
        try:
            logging.warning("All cloud models failed, trying local LLM as final fallback")
            return self._try_local_fallback(prompt)
        except Exception as local_err:
            logging.error(f"Local LLM final fallback failed: {local_err}")
        
        raise RuntimeError(f"LLM failed on all models: {last_err}")

    def _run_with_retry(self, agent: Any, prompt: str) -> str:
        """Retry wrapper for ADK agents."""
        last_exception = None
        
        for attempt in range(self.cfg.max_retries + 1):
            try:
                return str(agent.run(prompt))
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                    if attempt < self.cfg.max_retries:
                        delay = self.cfg.base_delay * (2 ** attempt) + random.uniform(0, 1)
                        if "retrydelay" in error_str and "40s" in error_str:
                            delay = max(delay, 40)
                        delay = min(delay, self.cfg.max_delay)
                        
                        logging.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.cfg.max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise
        
        raise last_exception or RuntimeError("Failed after retries")

    def _try_local_fallback(self, prompt: str) -> str:
        """Try local LLM as fallback."""
        url = os.getenv("EIA_LOCAL_LLM_URL", "http://127.0.0.1:11434/api/generate")
        model = os.getenv("EIA_LOCAL_LLM_MODEL", "llama3.2")  # Default to a common local model
        payload = {"model": model, "prompt": prompt, "stream": False}
        
        req = _urlrequest.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urlrequest.urlopen(req, timeout=120) as resp:  # Longer timeout for local LLM
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(body)
                if isinstance(data, dict) and "response" in data:
                    return str(data["response"])
            except Exception:
                pass
            return body


