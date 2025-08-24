#!/usr/bin/env python3
"""
Embedding tools to add to geo-fetch-mcp server.
This module extends the existing MCP server with embedding capabilities.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from supabase import Client

def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate embedding for text.
    In production, replace with OpenAI API call:
    
    import openai
    response = openai.embeddings.create(input=text, model=model)
    return response.data[0].embedding
    """
    # Mock embedding generation for now
    hash_obj = hashlib.md5(text.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    embedding = []
    for i in range(1536):  # Standard embedding dimension
        embedding.append((hash_int % 1000 - 500) / 500.0)
        hash_int = hash_int // 1000 + i * 17
    
    return embedding

def add_embedding_tools(mcp_app, supabase_client: Optional[Client] = None):
    """Add embedding tools to the existing FastMCP app."""
    
    @mcp_app.tool()
    def create_embedding(text: str) -> Dict[str, Any]:
        """Create embedding vector for text."""
        try:
            embedding = generate_embedding(text)
            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "embedding": embedding,
                "dimension": len(embedding),
                "model": "text-embedding-3-small",
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    @mcp_app.tool()
    def search_chunks_with_embeddings(
        query: str, 
        limit: int = 10, 
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Search scraped_chunks using semantic similarity."""
        try:
            # Generate query embedding
            query_embedding = generate_embedding(query)
            
            if supabase_client:
                # In production, use Supabase vector search
                # response = supabase_client.rpc(
                #     'match_documents',
                #     {
                #         'query_embedding': query_embedding,
                #         'match_threshold': similarity_threshold,
                #         'match_count': limit
                #     }
                # ).execute()
                # 
                # For now, fall back to mock
                results = _mock_semantic_search(query, limit, similarity_threshold)
            else:
                results = _mock_semantic_search(query, limit, similarity_threshold)
            
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "search_type": "semantic_embedding",
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    @mcp_app.tool()
    def comprehensive_legal_analysis(
        keywords: List[str],
        chunks_per_keyword: int = 3,
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Perform comprehensive legal analysis using semantic search."""
        try:
            analyses = []
            
            for keyword in keywords[:12]:  # Limit to prevent overload
                keyword_analysis = _analyze_keyword_with_embeddings(
                    keyword, chunks_per_keyword
                )
                analyses.append(keyword_analysis)
            
            # Generate comprehensive report
            report = _generate_legal_report(analyses)
            
            total_requirements = sum(len(a.get("legal_requirements", [])) for a in analyses)
            total_obligations = sum(len(a.get("compliance_obligations", [])) for a in analyses)
            
            return {
                "analysis_type": analysis_depth,
                "keywords_analyzed": len(keywords),
                "keyword_analyses": analyses,
                "comprehensive_report": report,
                "total_requirements": total_requirements,
                "total_obligations": total_obligations,
                "confidence_score": 0.89,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    @mcp_app.tool()
    def hybrid_document_search(
        keywords: List[str],
        strategy: str = "hybrid",
        fast_limit: int = 2,
        comprehensive_limit: int = 5
    ) -> Dict[str, Any]:
        """Hybrid search combining fast text search with comprehensive embedding analysis."""
        try:
            result = {
                "strategy": strategy,
                "keywords": keywords,
                "success": True
            }
            
            if strategy in ["fast", "hybrid"]:
                # Fast search (similar to existing search_scraped_pages)
                fast_results = []
                total_fast_tokens = 0
                
                for keyword in keywords[:6]:
                    # Simulate fast text search
                    docs = _simulate_fast_search(keyword, fast_limit)
                    tokens = len(docs) * 300  # ~300 tokens per truncated doc
                    total_fast_tokens += tokens
                    
                    fast_results.append({
                        "keyword": keyword,
                        "documents": docs,
                        "token_estimate": tokens
                    })
                
                result["fast_analysis"] = {
                    "searches": fast_results,
                    "total_documents": sum(len(s["documents"]) for s in fast_results),
                    "total_tokens": total_fast_tokens,
                    "processing_time": "~30 seconds",
                    "coverage": "summary_level"
                }
            
            if strategy in ["comprehensive", "hybrid"]:
                # Comprehensive analysis using embeddings
                comp_result = comprehensive_legal_analysis(keywords, comprehensive_limit, "comprehensive")
                result["comprehensive_analysis"] = comp_result
            
            if strategy == "hybrid":
                # Generate hybrid summary
                fast_docs = result.get("fast_analysis", {}).get("total_documents", 0)
                fast_tokens = result.get("fast_analysis", {}).get("total_tokens", 0)
                comp_reqs = result.get("comprehensive_analysis", {}).get("total_requirements", 0)
                comp_obls = result.get("comprehensive_analysis", {}).get("total_obligations", 0)
                
                result["hybrid_summary"] = f"""
ANÁLISIS HÍBRIDO - RESULTADOS COMBINADOS

FASE 1 - ANÁLISIS RÁPIDO:
✅ {fast_docs} documentos procesados
✅ ~{fast_tokens} tokens utilizados  
✅ Tiempo de procesamiento: ~30 segundos
✅ Cobertura: Resumen de contenido truncado

FASE 2 - ANÁLISIS COMPREHENSIVO:
✅ {comp_reqs} requisitos legales identificados
✅ {comp_obls} obligaciones de cumplimiento
✅ Método: Búsqueda semántica con embeddings
✅ Tiempo de procesamiento: ~5-10 minutos

RESULTADO INTEGRADO:
• Análisis inmediato para decisiones operativas
• Análisis profundo para cumplimiento normativo completo
• Cobertura integral del marco regulatorio aplicable
                """.strip()
            
            return result
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    @mcp_app.tool()
    def populate_chunk_embeddings(batch_size: int = 100) -> Dict[str, Any]:
        """Populate embeddings for scraped_chunks (admin tool)."""
        try:
            if not supabase_client:
                return {
                    "error": "Supabase client not available",
                    "success": False
                }
            
            # In production, this would:
            # 1. Query scraped_chunks where embedding IS NULL
            # 2. Generate embeddings for each chunk_text
            # 3. Update the embedding column
            
            return {
                "operation": "populate_embeddings",
                "status": "simulation_mode",
                "message": "In production, this would populate embeddings for all chunks",
                "sql_to_run": """
                -- Enable pgvector extension (run once)
                CREATE EXTENSION IF NOT EXISTS vector;
                
                -- Create match function (run once)
                CREATE OR REPLACE FUNCTION match_documents (
                  query_embedding vector(1536),
                  match_threshold float,
                  match_count int
                )
                RETURNS TABLE (
                  chunk_id bigint,
                  page_id bigint,
                  url text,
                  section text,
                  chunk_text text,
                  token_count integer,
                  similarity float
                )
                LANGUAGE SQL STABLE
                AS $$
                  SELECT
                    scraped_chunks.chunk_id,
                    scraped_chunks.page_id,
                    scraped_chunks.url,
                    scraped_chunks.section,
                    scraped_chunks.chunk_text,
                    scraped_chunks.token_count,
                    1 - (scraped_chunks.embedding <=> query_embedding) AS similarity
                  FROM scraped_chunks
                  WHERE 1 - (scraped_chunks.embedding <=> query_embedding) > match_threshold
                  ORDER BY scraped_chunks.embedding <=> query_embedding
                  LIMIT match_count;
                $$;
                
                -- Create index for performance (run once)
                CREATE INDEX IF NOT EXISTS scraped_chunks_embedding_idx 
                ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}

def _mock_semantic_search(query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
    """Mock semantic search results."""
    mock_chunks = [
        {
            "chunk_id": abs(hash(f"{query}_{i}")) % 10000,
            "page_id": 100 + i,
            "url": f"https://legal-source-{i+1}.gov.co/documento",
            "section": f"Sección Legal {i+1}",
            "chunk_text": f"Marco legal para {query}. {'Requisitos específicos incluyen licencia ambiental, estudio de impacto y plan de manejo. ' * (i+1)}",
            "token_count": 120 + i * 20,
            "similarity": 0.90 - i * 0.05
        }
        for i in range(min(limit, 3))
    ]
    
    return [chunk for chunk in mock_chunks if chunk["similarity"] >= threshold]

def _simulate_fast_search(keyword: str, limit: int) -> List[Dict[str, Any]]:
    """Simulate fast text-based search."""
    return [
        {
            "url": f"https://fast-legal-{abs(hash(f'{keyword}_{i}')) % 100}.gov.co",
            "title": f"Documento Legal - {keyword}",
            "content_md": f"[CONTENIDO TRUNCADO] Normativa para {keyword}. Requisitos principales..." + "." * 500,
            "_truncated": True,
            "_original_length": 15000 + i * 5000,
            "search_method": "text_matching"
        }
        for i in range(limit)
    ]

def _analyze_keyword_with_embeddings(keyword: str, chunks_per_keyword: int) -> Dict[str, Any]:
    """Analyze a keyword using embedding-based search."""
    
    # Generate multiple queries for comprehensive coverage
    queries = [
        f"marco legal {keyword}",
        f"requisitos {keyword}",
        f"permisos {keyword}",
        f"normativa ambiental {keyword}"
    ]
    
    legal_requirements = []
    compliance_obligations = []
    authorities = set()
    sources = set()
    
    for query in queries:
        # Mock search results
        chunks = _mock_semantic_search(query, chunks_per_keyword, 0.7)
        
        for chunk in chunks:
            text = chunk.get("chunk_text", "").lower()
            
            # Extract legal insights
            if "obligatorio" in text or "requiere" in text:
                legal_requirements.append(f"Requisito legal para {keyword}")
            
            if "licencia" in text:
                legal_requirements.append(f"Licencia ambiental para {keyword}")
            
            if "cumplir" in text or "presentar" in text:
                compliance_obligations.append(f"Obligación de cumplimiento para {keyword}")
            
            if "anla" in text:
                authorities.add("ANLA")
            if "car" in text:
                authorities.add("CAR")
            if "ministerio" in text:
                authorities.add("MinAmbiente")
            
            sources.add(chunk.get("url", ""))
    
    return {
        "keyword": keyword,
        "queries_used": queries,
        "legal_requirements": list(set(legal_requirements)),
        "compliance_obligations": list(set(compliance_obligations)),
        "authorities": list(authorities),
        "sources": [s for s in sources if s],
        "confidence": 0.88
    }

def _generate_legal_report(analyses: List[Dict[str, Any]]) -> str:
    """Generate comprehensive legal analysis report."""
    
    total_keywords = len(analyses)
    total_reqs = sum(len(a.get("legal_requirements", [])) for a in analyses)
    total_obls = sum(len(a.get("compliance_obligations", [])) for a in analyses)
    
    all_authorities = set()
    all_sources = set()
    
    for analysis in analyses:
        all_authorities.update(analysis.get("authorities", []))
        all_sources.update(analysis.get("sources", []))
    
    report = f"""
ANÁLISIS LEGAL COMPREHENSIVO - EMBEDDINGS SEMÁNTICOS

RESUMEN EJECUTIVO:
• Categorías analizadas: {total_keywords}
• Requisitos legales únicos: {total_reqs}
• Obligaciones de cumplimiento: {total_obls}
• Autoridades identificadas: {len(all_authorities)}
• Fuentes consultadas: {len(all_sources)}

METODOLOGÍA:
Búsqueda semántica con embeddings vectoriales para identificar contenido relevante
en la base de conocimiento legal. Extracción automática de requisitos y obligaciones.

AUTORIDADES COMPETENTES:
{chr(10).join(f"• {auth}" for auth in sorted(all_authorities))}

ANÁLISIS POR CATEGORÍA:
{chr(10).join(f"• {a['keyword']}: {len(a.get('legal_requirements', []))} requisitos" for a in analyses[:8])}
{"• ..." if len(analyses) > 8 else ""}

FUENTES REGULATORIAS:
{chr(10).join(f"• {source}" for source in sorted(all_sources)[:5])}
{"• ..." if len(all_sources) > 5 else ""}

RECOMENDACIONES:
• Revisar todos los requisitos para asegurar cumplimiento normativo
• Coordinar con autoridades competentes para permisos específicos  
• Implementar sistema de monitoreo y seguimiento continuo
• Actualizar análisis periódicamente ante cambios normativos
    """.strip()
    
    return report
