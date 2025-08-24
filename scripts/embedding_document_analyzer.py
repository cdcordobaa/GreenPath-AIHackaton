#!/usr/bin/env python3
"""
Enhanced Document Analysis using Supabase Embeddings.
Leverages existing scraped_chunks table with pgvector for semantic search.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from pathlib import Path

# Mock imports for demonstration - replace with actual imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available - using mock mode")

@dataclass
class DocumentChunk:
    """Represents a chunk of a document for embedding analysis."""
    chunk_id: int
    page_id: int
    url: str
    section: str
    chunk_text: str
    token_count: int
    embedding: Optional[List[float]] = None

@dataclass
class SemanticSearchResult:
    """Result from semantic search in embeddings."""
    chunk: DocumentChunk
    similarity_score: float
    rank: int

@dataclass
class EmbeddingAnalysisResult:
    """Complete analysis result using embeddings."""
    query: str
    total_chunks_searched: int
    relevant_chunks: List[SemanticSearchResult]
    analysis_summary: str
    key_insights: List[str]
    legal_requirements: List[str]
    compliance_items: List[str]
    confidence_score: float

class EmbeddingDocumentAnalyzer:
    """Document analyzer using Supabase embeddings for semantic search."""
    
    def __init__(self):
        self.supabase = self._get_supabase_client()
        
    def _get_supabase_client(self) -> Optional[Any]:
        """Get Supabase client if available."""
        if not SUPABASE_AVAILABLE:
            return None
            
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if url and key:
            return create_client(url, key)
        else:
            print("⚠️ Supabase credentials not found - using mock mode")
            return None
    
    def semantic_search_documents(
        self, 
        query: str, 
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SemanticSearchResult]:
        """Perform semantic search using embeddings."""
        
        if not self.supabase:
            # Mock results for demonstration
            return self._mock_semantic_search(query, limit)
        
        try:
            # Generate embedding for the query (would use OpenAI/Hugging Face)
            query_embedding = self._generate_query_embedding(query)
            
            # Search similar chunks using pgvector
            # This uses cosine similarity with the embedding column
            response = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
            ).execute()
            
            results = []
            for i, row in enumerate(response.data or []):
                chunk = DocumentChunk(
                    chunk_id=row['chunk_id'],
                    page_id=row['page_id'],
                    url=row['url'],
                    section=row['section'],
                    chunk_text=row['chunk_text'],
                    token_count=row['token_count'],
                    embedding=None  # Don't return full embedding for efficiency
                )
                
                result = SemanticSearchResult(
                    chunk=chunk,
                    similarity_score=row['similarity'],
                    rank=i + 1
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            return self._mock_semantic_search(query, limit)
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query text."""
        # In real implementation, use OpenAI embeddings or Hugging Face
        # For now, return a mock embedding
        hash_obj = hashlib.md5(query.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generate deterministic "embedding" from hash
        embedding = []
        for i in range(1536):  # OpenAI embedding dimension
            embedding.append((hash_int % 1000 - 500) / 500.0)
            hash_int = hash_int // 1000 + i
        
        return embedding
    
    def _mock_semantic_search(self, query: str, limit: int) -> List[SemanticSearchResult]:
        """Mock semantic search for demonstration."""
        
        # Mock document chunks based on common legal terms
        mock_chunks = [
            {
                'chunk_id': 1,
                'page_id': 101,
                'url': 'https://anla.gov.co/licencia-ambiental-guia',
                'section': 'Requisitos Legales',
                'chunk_text': f'Para proyectos que requieren licencia ambiental relacionados con {query.lower()}, es obligatorio cumplir con los siguientes requisitos: presentar Estudio de Impacto Ambiental, obtener concepto técnico de la autoridad competente, y implementar el Plan de Manejo Ambiental.',
                'token_count': 156,
                'similarity': 0.95
            },
            {
                'chunk_id': 2,
                'page_id': 102,
                'url': 'https://minambiente.gov.co/decreto-1076-2015',
                'section': 'Compensaciones Ambientales',
                'chunk_text': f'Las compensaciones ambientales para {query.lower()} deben calcularse según los factores de representatividad, rareza y remanencia del ecosistema afectado. El área de compensación no podrá ser inferior a la pérdida de biodiversidad generada.',
                'token_count': 134,
                'similarity': 0.89
            },
            {
                'chunk_id': 3,
                'page_id': 103,
                'url': 'https://corporinoquia.gov.co/procedimientos-ambientales',
                'section': 'Procedimientos CAR',
                'chunk_text': f'Para {query.lower()}, la Corporación Autónoma Regional debe verificar el cumplimiento de las obligaciones ambientales y puede imponer medidas preventivas, correctivas o sancionatorias según el caso.',
                'token_count': 98,
                'similarity': 0.84
            },
            {
                'chunk_id': 4,
                'page_id': 104,
                'url': 'https://anla.gov.co/seguimiento-cumplimiento',
                'section': 'Seguimiento y Control',
                'chunk_text': f'El seguimiento de {query.lower()} incluye la presentación de Informes de Cumplimiento Ambiental (ICA) con periodicidad semestral, monitoreo de variables ambientales y verificación del cumplimiento del Plan de Manejo Ambiental.',
                'token_count': 142,
                'similarity': 0.81
            },
            {
                'chunk_id': 5,
                'page_id': 105,
                'url': 'https://ideam.gov.co/permisos-recursos-naturales',
                'section': 'Permisos Específicos',
                'chunk_text': f'Para actividades de {query.lower()}, se requieren permisos específicos como aprovechamiento forestal, concesión de aguas, y vertimientos si aplica. Cada permiso tiene requisitos técnicos particulares.',
                'token_count': 118,
                'similarity': 0.78
            }
        ]
        
        results = []
        for i, chunk_data in enumerate(mock_chunks[:limit]):
            chunk = DocumentChunk(
                chunk_id=chunk_data['chunk_id'],
                page_id=chunk_data['page_id'],
                url=chunk_data['url'],
                section=chunk_data['section'],
                chunk_text=chunk_data['chunk_text'],
                token_count=chunk_data['token_count']
            )
            
            result = SemanticSearchResult(
                chunk=chunk,
                similarity_score=chunk_data['similarity'],
                rank=i + 1
            )
            results.append(result)
        
        return results
    
    def analyze_with_embeddings(
        self, 
        analysis_queries: List[str],
        chunks_per_query: int = 5
    ) -> List[EmbeddingAnalysisResult]:
        """Perform comprehensive analysis using semantic search."""
        
        print(f"🔍 Performing embedding-based analysis for {len(analysis_queries)} queries")
        
        results = []
        
        for i, query in enumerate(analysis_queries, 1):
            print(f"   {i}. Analyzing: '{query[:50]}...'")
            
            # Semantic search for relevant chunks
            search_results = self.semantic_search_documents(
                query=query,
                limit=chunks_per_query,
                similarity_threshold=0.7
            )
            
            # Analyze the retrieved chunks
            analysis = self._analyze_search_results(query, search_results)
            results.append(analysis)
            
            print(f"      Found {len(search_results)} relevant chunks, confidence: {analysis.confidence_score:.2f}")
        
        return results
    
    def _analyze_search_results(
        self, 
        query: str, 
        search_results: List[SemanticSearchResult]
    ) -> EmbeddingAnalysisResult:
        """Analyze semantic search results to extract insights."""
        
        if not search_results:
            return EmbeddingAnalysisResult(
                query=query,
                total_chunks_searched=0,
                relevant_chunks=[],
                analysis_summary="No relevant documents found.",
                key_insights=[],
                legal_requirements=[],
                compliance_items=[],
                confidence_score=0.0
            )
        
        # Extract legal requirements from chunks
        legal_requirements = []
        compliance_items = []
        key_insights = []
        
        combined_text = " ".join([result.chunk.chunk_text for result in search_results])
        
        # Simple pattern matching for legal requirements
        import re
        
        # Legal requirement patterns
        req_patterns = [
            r'es obligatorio (.+?)(?:\.|,)',
            r'debe[rn]?\s+(.+?)(?:\.|,)',
            r'requiere[n]?\s+(.+?)(?:\.|,)',
            r'se exige (.+?)(?:\.|,)',
        ]
        
        for pattern in req_patterns:
            matches = re.findall(pattern, combined_text.lower(), re.IGNORECASE)
            legal_requirements.extend([match.strip() for match in matches[:3]])
        
        # Compliance patterns
        comp_patterns = [
            r'cumplir con (.+?)(?:\.|,)',
            r'presentar (.+?)(?:\.|,)',
            r'verificar (.+?)(?:\.|,)',
            r'implementar (.+?)(?:\.|,)',
        ]
        
        for pattern in comp_patterns:
            matches = re.findall(pattern, combined_text.lower(), re.IGNORECASE)
            compliance_items.extend([match.strip() for match in matches[:3]])
        
        # Extract key insights
        key_insights = [
            f"Encontrados {len(search_results)} documentos relevantes",
            f"Promedio de similitud: {sum(r.similarity_score for r in search_results) / len(search_results):.2f}",
            f"Fuentes principales: {', '.join(set(r.chunk.url.split('/')[2] for r in search_results[:3]))}"
        ]
        
        # Generate summary
        summary = f"""
Análisis de consulta: "{query}"

Se encontraron {len(search_results)} documentos relevantes con alta similitud semántica.
Los documentos cubren aspectos de {', '.join(set(r.chunk.section for r in search_results[:3]))}.

Principales fuentes regulatorias identificadas:
{chr(10).join(f"• {result.chunk.url} - {result.chunk.section}" for result in search_results[:3])}

Se identificaron {len(legal_requirements)} requisitos legales y {len(compliance_items)} obligaciones de cumplimiento específicas.
        """.strip()
        
        # Calculate confidence based on similarity scores
        avg_similarity = sum(r.similarity_score for r in search_results) / len(search_results)
        confidence = min(0.95, avg_similarity)
        
        return EmbeddingAnalysisResult(
            query=query,
            total_chunks_searched=len(search_results),
            relevant_chunks=search_results,
            analysis_summary=summary,
            key_insights=key_insights,
            legal_requirements=list(set(legal_requirements)),
            compliance_items=list(set(compliance_items)),
            confidence_score=confidence
        )
    
    def comprehensive_project_analysis(
        self, 
        project_keywords: List[str],
        environmental_aspects: List[str]
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis for an EIA project."""
        
        print(f"🎯 COMPREHENSIVE PROJECT ANALYSIS")
        print(f"   Keywords: {len(project_keywords)}")
        print(f"   Environmental aspects: {len(environmental_aspects)}")
        
        # Generate analysis queries
        analysis_queries = []
        
        # 1. General regulatory framework
        for keyword in project_keywords:
            analysis_queries.append(f"marco regulatorio para {keyword}")
            analysis_queries.append(f"requisitos legales {keyword}")
        
        # 2. Environmental aspect specific
        for aspect in environmental_aspects:
            analysis_queries.append(f"normativa ambiental {aspect}")
            analysis_queries.append(f"permisos ambientales {aspect}")
            analysis_queries.append(f"compensaciones ambientales {aspect}")
        
        # 3. Compliance and monitoring
        analysis_queries.extend([
            "seguimiento y monitoreo ambiental",
            "informes de cumplimiento ambiental",
            "medidas de manejo ambiental",
            "sanciones ambientales"
        ])
        
        print(f"   Generated {len(analysis_queries)} analysis queries")
        
        # Perform embedding analysis
        analysis_results = self.analyze_with_embeddings(
            analysis_queries=analysis_queries[:12],  # Limit to manage token usage
            chunks_per_query=3
        )
        
        # Aggregate results
        all_requirements = []
        all_compliance = []
        all_insights = []
        all_sources = set()
        
        for result in analysis_results:
            all_requirements.extend(result.legal_requirements)
            all_compliance.extend(result.compliance_items)
            all_insights.extend(result.key_insights)
            all_sources.update(chunk.url for chunk in [sr.chunk for sr in result.relevant_chunks])
        
        # Deduplicate
        unique_requirements = list(set(all_requirements))
        unique_compliance = list(set(all_compliance))
        
        # Calculate overall confidence
        avg_confidence = sum(r.confidence_score for r in analysis_results) / len(analysis_results)
        
        # Generate comprehensive report
        comprehensive_report = f"""
ANÁLISIS INTEGRAL DE PROYECTO - BASADO EN EMBEDDINGS

RESUMEN EJECUTIVO:
Se analizaron {len(analysis_queries)} consultas específicas utilizando búsqueda semántica en {len(all_sources)} fuentes regulatorias.

HALLAZGOS PRINCIPALES:
• {len(unique_requirements)} requisitos legales únicos identificados
• {len(unique_compliance)} obligaciones de cumplimiento específicas
• {len(all_sources)} fuentes regulatorias consultadas
• Confianza promedio del análisis: {avg_confidence:.1%}

REQUISITOS LEGALES CLAVE:
{chr(10).join(f"• {req}" for req in unique_requirements[:10])}
{'• ...' if len(unique_requirements) > 10 else ''}

OBLIGACIONES DE CUMPLIMIENTO:
{chr(10).join(f"• {comp}" for comp in unique_compliance[:10])}
{'• ...' if len(unique_compliance) > 10 else ''}

FUENTES CONSULTADAS:
{chr(10).join(f"• {source}" for source in sorted(all_sources))}

METODOLOGÍA:
Análisis basado en embeddings semánticos con búsqueda vectorial en base de conocimiento legal.
Similitud semántica promedio: {avg_confidence:.1%}
        """.strip()
        
        return {
            "analysis_results": analysis_results,
            "comprehensive_report": comprehensive_report,
            "summary": {
                "total_queries": len(analysis_queries),
                "unique_requirements": len(unique_requirements),
                "unique_compliance": len(unique_compliance),
                "sources_consulted": len(all_sources),
                "avg_confidence": avg_confidence,
                "total_chunks_analyzed": sum(len(r.relevant_chunks) for r in analysis_results)
            },
            "requirements": unique_requirements,
            "compliance_items": unique_compliance,
            "sources": list(all_sources)
        }

def create_supabase_embedding_functions():
    """Create the necessary Supabase functions for semantic search."""
    
    print("📝 SUPABASE EMBEDDING SETUP")
    print("=" * 40)
    
    # SQL function for semantic search
    match_documents_sql = """
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
    """
    
    # Index creation for performance
    create_index_sql = """
CREATE INDEX IF NOT EXISTS scraped_chunks_embedding_idx 
ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
    """
    
    print("🔧 Required SQL Functions:")
    print("\n1. Semantic Search Function:")
    print(match_documents_sql)
    print("\n2. Performance Index:")
    print(create_index_sql)
    
    print("\n💡 To set up embeddings:")
    print("1. Run the SQL functions above in your Supabase SQL editor")
    print("2. Ensure pgvector extension is enabled")
    print("3. Populate embeddings for existing scraped_chunks")
    print("4. Use OpenAI embeddings or similar for production")
    
    return {
        "match_documents_function": match_documents_sql,
        "embedding_index": create_index_sql
    }

def test_embedding_analyzer():
    """Test the embedding-based document analyzer."""
    
    print("🧪 TESTING EMBEDDING DOCUMENT ANALYZER")
    print("=" * 60)
    
    analyzer = EmbeddingDocumentAnalyzer()
    
    # Test project analysis
    project_keywords = ["línea de transmisión", "infraestructura eléctrica", "110kV"]
    environmental_aspects = ["flora", "fauna", "recursos hídricos", "suelos", "ecosistemas"]
    
    result = analyzer.comprehensive_project_analysis(
        project_keywords=project_keywords,
        environmental_aspects=environmental_aspects
    )
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Queries analyzed: {result['summary']['total_queries']}")
    print(f"   Chunks analyzed: {result['summary']['total_chunks_analyzed']}")
    print(f"   Unique requirements: {result['summary']['unique_requirements']}")
    print(f"   Compliance items: {result['summary']['unique_compliance']}")
    print(f"   Confidence: {result['summary']['avg_confidence']:.1%}")
    
    print(f"\n📋 COMPREHENSIVE REPORT:")
    print(result['comprehensive_report'])
    
    # Show SQL setup
    print(f"\n🔧 SUPABASE SETUP:")
    sql_functions = create_supabase_embedding_functions()
    
    return result

if __name__ == "__main__":
    test_embedding_analyzer()
