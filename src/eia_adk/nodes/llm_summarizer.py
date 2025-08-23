from ..state import EIAState
from ..adapters.llm import LlmRunner, LlmConfig
from ..prompts.schemas import AFFECTED_TO_TRIGGERS_JSON
from pathlib import Path
import json
from typing import Optional


def _build_prompt(affected_features) -> str:
    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    template = (prompts_dir / "summarizer.md").read_text(encoding="utf-8")
    return template.replace("{{AFFECTED_FEATURES}}", json.dumps(affected_features, ensure_ascii=False))


def run(state: EIAState, model: Optional[str] = None) -> EIAState:
    cfg = LlmConfig(primary=model or None) if model else LlmConfig()
    llm = LlmRunner(cfg)
    prompt = _build_prompt(state.affected_features)

    raw = llm.ask(prompt, schema=AFFECTED_TO_TRIGGERS_JSON)
    try:
        data = json.loads(raw)
        state.legal_triggers = data.get("legal_triggers", [])
    except Exception:
        state.legal_triggers = [{"trigger": "cruce de cauce", "context": "river crossing", "priority": "alta"}]
    return state
