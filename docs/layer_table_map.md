## Layer → Supabase tables map

Mapping derived from `Map Category Table.csv` and current `public` schema tables in Supabase.

### T_14_SUELOS
- CapacidadUsoTierra → `CapacidadUsoTierra`
- ConflictoUsoSuelo → (missing)
- PuntoMuestreoSuelo → (missing)
- Suelo → (missing)
- UsoActualSuelo → (missing)

### T_15_HIDROLOGIA
- CuencaHidrografica → `CuencaHidrografica`
- OcupacionCauce → `ocupacioncauce`
- PuntoMuestreoAguaSuper → `puntomuestreoaguasuper`
- UsosyUsuariosRecursoHidrico → `usosyusuariosrecursohidrico`

### T_16_HIDROGEOLOGIA
- PuntoHidrogeologico → `PuntoHidrogeologico`, `puntohidrogeologico`
- PuntoMuestreoAguaSubter → `puntomuestreoaguasubter`
- UnidadHidrogeologica → (missing)
- ZonasRecarga → (missing)

### T_20_BIOTICO_CONTI_COSTE
- AprovechaForestalPG → `aprovechaforestalpg`
- AprovechaForestalPT → `aprovechaforestalpt`
- CoberturaTierra → `coberturatierra`
- Ecosistema → `ecosistema`
- PuntoMuestreoFauna → `puntomuestreofauna`
- PuntoMuestreoFlora → `puntomuestreoflora`
- TransectoMuestreoFauna → `transectomuestreofauna`

### T_26_GESTION_RIESGO
- AmenazaOtras → `amenazaotras`
- AmenazaSismica → (missing)
- AmenazaVolcanica → (missing)
- ElementosExpuestosLN → `elementosexpuestosln`
- ElementosExpuestosPG → `elementosexpuestospg`
- ElementosExpuestosPT → `elementosexpuestospt`
- EscenAmenAvenTorren → (missing)
- EscenAmenIncendio → (missing)
- EscenAmenInunda → (missing)
- EscenAmenMovMasa → (missing)
- EscenRiesgoAvenTorren → (missing)
- EscenRiesgoIncendio → `escenriesgoincendio`
- EscenRiesgoInundacion → (missing)
- EscenRiesgoMovMasa → `escenriesgomovmasa`
- Eventos_PT → `eventos_pt`
- Export_Output → `export_output`
- Suscept_AvenTorren → `suscept_aventorren`
- Suscept_Incendios → `suscept_incendios`
- Suscept_Inundaciones → `suscept_inundaciones`
- Suscept_MovMasa → `suscept_movmasa`
- Vulnerabilidad_LN → `vulnerabilidad_ln`
- Vulnerabilidad_PG → `vulnerabilidad_pg`
- Vulnerabilidad_PT → `vulnerabilidad_pt`

### T_34_COMPENSACION
- CompensacionBiodiversidad → `compensacionbiodiversidad`

### Unmapped existing tables (not listed in CSV)
- `scraped_pages`
- `scraped_chunks`
- `proyectos`


