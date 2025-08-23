class LegalKBMCP:
    def map_triggers_to_rules(self, triggers: list[dict]) -> list[dict]:
        out: list[dict] = []
        for t in triggers:
            if "cauce" in t.get("trigger", ""):
                out.append(
                    {
                        "legal_ref": "Decreto 1076/2015 Art. X",
                        "permit_type": "Ocupación de cauce",
                        "authority": "ANLA/CAR",
                        "evidence": ["plano 1:5000", "memoria hidráulica"],
                        "resources": ["resources://decreto_1076_art_x"],
                    }
                )
        return out or [
            {
                "legal_ref": "Ley 99/1993 (general)",
                "permit_type": "Determinación de autoridad ambiental",
                "authority": "CAR",
                "evidence": [],
                "resources": [],
            }
        ]

    def list_resources(self, legal_refs: list[str]) -> list[dict]:
        return [{"ref": r, "uri": f"supabase://docs/{r.replace(' ', '_')}"} for r in legal_refs]
