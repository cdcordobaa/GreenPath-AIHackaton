from ..state import EIAState
from ..adapters.llm import LlmRunner, LlmConfig
from ..prompts.schemas import LEGAL_REQUIREMENTS_JSON
from pathlib import Path
import json
from typing import Optional


def _build_prompt(scope, context) -> str:
    prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
    t = (prompts_dir / "legal_analysis.md").read_text(encoding="utf-8")
    return (t.replace("{{LEGAL_SCOPE}}", json.dumps(scope, ensure_ascii=False))
             .replace("{{CONTEXT}}", json.dumps(context, ensure_ascii=False)))


def run(state: EIAState, model: Optional[str] = None) -> EIAState:
    cfg = LlmConfig(primary=model or None) if model else LlmConfig()
    llm = LlmRunner(cfg)
    prompt = _build_prompt(state.legal_scope, {
        "affected_features": state.affected_features,
        "triggers": state.legal_triggers
    })

    raw = llm.ask(prompt, schema=LEGAL_REQUIREMENTS_JSON)
    try:
        data = json.loads(raw)
        state.compliance["requirements"] = data.get("requirements", [])
    except Exception:
        state.compliance["requirements"] = [
          {"ref": i["legal_ref"], "action": f"Tramitar {i['permit_type']}", "when":"antes de obra",
           "docs": i.get("evidence", []), "risk":"medio"} for i in state.legal_scope
        ]
    return state
