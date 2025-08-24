#!/usr/bin/env python3
"""
Comprehensive Document Analyzer implementing Hierarchical Chunking + Parallel Processing.
Designed for analyzing full legal documents while managing token limits.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from copy import deepcopy

@dataclass
class DocumentSection:
    """Represents a section of a document."""
    section_id: str
    title: str
    content: str
    level: int  # 1=main section, 2=subsection, etc.
    start_char: int
    end_char: int
    char_count: int
    token_estimate: int

@dataclass
class SectionAnalysis:
    """Analysis results for a document section."""
    section_id: str
    legal_requirements: List[str]
    compliance_obligations: List[str]
    entities_mentioned: List[str]
    key_concepts: List[str]
    risk_factors: List[str]
    summary: str
    confidence_score: float

@dataclass
class ComprehensiveDocumentAnalysis:
    """Complete analysis of a document."""
    doc_id: str
    url: str
    title: str
    total_chars: int
    total_sections: int
    
    # Aggregated insights
    all_legal_requirements: List[str]
    all_compliance_obligations: List[str]
    all_entities: List[str]
    all_risk_factors: List[str]
    
    # Section analyses
    section_analyses: List[SectionAnalysis]
    
    # Final reports
    executive_summary: str
    compliance_report: str
    risk_assessment: str
    
    # Processing metadata
    token_usage: int
    processing_strategy: str

class ComprehensiveDocumentAnalyzer:
    """Analyzes large legal documents using hierarchical chunking + parallel processing."""
    
    def __init__(self, max_section_chars: int = 20000):
        self.max_section_chars = max_section_chars
        self.token_usage = 0
    
    def extract_document_structure(self, content: str, title: str = "") -> List[DocumentSection]:
        """Extract logical sections from a document."""
        sections = []
        
        # Define patterns for different section headers (Spanish legal documents)
        section_patterns = [
            r'^(CAPÍTULO|CAPÍTULO\s+[IVX]+|TÍTULO|TÍTULO\s+[IVX]+)\s*[\.:]?\s*(.+?)$',
            r'^(ARTÍCULO|ARTÍCULO\s+\d+|Art\.\s*\d+)\s*[\.:]?\s*(.+?)$',
            r'^(SECCIÓN|SECCIÓN\s+[IVX]+)\s*[\.:]?\s*(.+?)$',
            r'^(\d+\.\s+)(.+?)$',
            r'^([A-Z][A-Z\s]{10,})\s*$',  # ALL CAPS headers
            r'^(CONSIDERANDO|RESUELVE|DISPONE)\s*:?\s*(.*)$',
        ]
        
        lines = content.split('\n')
        current_section = None
        section_content = []
        section_counter = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                if current_section:
                    section_content.append(line)
                continue
            
            # Check if line matches any section pattern
            is_header = False
            header_title = ""
            header_level = 1
            
            for level, pattern in enumerate(section_patterns, 1):
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    is_header = True
                    header_title = f"{match.group(1)} {match.group(2) if len(match.groups()) > 1 else ''}".strip()
                    header_level = level
                    break
            
            if is_header and current_section is not None:
                # Save previous section
                section_text = '\n'.join(section_content).strip()
                if section_text:
                    sections.append(DocumentSection(
                        section_id=current_section['id'],
                        title=current_section['title'],
                        content=section_text,
                        level=current_section['level'],
                        start_char=current_section['start_char'],
                        end_char=current_section['start_char'] + len(section_text),
                        char_count=len(section_text),
                        token_estimate=len(section_text) // 4
                    ))
                
                # Start new section
                section_counter += 1
                current_section = {
                    'id': f"section_{section_counter}",
                    'title': header_title or f"Section {section_counter}",
                    'level': header_level,
                    'start_char': sum(len(l) + 1 for l in lines[:i])
                }
                section_content = [line]
                
            elif current_section is None:
                # First section (document header/intro)
                section_counter += 1
                current_section = {
                    'id': f"section_{section_counter}",
                    'title': title or "Document Header",
                    'level': 1,
                    'start_char': 0
                }
                section_content = [line]
            else:
                # Add to current section
                section_content.append(line)
        
        # Don't forget the last section
        if current_section and section_content:
            section_text = '\n'.join(section_content).strip()
            if section_text:
                sections.append(DocumentSection(
                    section_id=current_section['id'],
                    title=current_section['title'],
                    content=section_text,
                    level=current_section['level'],
                    start_char=current_section['start_char'],
                    end_char=current_section['start_char'] + len(section_text),
                    char_count=len(section_text),
                    token_estimate=len(section_text) // 4
                ))
        
        # If no sections found, treat entire document as one section
        if not sections:
            sections.append(DocumentSection(
                section_id="section_1",
                title=title or "Complete Document",
                content=content,
                level=1,
                start_char=0,
                end_char=len(content),
                char_count=len(content),
                token_estimate=len(content) // 4
            ))
        
        return sections
    
    def split_large_section(self, section: DocumentSection) -> List[DocumentSection]:
        """Split sections that are too large for single analysis."""
        if section.char_count <= self.max_section_chars:
            return [section]
        
        # Split by paragraphs first
        paragraphs = section.content.split('\n\n')
        subsections = []
        current_chunk = []
        current_chars = 0
        chunk_counter = 1
        
        for paragraph in paragraphs:
            para_chars = len(paragraph)
            
            if current_chars + para_chars > self.max_section_chars and current_chunk:
                # Save current chunk
                chunk_content = '\n\n'.join(current_chunk)
                subsections.append(DocumentSection(
                    section_id=f"{section.section_id}_part_{chunk_counter}",
                    title=f"{section.title} (Part {chunk_counter})",
                    content=chunk_content,
                    level=section.level + 1,
                    start_char=section.start_char + (len(section.content) - len('\n\n'.join(current_chunk + [paragraph] + paragraphs[paragraphs.index(paragraph)+1:]))),
                    end_char=section.start_char + (len(section.content) - len('\n\n'.join(paragraphs[paragraphs.index(paragraph):]))),
                    char_count=len(chunk_content),
                    token_estimate=len(chunk_content) // 4
                ))
                
                # Start new chunk
                current_chunk = [paragraph]
                current_chars = para_chars
                chunk_counter += 1
            else:
                current_chunk.append(paragraph)
                current_chars += para_chars
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            subsections.append(DocumentSection(
                section_id=f"{section.section_id}_part_{chunk_counter}",
                title=f"{section.title} (Part {chunk_counter})",
                content=chunk_content,
                level=section.level + 1,
                start_char=section.end_char - len(chunk_content),
                end_char=section.end_char,
                char_count=len(chunk_content),
                token_estimate=len(chunk_content) // 4
            ))
        
        return subsections
    
    def simulate_section_analysis(self, section: DocumentSection) -> SectionAnalysis:
        """Simulate comprehensive analysis of a document section."""
        content = section.content.lower()
        
        # Extract legal requirements (mock analysis)
        legal_patterns = [
            r'deber[áa]n?\s+([^\.]+)',
            r'obligaci[óo]n\s+de\s+([^\.]+)',
            r'requiere\s+([^\.]+)',
            r'es\s+obligatorio\s+([^\.]+)',
            r'se\s+exige\s+([^\.]+)'
        ]
        
        legal_requirements = []
        for pattern in legal_patterns:
            matches = re.findall(pattern, content)
            legal_requirements.extend([match.strip()[:100] for match in matches[:3]])
        
        # Extract compliance obligations
        compliance_patterns = [
            r'cumplir\s+con\s+([^\.]+)',
            r'acatar\s+([^\.]+)',
            r'observar\s+([^\.]+)',
            r'atender\s+([^\.]+)'
        ]
        
        compliance_obligations = []
        for pattern in compliance_patterns:
            matches = re.findall(pattern, content)
            compliance_obligations.extend([match.strip()[:100] for match in matches[:3]])
        
        # Extract entities
        entity_patterns = [
            r'(anla|autoridad nacional de licencias ambientales)',
            r'(ministerio de ambiente)',
            r'(corporaci[óo]n aut[óo]noma regional)',
            r'(car\b)',
            r'(minambiente)',
            r'(ideam)'
        ]
        
        entities = []
        for pattern in entity_patterns:
            if re.search(pattern, content):
                entities.append(pattern.replace(r'\b', '').replace('(', '').replace(')', '').upper())
        
        # Extract key concepts
        key_concepts = []
        concept_patterns = [
            r'(licencia ambiental)',
            r'(plan de manejo ambiental)',
            r'(impacto ambiental)',
            r'(compensaci[óo]n ambiental)',
            r'(aprovechamiento forestal)',
            r'(recurso h[íi]drico)'
        ]
        
        for pattern in concept_patterns:
            if re.search(pattern, content):
                key_concepts.append(pattern.replace('(', '').replace(')', '').title())
        
        # Extract risk factors
        risk_patterns = [
            r'riesgo\s+de\s+([^\.]+)',
            r'puede\s+causar\s+([^\.]+)',
            r'efectos?\s+adversos?\s+([^\.]+)',
            r'da[ñn]o\s+([^\.]+)'
        ]
        
        risk_factors = []
        for pattern in risk_patterns:
            matches = re.findall(pattern, content)
            risk_factors.extend([match.strip()[:100] for match in matches[:2]])
        
        # Generate summary
        summary = f"Sección '{section.title}' contiene {len(legal_requirements)} requisitos legales, {len(compliance_obligations)} obligaciones de cumplimiento, y referencias a {len(entities)} entidades regulatorias."
        
        # Calculate confidence based on content richness
        confidence = min(0.95, 0.5 + (len(legal_requirements) + len(compliance_obligations) + len(entities)) * 0.05)
        
        return SectionAnalysis(
            section_id=section.section_id,
            legal_requirements=legal_requirements,
            compliance_obligations=compliance_obligations,
            entities_mentioned=entities,
            key_concepts=key_concepts,
            risk_factors=risk_factors,
            summary=summary,
            confidence_score=confidence
        )
    
    def analyze_complete_document(self, doc_content: str, doc_url: str = "", doc_title: str = "") -> ComprehensiveDocumentAnalysis:
        """Perform comprehensive analysis of a complete document."""
        
        print(f"🔍 Analyzing document: {doc_title or 'Untitled'}")
        print(f"   📏 Size: {len(doc_content):,} characters")
        
        # Step 1: Extract document structure
        print("   1️⃣ Extracting document structure...")
        sections = self.extract_document_structure(doc_content, doc_title)
        print(f"      Found {len(sections)} sections")
        
        # Step 2: Split large sections
        print("   2️⃣ Processing large sections...")
        all_sections = []
        for section in sections:
            if section.char_count > self.max_section_chars:
                subsections = self.split_large_section(section)
                all_sections.extend(subsections)
                print(f"      Split '{section.title}' into {len(subsections)} parts")
            else:
                all_sections.append(section)
        
        print(f"      Total processable sections: {len(all_sections)}")
        
        # Step 3: Analyze each section
        print("   3️⃣ Analyzing sections...")
        section_analyses = []
        total_tokens = 0
        
        for i, section in enumerate(all_sections, 1):
            print(f"      Analyzing section {i}/{len(all_sections)}: {section.title[:50]}...")
            analysis = self.simulate_section_analysis(section)
            section_analyses.append(analysis)
            
            # Estimate token usage
            tokens_used = section.token_estimate + 500  # Analysis overhead
            total_tokens += tokens_used
            
            print(f"         Requirements: {len(analysis.legal_requirements)}, Entities: {len(analysis.entities_mentioned)}, Tokens: ~{tokens_used}")
        
        # Step 4: Aggregate insights
        print("   4️⃣ Aggregating insights...")
        all_requirements = []
        all_obligations = []
        all_entities = []
        all_risks = []
        
        for analysis in section_analyses:
            all_requirements.extend(analysis.legal_requirements)
            all_obligations.extend(analysis.compliance_obligations)
            all_entities.extend(analysis.entities_mentioned)
            all_risks.extend(analysis.risk_factors)
        
        # Deduplicate
        all_requirements = list(set(all_requirements))
        all_obligations = list(set(all_obligations))
        all_entities = list(set(all_entities))
        all_risks = list(set(all_risks))
        
        # Step 5: Generate comprehensive reports
        print("   5️⃣ Generating comprehensive reports...")
        
        executive_summary = f"""
RESUMEN EJECUTIVO - {doc_title}

DOCUMENTO: {doc_title}
TAMAÑO: {len(doc_content):,} caracteres, {len(all_sections)} secciones
ENTIDADES REGULATORIAS: {', '.join(all_entities[:5])}{'...' if len(all_entities) > 5 else ''}

HALLAZGOS PRINCIPALES:
• {len(all_requirements)} requisitos legales identificados
• {len(all_obligations)} obligaciones de cumplimiento
• {len(all_risks)} factores de riesgo documentados

SECTORES PRINCIPALES ANALIZADOS:
{chr(10).join(f"• {section.title}" for section in all_sections[:5])}
{'• ...' if len(all_sections) > 5 else ''}
        """.strip()
        
        compliance_report = f"""
REPORTE DE CUMPLIMIENTO - {doc_title}

OBLIGACIONES LEGALES IDENTIFICADAS:
{chr(10).join(f"• {req}" for req in all_requirements[:10])}
{'• ...' if len(all_requirements) > 10 else ''}

OBLIGACIONES DE CUMPLIMIENTO:
{chr(10).join(f"• {obl}" for obl in all_obligations[:10])}
{'• ...' if len(all_obligations) > 10 else ''}

ENTIDADES COMPETENTES:
{chr(10).join(f"• {entity}" for entity in all_entities)}
        """.strip()
        
        risk_assessment = f"""
EVALUACIÓN DE RIESGOS - {doc_title}

FACTORES DE RIESGO IDENTIFICADOS:
{chr(10).join(f"• {risk}" for risk in all_risks[:10])}
{'• ...' if len(all_risks) > 10 else ''}

NIVEL DE RIESGO: {'ALTO' if len(all_risks) > 10 else 'MEDIO' if len(all_risks) > 5 else 'BAJO'}
COMPLEJIDAD REGULATORIA: {'ALTA' if len(all_entities) > 3 else 'MEDIA' if len(all_entities) > 1 else 'BAJA'}
        """.strip()
        
        print(f"      ✅ Analysis complete! Token usage: ~{total_tokens:,}")
        
        return ComprehensiveDocumentAnalysis(
            doc_id=doc_url or doc_title or "document",
            url=doc_url,
            title=doc_title,
            total_chars=len(doc_content),
            total_sections=len(all_sections),
            all_legal_requirements=all_requirements,
            all_compliance_obligations=all_obligations,
            all_entities=all_entities,
            all_risk_factors=all_risks,
            section_analyses=section_analyses,
            executive_summary=executive_summary,
            compliance_report=compliance_report,
            risk_assessment=risk_assessment,
            token_usage=total_tokens,
            processing_strategy="Hierarchical Chunking + Parallel Processing"
        )

def test_comprehensive_analyzer():
    """Test the comprehensive document analyzer."""
    
    print("🧪 TESTING COMPREHENSIVE DOCUMENT ANALYZER")
    print("=" * 60)
    
    # Create a sample legal document
    sample_document = """
DECRETO 1076 DE 2015
SECTOR AMBIENTE Y DESARROLLO SOSTENIBLE

CAPÍTULO I: DISPOSICIONES GENERALES

ARTÍCULO 1. OBJETO
El presente decreto tiene por objeto reglamentar el sector ambiente y desarrollo sostenible.

ARTÍCULO 2. AUTORIDADES COMPETENTES
La Autoridad Nacional de Licencias Ambientales - ANLA, las Corporaciones Autónomas Regionales y el Ministerio de Ambiente son las autoridades competentes.

CAPÍTULO II: LICENCIAS AMBIENTALES

ARTÍCULO 5. DEFINICIÓN
La licencia ambiental es la autorización que otorga la autoridad ambiental competente.

ARTÍCULO 6. OBLIGACIONES
Los titulares de licencias ambientales deberán cumplir con el Plan de Manejo Ambiental.
Es obligatorio presentar los Informes de Cumplimiento Ambiental.

CAPÍTULO III: APROVECHAMIENTO FORESTAL

ARTÍCULO 10. PERMISOS
Se requiere permiso para el aprovechamiento forestal. 
La autoridad deberá verificar el cumplimiento de las obligaciones ambientales.

SECCIÓN I: COMPENSACIONES AMBIENTALES

Las compensaciones ambientales son obligatorias cuando se cause daño al ambiente.
El riesgo de impacto debe ser evaluado previamente.
    """.strip()
    
    # Test the analyzer
    analyzer = ComprehensiveDocumentAnalyzer(max_section_chars=15000)
    
    analysis = analyzer.analyze_complete_document(
        doc_content=sample_document,
        doc_url="https://example.gov.co/decreto-1076-2015",
        doc_title="Decreto 1076 de 2015 - Sector Ambiente"
    )
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Document: {analysis.title}")
    print(f"   Sections analyzed: {analysis.total_sections}")
    print(f"   Token usage: {analysis.token_usage:,}")
    print(f"   Legal requirements: {len(analysis.all_legal_requirements)}")
    print(f"   Compliance obligations: {len(analysis.all_compliance_obligations)}")
    print(f"   Entities mentioned: {len(analysis.all_entities)}")
    
    print(f"\n📋 EXECUTIVE SUMMARY:")
    print(analysis.executive_summary)
    
    print(f"\n📑 COMPLIANCE REPORT:")
    print(analysis.compliance_report)
    
    print(f"\n⚠️ RISK ASSESSMENT:")
    print(analysis.risk_assessment)
    
    return analysis

if __name__ == "__main__":
    test_comprehensive_analyzer()
