from dotenv import load_dotenv

load_dotenv()

try:
    from .graph import run_pipeline
except Exception:
    from eia_adk.graph import run_pipeline

if __name__ == "__main__":
    s = run_pipeline(
        project_path="data/sample_project/lines.geojson",
        target_layers=["hydro.rivers", "ecosystems", "protected_areas"],
    )
    print("Artifacts:", s.artifacts)
