## Supabase schema (public)

This document lists all tables in the `public` schema and their columns.

### scraped_pages
- page_id (bigint), url (text), status (text), last_crawled_at (timestamptz), content_type (text), title (text), description (text), content_md (text), content_html (text), meta (jsonb), doc_id (text)

### scraped_chunks
- chunk_id (bigint), page_id (bigint), url (text), section (text), chunk_text (text), token_count (integer), embedding (vector), tsv (tsvector)

### CapacidadUsoTierra
- id (bigint), EXPEDIENTE (varchar), CLASE (float8), SUBCLASE (varchar), G_MANEJO (varchar), USO_PRIN_P (float8), AREA_HA (float8), DES_LIMI_U (varchar), OBSERV (varchar), TIPO (varchar), CATEGORIA (varchar), GEOMETRY (varchar)

### CuencaHidrografica
- id (bigint), OBJECTID (bigint), EXPEDIENTE (varchar), AH (varchar), ZH (varchar), SZH (varchar), N_NV_SUB (varchar), C_NV_SUB (varchar), N_MIC_CUE (varchar), C_MIC_CUE (varchar), NOMENCLAT (varchar), IND_COMPAC (float8), FORM_IND_C (float8), IND_SIN (float8), TIPO_DRENA (float8), DEN_CORRIE (float8), DEN_DREN (float8), TIEM_CONC (float8), MET_T_CONC (varchar), OBSERV (varchar), AREA_HA (float8), OF_HID_TOT (float8), OF_HID_DIS (float8), CAUD_AMB (float8), IUA (float8), IRH (float8), IVH (float8), IA (float8), SHAPE_LENG (float8), SHAPE_AREA (float8), GEOMETRY (varchar), TIPO (varchar), CATEGORIA (varchar)

### PuntoHidrogeologico
- ID (bigint), EXPEDIENTE (text), OPERADOR (text), PROYECTO (text), VEREDA (text), MUNICIPIO (text), DEPTO (text), CAR (float8), NOMBRE (text), ID_PUNTO_H (text), TIPO_PUNTO (float8), UNI_GEOLO (text), NOM_PREDIO (text), COND_PROPI (float8), SITIO (text), FEC_CARACT (date), DILIGENCIA (text), FEC_CONST (date), DIAM_EXT (float8), DIAM_INT (float8), ANC_EXT (float8), LAR_ETX (float8), PROFUND_M (float8), LONG_SUPER (float8), NIV_PIEZOM (float8), PER_CORPO (float8), CAUDA_CORP (float8), MATERIAL (text), MET_EXPLOT (float8), T_ENERGIA (float8), US_DI_POZO (float8), MED_SURG (float8), T_MANANT (float8), P_MANANT (float8), CONDI_PUNT (float8), PROP_PTO (float8), U_APROV_1 (float8), D_U_APR_1 (float8), U_APROV_2 (float8), D_U_APR_2 (float8), U_APROV_3 (float8), D_U_APR_3 (float8), U_APROV_4 (float8), D_U_APR_4 (float8), D_USO_TOT (float8), N_US_PUB (bigint), N_US_DOM (bigint), T_INDUST (text), T_CULTIVO (text), A_IRRIG_HA (float8), T_AGROIND (text), N_ANIM (bigint), RESID_SOL (float8), MAN_RESID (float8), OBS_RESID (text), OBSERV (text), COTA (float8), COOR_ESTE (float8), COOR_NORTE (float8), GEOMETRY (text), TIPO (text), CATEGORIA (text)

### proyectos
- id (bigint), nombreProyecto (text)

### escenriesgomovmasa
- id (integer), objectid (integer), expediente (text), amenaza (text), vulnerabil (text), riesgo (text), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), geometry (text), tipo (text), categoria (text)

### eventos_pt
- id (integer), objectid (integer), expediente (text), evento (text), fecha_even (text), tipo_even (text), descripcion (text), observ (text), x_magna (numeric), y_magna (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), vereda (text), geometry (text), tipo (text), categoria (text)

### export_output
- id (integer), objectid (integer), expediente (text), geometry (text), tipo (text), categoria (text)

### suscept_aventorren
- id (integer), objectid (integer), expediente (text), nivel (text), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), geology (text), tipo (text), categoria (text)

### suscept_movmasa
- id (integer), objectid (integer), expediente (text), geomorfolo (text), geologia (text), pendientes (text), cobertura (text), precipitac (text), sismicidad (text), susceptibi (text), nivel (text), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), crit_geomor (integer), crit_geolo (integer), crit_pendi (integer), crit_cober (integer), crit_preci (integer), crit_sismi (integer), detonante (text), geometry (text), tipo (text), categoria (text)

### vulnerabilidad_ln
- id (integer), objectid (integer), expediente (text), elemento (text), exposicion (integer), fragilidad (integer), resistencia (integer), resilencia (integer), vulnerabil (numeric), nivel_vuln (text), observ (text), long_km (numeric), shape_leng (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), geometry (text), tipo (text), categoria (text)

### vulnerabilidad_pg
- id (integer), objectid (integer), expediente (text), elemento (text), exposicion (integer), fragilidad (integer), resistencia (integer), resilencia (integer), vulnerabil (numeric), nivel_vuln (text), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), cod_depart (integer), departamen (text), cod_munic (integer), municipio (text), geometry (text), tipo (text), categoria (text)

### puntomuestreoflora
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), nombre (text), id_muest (text), n_cobert (text), nomenclat (integer), t_muest (numeric), area_um_ha (numeric), longi_tr_m (numeric), cuerpo_agu (text), profund (numeric), descrip (text), fec_muest (timestamp), estacional (numeric), localidad (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### puntomuestreofauna
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), nombre (text), id_mues_pt (text), n_cobert (text), nomenclat (integer), t_muest (numeric), habitat (text), descrip (text), fec_muest (timestamp), estacional (numeric), cuerpo_agu (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### transectomuestreofauna
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), nombre (text), id_mues_tr (text), t_transec (integer), ot_transec (text), n_cobert (text), nomenclat (integer), habitat (text), descrip (text), fec_muest (timestamp), estacional (numeric), cuerpo_agu (text), cota_min (numeric), cota_max (numeric), longitud_m (numeric), shape_leng (numeric), geometry (text), tipo (text), categoria (text)

### ocupacioncauce
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), car (numeric), nombre (text), id_ocu_cau (text), nom_c_ag (text), estado_oc (numeric), margen (numeric), t_caudal (numeric), t_fue_sup (numeric), tipo_ocup (text), especific (text), ah (text), zh (text), szh (text), n_nv_sub (text), c_nv_sub (text), n_mic_cue (text), c_mic_cue (text), observ (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### puntomuestreoaguasuper
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), car (numeric), nombre (text), id_punto_m (text), tipo_punto (integer), ocasional (text), fc_mon_agu (numeric), id_act_rel (text), cate_monit (numeric), tip_fu_sup (numeric), nom_c_ag (text), t_caudal (numeric), ah (text), zh (text), szh (text), n_nv_sub (text), c_nv_sub (text), n_mic_cue (text), c_mic_cue (text), observ (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### usosyusuariosrecursohidrico
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), nombre (text), id_usos_us (text), tip_fu_sup (numeric), nom_c_ag (text), u_aprov_1 (numeric), d_u_apr_1 (numeric), u_aprov_2 (numeric), d_u_apr_2 (numeric), u_aprov_3 (numeric), d_u_apr_3 (numeric), u_aprov_4 (numeric), d_u_apr_4 (numeric), d_uso_tot (numeric), ah (text), zh (text), szh (text), n_nv_sub (text), c_nv_sub (text), n_mic_cue (text), c_mic_cue (text), desc_usuar (text), observ (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### puntohidrogeologico
- id (integer), expediente (text), operador (text), proyecto (text), vereda (text), municipio (text), depto (text), car (numeric), nombre (text), id_punto_h (text), tipo_punto (numeric), uni_geolo (text), nom_predio (text), cond_propi (numeric), sitio (text), fec_caract (timestamp), diligencia (text), fec_const (timestamp), diam_ext (numeric), diam_int (numeric), anc_ext (numeric), lar_etx (numeric), profund_m (numeric), long_super (numeric), niv_piezom (numeric), per_corpo (numeric), cauda_corp (numeric), material (text), met_explot (numeric), t_energia (numeric), us_di_pozo (numeric), med_surg (numeric), t_manant (numeric), p_manant (numeric), condi_punt (numeric), prop_pto (numeric), u_aprov_1 (numeric), d_u_apr_1 (numeric), u_aprov_2 (numeric), d_u_apr_2 (numeric), u_aprov_3 (numeric), d_u_apr_3 (numeric), u_aprov_4 (numeric), d_u_apr_4 (numeric), d_uso_tot (numeric), n_us_pub (integer), n_us_dom (integer), t_indust (text), t_cultivo (text), a_irrig_ha (numeric), t_agroind (text), n_anim (integer), resid_sol (numeric), man_resid (numeric), obs_resid (text), observ (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### puntomuestreoaguasubter
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), vereda (text), municipio (text), depto (text), car (numeric), nombre (text), id_punto_m (text), tipo_punto (integer), ocasional (text), fc_mon_sub (numeric), id_relacio (text), observ (text), cota (numeric), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### aprovechaforestalpg
- id (integer), expediente (text), operador (text), proyecto (text), nomb_a_apr (text), n_cobert (text), nomenclat (integer), nomb_ecosi (text), individuos (integer), vol_esti (numeric), vol_max (numeric), biom_t_apr (numeric), carb_t_apr (numeric), observ (text), area_ha (numeric), geometry (text), tipo (text), categoria (text)

### aprovechaforestalpt
- id (integer), expediente (text), operador (text), proyecto (text), num_act_ad (text), fec_act_ad (timestamp), art_act_ad (text), est_indivi (integer), id_indivi (text), division (text), clase (text), orden (text), familia (text), genero (text), especie (text), n_comun (text), categ_cit (numeric), categ_uicn (numeric), cate_minis (numeric), t_distrib (numeric), veda (numeric), resolucion (text), entid_veda (numeric), vigen_veda (numeric), uso (numeric), dap_indiv (numeric), ab_indiv (numeric), h_total (numeric), h_fuste (numeric), vol_total (numeric), vol_com (numeric), biom_indiv (numeric), carb_indiv (numeric), fecha_c_a (timestamp), observ (text), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### coberturatierra
- id (integer), expediente (text), operador (text), proyecto (text), id_cobert (integer), n1_cobert (numeric), n2_cobert (numeric), n3_cobert (numeric), n4_cobert (numeric), n5_cobert (numeric), n6_cobert (numeric), nomenclat (integer), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### ecosistema
- id (integer), expediente (text), operador (text), proyecto (text), id_ecosis (integer), gran_bioma (numeric), bioma (numeric), dis_biogeo (numeric), z_climat (numeric), n_ugm_igac (text), n_ugm_sgc (text), n3_cobert (numeric), n4_cobert (numeric), n5_cobert (numeric), n6_cobert (numeric), nombre (text), nomenclat (text), represent (numeric), rareza (numeric), remanencia (numeric), pot_transf (numeric), s_ec_n1 (numeric), s_ec_n2 (numeric), riq_clave (numeric), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### amenazaotras
- id (integer), expediente (text), tipo_even (numeric), entidad (text), grad_ame (numeric), peso_ame (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### elementosexpuestosln
- id (integer), expediente (text), nombre (text), nomenclat (text), clas_infra (numeric), est_infra (numeric), calidad (numeric), no_habit (numeric), valor_rep (integer), observ (text), longitud_m (numeric), shape_leng (numeric), geometry (text), tipo (text), categoria (text)

### elementosexpuestospg
- id (integer), expediente (text), nombre (text), nomenclat (text), clas_infra (numeric), est_infra (numeric), calidad (numeric), no_habit (numeric), valor_rep (integer), grupo_uso (numeric), uso_act (numeric), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### elementosexpuestospt
- id (integer), expediente (text), nombre (text), nomenclat (text), clas_infra (numeric), est_infra (numeric), calidad (numeric), no_habit (numeric), valor_rep (integer), coor_este (numeric), coor_norte (numeric), observ (text), geometry (text), tipo (text), categoria (text)

### compensacionbiodiversidad
- id (integer), expediente (text), operador (text), proyecto (text), id_comp (text), no_actoad (integer), fe_actoad (timestamp), t_acto_obl (numeric), res_obl (integer), fe_obl (timestamp), area_comp (numeric), act_comp (numeric), sbact_comp (numeric), otra_act (text), descripcio (text), area_pg_ha (numeric), estado (numeric), fecha_ini (timestamp), fecha_ter (timestamp), ecosist_im (numeric), o_ecos_im (text), afect_sol (numeric), contex_pei (numeric), fac_repres (numeric), fac_rarez (numeric), fac_remane (numeric), fac_p_tran (numeric), factorcomp (numeric), ecosistema (numeric), otr_ecosis (text), contex_pec (numeric), prec_suelo (numeric), val_e_com (numeric), val_ej_act (numeric), valor_act (numeric), obser_cppb (text), geometry (text), tipo (text), categoria (text)

### vulnerabilidad_pt
- id (integer), expediente (text), ame_inu_ra (numeric), ame_inu_va (text), ame_mm_ra (numeric), ame_mm_val (text), ame_inc_ra (numeric), ame_inc_va (text), ame_at_ra (numeric), ame_at_val (text), ind_perdid (numeric), ind_frag (numeric), ind_f_res (numeric), ind_p_max (numeric), vuln_rango (numeric), vuln_valor (text), observ (text), coor_este (numeric), coor_norte (numeric), geometry (text), tipo (text), categoria (text)

### suscept_inundaciones
- id (integer), expediente (text), suscep_ran (text), suscep_inu (numeric), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### suscept_incendios
- id (integer), expediente (text), zon_ine_id (text), n1_cobert (numeric), n2_cobert (numeric), n3_cobert (numeric), n4_cobert (numeric), n5_cobert (numeric), n6_cobert (numeric), nomenclat (text), tipo_comb (text), biomasa (text), humedad_v (text), isci (numeric), suscep_ran (text), suscep_in (numeric), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)

### escenriesgoincendio
- id (integer), expediente (text), amen_rango (numeric), amen_valor (text), vuln_rango (numeric), vuln_valor (text), ries_rango (numeric), ries_valor (text), ind_rie_t (text), observ (text), area_ha (numeric), shape_leng (numeric), shape_area (numeric), geometry (text), tipo (text), categoria (text)


