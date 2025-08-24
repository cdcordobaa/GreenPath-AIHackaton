import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

    def find_dotenv(*args, **kwargs):
        return ""


async def main() -> None:
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

            if "map_geo_to_legal" in tool_names:
                # minimal smoke payload
                payload = {
                    "geo": {
                        "summary": {"capacidad_uso_tierra_count": 1},
                        "by_layer": {
                            "capacidad_uso_tierra": {
                                "rows": [
                                    {
                                        "CATEGORIA": "T_14_SUELOS",
                                        "TIPO": "CapacidadUsoTierra",
                                        "DES_LIMI_U": "Limitantes por suelo",
                                        "CLASE": "s",
                                        "SUBCLASE": "4s5",
                                        "G_MANEJO": "40106",
                                        "USO_PRIN_P": "10404",
                                    }
                                ]
                            }
                        },
                    }
                }
                res = await call_tool_json("map_geo_to_legal", {"input": payload})
                print({"map_geo_to_legal": res})

            if "inspect_taxonomy" in tool_names:
                res = await call_tool_json(
                    "inspect_taxonomy",
                    {
                        "input": {
                            "count_limit": 50,
                            "include_properties": True,
                            "include_indexes": False,
                            "include_constraints": False,
                        }
                    },
                )
                # Print a small summary to avoid huge logs
                labels = res.get("labels", [])
                rel_types = res.get("rel_types", [])
                print({
                    "inspect_taxonomy": {
                        "labels_top": labels[:5],
                        "rel_types_top": rel_types[:5],
                        "node_props_count": len(res.get("node_properties", [])),
                        "rel_props_count": len(res.get("rel_properties", [])),
                    }
                })

            if "get_instrumento_paths" in tool_names:
                res = await call_tool_json(
                    "get_instrumento_paths",
                    {"input": {"limit": 10}},
                )
                count = res.get("count")
                paths = (res.get("paths") or [])[:3]
                print({"get_instrumento_paths_count": count})
                try:
                    print(json.dumps(paths, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(paths))

            if "map_by_aliases" in tool_names:
                aliases = [
                    "aprovechaforestalpg",
                    "usosyusuariosrecursohidrico",
                    "compensacionbiodiversidad",
                ]
                res = await call_tool_json(
                    "map_by_aliases",
                    {"input": {"aliases": aliases}},
                )
                print({
                    "map_by_aliases": {
                        "ok": res.get("ok"),
                        "count": res.get("count"),
                        "aliases": aliases,
                    }
                })
                # Print first result compactly
                results = (res.get("results") or [])
                if results:
                    head = results[0]
                    compact = {
                        "category": head.get("category"),
                        "instruments_count": len(head.get("instrumentsAndPermits", [])),
                        "norms_count": len(head.get("associatedNorms", [])),
                    }
                    print({"map_by_aliases_head": compact})


if __name__ == "__main__":
    asyncio.run(main())


