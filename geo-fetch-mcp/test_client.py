import asyncio
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


async def main() -> None:
    # Load environment variables from .env if present
    try:
        load_dotenv(find_dotenv())
    except Exception:
        pass
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:
        print({"ok": False, "error": f"Missing mcp client: {exc}"})
        return

    entry = Path(__file__).with_name("run_stdio.py")
    server = StdioServerParameters(command=sys.executable, args=[str(entry)])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print({"tools": tool_names})

            async def call_tool_json(name: str, args: dict) -> dict:
                try:
                    res = await session.call_tool(name, args)
                    blocks = getattr(res, "content", [])
                    for blk in blocks:
                        data = getattr(blk, "data", None) or getattr(blk, "text", None)
                        if isinstance(data, dict):
                            return data
                        if isinstance(data, str):
                            try:
                                parsed = json.loads(data)
                                if isinstance(parsed, dict):
                                    return parsed
                            except Exception:
                                pass
                    return {"ok": True, "raw": str(blocks[0].text) if blocks else None}
                except Exception as exc:
                    return {"ok": False, "error": str(exc)}

            if "ping" in tool_names:
                print(await call_tool_json("ping", {}))

            have_supabase = bool(os.environ.get("SUPABASE_URL") and (os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")))
            project_id = os.environ.get("PROJECT_ID", "demo-project")

            if not have_supabase:
                print({"note": "Skipping Supabase-backed tools (missing SUPABASE_URL/KEY)."})
                return

            compendiums = [
                "get_soils_compendium",
                "get_hydrology_compendium",
                "get_hydrogeology_compendium",
                "get_biotic_compendium",
                "get_risk_management_compendium",
                "get_compensation_compendium",
            ]

            comp_rows = []
            for name in compendiums:
                if name in tool_names:
                    res = await call_tool_json(name, {"project_id": project_id})
                    summary = res.get("summary") or {}
                    print({"tool": name, "summary": summary, "ok": res.get("error") is None})
                    # Flatten summary into rows: one row per key
                    for k, v in summary.items():
                        comp_rows.append({
                            "tool": name,
                            "metric": k,
                            "value": v,
                        })

            uniques = [
                "get_soils_unique",
                "get_hydrology_unique",
                "get_hydrogeology_unique",
                "get_biotic_unique",
                "get_risk_management_unique",
                "get_compensation_unique",
            ]

            unique_rows = []
            for name in uniques:
                if name in tool_names:
                    res = await call_tool_json(name, {"project_id": project_id})
                    uniq_count = (res.get("summary") or {}).get("unique_count")
                    print({"tool": name, "unique_count": uniq_count, "ok": res.get("error") is None})
                    unique_rows.append({
                        "tool": name,
                        "unique_count": uniq_count,
                    })

            # Write CSVs
            out_dir = Path(__file__).with_name("outputs")
            out_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            comp_csv = out_dir / f"compendium_summary_{ts}.csv"
            if comp_rows:
                with comp_csv.open("w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["tool", "metric", "value"])
                    writer.writeheader()
                    writer.writerows(comp_rows)
                print({"wrote": str(comp_csv), "rows": len(comp_rows)})

            uniq_csv = out_dir / f"unique_summary_{ts}.csv"
            if unique_rows:
                with uniq_csv.open("w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["tool", "unique_count"])
                    writer.writeheader()
                    writer.writerows(unique_rows)
                print({"wrote": str(uniq_csv), "rows": len(unique_rows)})


if __name__ == "__main__":
    asyncio.run(main())


