from dotenv import load_dotenv
from eia_adk.state import EIAState
from eia_adk.nodes.llm_summarizer import run as sum_run
from eia_adk.nodes.legal_analysis import run as leg_run


def main() -> None:
    load_dotenv()
    s = EIAState(affected_features=[{"theme": "water", "feature": "hydro.rivers", "n_records": 2}])
    s = sum_run(s, model="gemini-2.5-pro")
    assert s.legal_triggers, "Expected triggers"

    s.legal_scope = [{
      "legal_ref": "Decreto 1076/2015 Art. X",
      "permit_type": "Ocupación de cauce",
      "authority": "ANLA",
      "evidence": ["plano 1:5000"]
    }]
    s = leg_run(s, model="gemini-2.5-pro")
    assert s.compliance["requirements"], "Expected requirements"
    print("OK", s.legal_triggers, s.compliance["requirements"]) 


if __name__ == "__main__":
    main()


