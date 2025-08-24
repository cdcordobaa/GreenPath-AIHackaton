import os
from typing import Optional, Dict, Any
import orjson

from dotenv import load_dotenv
from supabase import create_client, Client
from mcp.server.fastmcp import FastMCP
from models import LayerQueryInput, GenericLayerQueryInput, LayerQueryOutput
from supabase_io import fetch_layer_records


load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Allow starting without credentials; tools that need Supabase will raise if used
    supabase: Optional[Client] = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP("geo-fetch-mcp")


def _supabase_fetch_all_rows(table_name: str) -> Dict[str, Any]:
    if supabase is None:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    resp = supabase.table(table_name).select("*").execute()
    rows = getattr(resp, "data", []) or []
    err = getattr(resp, "error", None)
    return {"rows": rows, "count": len(rows), "error": err}


def _distinct_union_datasets(*datasets: Dict[str, Any]) -> Dict[str, Any]:
    seen: set[bytes] = set()
    unique_rows = []
    for ds in datasets:
        rows = ds.get("rows", []) or []
        for row in rows:
            try:
                key = orjson.dumps(row, option=orjson.OPT_SORT_KEYS)
            except Exception:
                # Fallback if row contains non-JSON-serializable values
                try:
                    key = orjson.dumps({k: str(v) for k, v in row.items()}, option=orjson.OPT_SORT_KEYS)
                except Exception:
                    key = repr(row).encode()
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)
    return {"unique_rows": unique_rows, "unique_count": len(unique_rows)}


@mcp.tool()
def get_layer_records(input: GenericLayerQueryInput) -> LayerQueryOutput:
    recs = fetch_layer_records(project_id=input.project_id, layer=input.layer)
    return LayerQueryOutput(layer=input.layer, count=len(recs), records=recs)


@mcp.tool()
def get_soils(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "soils"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_protected_areas(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "protected_areas"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_biotic(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "biotic"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_hydrography(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "hydrography"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_ecosystems(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "ecosystems"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_species(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "species"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def ping() -> dict:
    return {"ok": True, "service": "geo-fetch-mcp", "version": "0.1.0"}


@mcp.tool()
def capacidad_uso_tierra_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("CapacidadUsoTierra")


@mcp.tool()
def get_soils_compendium(project_id: str) -> Dict[str, Any]:
    capacidad = capacidad_uso_tierra_query(project_id)
    return {
        "summary": {"CapacidadUsoTierra": capacidad["count"]},
        "datasets": {"CapacidadUsoTierra": capacidad},
    }


@mcp.tool()
def get_soils_unique(project_id: str) -> Dict[str, Any]:
    capacidad = capacidad_uso_tierra_query(project_id)
    uniq = _distinct_union_datasets(capacidad)
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}


@mcp.tool()
def get_hydrology_compendium(project_id: str) -> Dict[str, Any]:
    cuencas = _supabase_fetch_all_rows("CuencaHidrografica")
    ocupacion = _supabase_fetch_all_rows("ocupacioncauce")
    muestras_super = _supabase_fetch_all_rows("puntomuestreoaguasuper")
    usos_usuarios = _supabase_fetch_all_rows("usosyusuariosrecursohidrico")

    return {
        "summary": {
            "CuencaHidrografica": cuencas["count"],
            "ocupacioncauce": ocupacion["count"],
            "puntomuestreoaguasuper": muestras_super["count"],
            "usosyusuariosrecursohidrico": usos_usuarios["count"],
        },
        "datasets": {
            "CuencaHidrografica": cuencas,
            "ocupacioncauce": ocupacion,
            "puntomuestreoaguasuper": muestras_super,
            "usosyusuariosrecursohidrico": usos_usuarios,
        },
    }


@mcp.tool()
def get_hydrology_unique(project_id: str) -> Dict[str, Any]:
    cuencas = _supabase_fetch_all_rows("CuencaHidrografica")
    ocupacion = _supabase_fetch_all_rows("ocupacioncauce")
    muestras_super = _supabase_fetch_all_rows("puntomuestreoaguasuper")
    usos_usuarios = _supabase_fetch_all_rows("usosyusuariosrecursohidrico")
    uniq = _distinct_union_datasets(cuencas, ocupacion, muestras_super, usos_usuarios)
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}


@mcp.tool()
def cuenca_hidrografica_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("CuencaHidrografica")


@mcp.tool()
def ocupacion_cauce_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("ocupacioncauce")


@mcp.tool()
def punto_muestreo_agua_super_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("puntomuestreoaguasuper")


@mcp.tool()
def usosy_usuarios_recurso_hidrico_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("usosyusuariosrecursohidrico")


@mcp.tool()
def get_hydrogeology_compendium(project_id: str) -> Dict[str, Any]:
    punto_hi = _supabase_fetch_all_rows("PuntoHidrogeologico")
    puntohi_lower = _supabase_fetch_all_rows("puntohidrogeologico")
    muestras_sub = _supabase_fetch_all_rows("puntomuestreoaguasubter")
    return {
        "summary": {
            "PuntoHidrogeologico": punto_hi["count"],
            "puntohidrogeologico": puntohi_lower["count"],
            "puntomuestreoaguasubter": muestras_sub["count"],
        },
        "datasets": {
            "PuntoHidrogeologico": punto_hi,
            "puntohidrogeologico": puntohi_lower,
            "puntomuestreoaguasubter": muestras_sub,
        },
    }


@mcp.tool()
def get_hydrogeology_unique(project_id: str) -> Dict[str, Any]:
    punto_hi = _supabase_fetch_all_rows("PuntoHidrogeologico")
    puntohi_lower = _supabase_fetch_all_rows("puntohidrogeologico")
    muestras_sub = _supabase_fetch_all_rows("puntomuestreoaguasubter")
    uniq = _distinct_union_datasets(punto_hi, puntohi_lower, muestras_sub)
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}


@mcp.tool()
def punto_hidrogeologico_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("PuntoHidrogeologico")


@mcp.tool()
def puntohidrogeologico_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("puntohidrogeologico")


@mcp.tool()
def punto_muestreo_agua_subter_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("puntomuestreoaguasubter")


@mcp.tool()
def get_biotic_compendium(project_id: str) -> Dict[str, Any]:
    a_pg = _supabase_fetch_all_rows("aprovechaforestalpg")
    a_pt = _supabase_fetch_all_rows("aprovechaforestalpt")
    cob = _supabase_fetch_all_rows("coberturatierra")
    eco = _supabase_fetch_all_rows("ecosistema")
    pm_fauna = _supabase_fetch_all_rows("puntomuestreofauna")
    pm_flora = _supabase_fetch_all_rows("puntomuestreoflora")
    tran_fauna = _supabase_fetch_all_rows("transectomuestreofauna")
    return {
        "summary": {
            "aprovechaforestalpg": a_pg["count"],
            "aprovechaforestalpt": a_pt["count"],
            "coberturatierra": cob["count"],
            "ecosistema": eco["count"],
            "puntomuestreofauna": pm_fauna["count"],
            "puntomuestreoflora": pm_flora["count"],
            "transectomuestreofauna": tran_fauna["count"],
        },
        "datasets": {
            "aprovechaforestalpg": a_pg,
            "aprovechaforestalpt": a_pt,
            "coberturatierra": cob,
            "ecosistema": eco,
            "puntomuestreofauna": pm_fauna,
            "puntomuestreoflora": pm_flora,
            "transectomuestreofauna": tran_fauna,
        },
    }


@mcp.tool()
def get_biotic_unique(project_id: str) -> Dict[str, Any]:
    a_pg = _supabase_fetch_all_rows("aprovechaforestalpg")
    a_pt = _supabase_fetch_all_rows("aprovechaforestalpt")
    cob = _supabase_fetch_all_rows("coberturatierra")
    eco = _supabase_fetch_all_rows("ecosistema")
    pm_fauna = _supabase_fetch_all_rows("puntomuestreofauna")
    pm_flora = _supabase_fetch_all_rows("puntomuestreoflora")
    tran_fauna = _supabase_fetch_all_rows("transectomuestreofauna")
    uniq = _distinct_union_datasets(a_pg, a_pt, cob, eco, pm_fauna, pm_flora, tran_fauna)
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}


@mcp.tool()
def aprovecha_forestal_pg_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("aprovechaforestalpg")


@mcp.tool()
def aprovecha_forestal_pt_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("aprovechaforestalpt")


@mcp.tool()
def cobertura_tierra_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("coberturatierra")


@mcp.tool()
def ecosistema_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("ecosistema")


@mcp.tool()
def punto_muestreo_fauna_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("puntomuestreofauna")


@mcp.tool()
def punto_muestreo_flora_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("puntomuestreoflora")


@mcp.tool()
def transecto_muestreo_fauna_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("transectomuestreofauna")


@mcp.tool()
def get_risk_management_compendium(project_id: str) -> Dict[str, Any]:
    am_otras = _supabase_fetch_all_rows("amenazaotras")
    el_ln = _supabase_fetch_all_rows("elementosexpuestosln")
    el_pg = _supabase_fetch_all_rows("elementosexpuestospg")
    el_pt = _supabase_fetch_all_rows("elementosexpuestospt")
    esc_inc = _supabase_fetch_all_rows("escenriesgoincendio")
    esc_mov = _supabase_fetch_all_rows("escenriesgomovmasa")
    eventos = _supabase_fetch_all_rows("eventos_pt")
    export_out = _supabase_fetch_all_rows("export_output")
    sus_av = _supabase_fetch_all_rows("suscept_aventorren")
    sus_inc = _supabase_fetch_all_rows("suscept_incendios")
    sus_inu = _supabase_fetch_all_rows("suscept_inundaciones")
    sus_mov = _supabase_fetch_all_rows("suscept_movmasa")
    vul_ln = _supabase_fetch_all_rows("vulnerabilidad_ln")
    vul_pg = _supabase_fetch_all_rows("vulnerabilidad_pg")
    vul_pt = _supabase_fetch_all_rows("vulnerabilidad_pt")

    return {
        "summary": {
            "amenazaotras": am_otras["count"],
            "elementosexpuestosln": el_ln["count"],
            "elementosexpuestospg": el_pg["count"],
            "elementosexpuestospt": el_pt["count"],
            "escenriesgoincendio": esc_inc["count"],
            "escenriesgomovmasa": esc_mov["count"],
            "eventos_pt": eventos["count"],
            "export_output": export_out["count"],
            "suscept_aventorren": sus_av["count"],
            "suscept_incendios": sus_inc["count"],
            "suscept_inundaciones": sus_inu["count"],
            "suscept_movmasa": sus_mov["count"],
            "vulnerabilidad_ln": vul_ln["count"],
            "vulnerabilidad_pg": vul_pg["count"],
            "vulnerabilidad_pt": vul_pt["count"],
        },
        "datasets": {
            "amenazaotras": am_otras,
            "elementosexpuestosln": el_ln,
            "elementosexpuestospg": el_pg,
            "elementosexpuestospt": el_pt,
            "escenriesgoincendio": esc_inc,
            "escenriesgomovmasa": esc_mov,
            "eventos_pt": eventos,
            "export_output": export_out,
            "suscept_aventorren": sus_av,
            "suscept_incendios": sus_inc,
            "suscept_inundaciones": sus_inu,
            "suscept_movmasa": sus_mov,
            "vulnerabilidad_ln": vul_ln,
            "vulnerabilidad_pg": vul_pg,
            "vulnerabilidad_pt": vul_pt,
        },
    }


@mcp.tool()
def get_risk_management_unique(project_id: str) -> Dict[str, Any]:
    am_otras = _supabase_fetch_all_rows("amenazaotras")
    el_ln = _supabase_fetch_all_rows("elementosexpuestosln")
    el_pg = _supabase_fetch_all_rows("elementosexpuestospg")
    el_pt = _supabase_fetch_all_rows("elementosexpuestospt")
    esc_inc = _supabase_fetch_all_rows("escenriesgoincendio")
    esc_mov = _supabase_fetch_all_rows("escenriesgomovmasa")
    eventos = _supabase_fetch_all_rows("eventos_pt")
    export_out = _supabase_fetch_all_rows("export_output")
    sus_av = _supabase_fetch_all_rows("suscept_aventorren")
    sus_inc = _supabase_fetch_all_rows("suscept_incendios")
    sus_inu = _supabase_fetch_all_rows("suscept_inundaciones")
    sus_mov = _supabase_fetch_all_rows("suscept_movmasa")
    vul_ln = _supabase_fetch_all_rows("vulnerabilidad_ln")
    vul_pg = _supabase_fetch_all_rows("vulnerabilidad_pg")
    vul_pt = _supabase_fetch_all_rows("vulnerabilidad_pt")
    uniq = _distinct_union_datasets(
        am_otras, el_ln, el_pg, el_pt, esc_inc, esc_mov, eventos, export_out,
        sus_av, sus_inc, sus_inu, sus_mov, vul_ln, vul_pg, vul_pt
    )
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}


@mcp.tool()
def amenaza_otras_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("amenazaotras")


@mcp.tool()
def elementos_expuestos_ln_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("elementosexpuestosln")


@mcp.tool()
def elementos_expuestos_pg_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("elementosexpuestospg")


@mcp.tool()
def elementos_expuestos_pt_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("elementosexpuestospt")


@mcp.tool()
def escen_riesgo_incendio_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("escenriesgoincendio")


@mcp.tool()
def escen_riesgo_mov_masa_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("escenriesgomovmasa")


@mcp.tool()
def eventos_pt_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("eventos_pt")


@mcp.tool()
def export_output_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("export_output")


@mcp.tool()
def suscept_aventorren_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("suscept_aventorren")


@mcp.tool()
def suscept_incendios_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("suscept_incendios")


@mcp.tool()
def suscept_inundaciones_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("suscept_inundaciones")


@mcp.tool()
def suscept_movmasa_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("suscept_movmasa")


@mcp.tool()
def vulnerabilidad_ln_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("vulnerabilidad_ln")


@mcp.tool()
def vulnerabilidad_pg_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("vulnerabilidad_pg")


@mcp.tool()
def vulnerabilidad_pt_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("vulnerabilidad_pt")


@mcp.tool()
def get_compensation_compendium(project_id: str) -> Dict[str, Any]:
    comp_bio = _supabase_fetch_all_rows("compensacionbiodiversidad")
    return {
        "summary": {"compensacionbiodiversidad": comp_bio["count"]},
        "datasets": {"compensacionbiodiversidad": comp_bio},
    }


@mcp.tool()
def get_compensation_unique(project_id: str) -> Dict[str, Any]:
    comp_bio = _supabase_fetch_all_rows("compensacionbiodiversidad")
    uniq = _distinct_union_datasets(comp_bio)
    return {"summary": {"unique_count": uniq["unique_count"]}, "unique": uniq}
@mcp.tool()
def compensacion_biodiversidad_query(project_id: str) -> Dict[str, Any]:
    return _supabase_fetch_all_rows("compensacionbiodiversidad")

if __name__ == "__main__":
    mcp.run_stdio()


