from ..state import EIAState


def run(state: EIAState, out_path: str = "out/report.md") -> EIAState:
    md = [
        "# Informe de Cumplimiento (MVP)",
        "## Proyecto",
        f"- Nombre: {state.project.get('name','')}",
        "## Intersecciones",
        f"- Total: {len(state.intersections)}",
        "## Impactos",
        f"- {state.affected_features}",
        "## Reglas legales mapeadas",
        f"- {state.legal_scope}",
        "## Requerimientos",
        f"- {state.compliance['requirements']}",
        "## Próximos pasos",
        "- Completar análisis GIS real",
        "- Adjuntar mapas / evidencias",
    ]
    import os

    os.makedirs("out", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    state.artifacts.append({"type": "report_md", "uri": out_path})
    return state
