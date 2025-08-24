#!/usr/bin/env python3
"""
Comprehensive Content Optimization Strategy for EIA-ADK Legal Knowledge Base.

This module implements a multi-tier approach to solve content size and rate limiting issues:
1. Smart Content Filtering & Prioritization
2. Progressive Analysis with Adaptive Scaling  
3. Intelligent Caching Layer
4. Rate Limit Protection & Monitoring
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from copy import deepcopy
import re

@dataclass
class ContentMetrics:
    """Metrics for tracking content processing efficiency."""
    total_docs_found: int = 0
    docs_kept: int = 0
    docs_truncated: int = 0
    docs_skipped: int = 0
    total_chars_before: int = 0
    total_chars_after: int = 0
    estimated_tokens: int = 0
    processing_time_ms: int = 0
    cache_hits: int = 0
    api_calls_made: int = 0

@dataclass
class DocumentScore:
    """Scoring system for document relevance and priority."""
    relevance_score: float = 0.0  # 0-1 based on keyword matches
    size_efficiency: float = 0.0  # 0-1 based on content/token ratio
    authority_score: float = 0.0  # 0-1 based on source authority
    recency_score: float = 0.0    # 0-1 based on document age
    final_score: float = 0.0      # Weighted composite score

class ContentOptimizer:
    """
    Intelligent content optimization system that dynamically adjusts processing
    based on context limits, relevance scoring, and performance requirements.
    """
    
    def __init__(self, 
                 cache_dir: Optional[Path] = None,
                 max_tokens_target: int = 50000,
                 enable_caching: bool = True):
        self.cache_dir = cache_dir or Path("cache/geo_kb")
        self.max_tokens_target = max_tokens_target
        self.enable_caching = enable_caching
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics = ContentMetrics()
        self.rate_limit_tracker = {
            "calls_per_minute": [],
            "last_call_time": 0,
            "backoff_multiplier": 1.0
        }
    
    def optimize_geo_kb_search(self, 
                             state_json: Dict[str, Any],
                             analysis_mode: str = "adaptive") -> Dict[str, Any]:
        """
        Main entry point for optimized geo_kb_search with intelligent content management.
        
        Analysis Modes:
        - "fast": Minimal content, quick results (~15K tokens)
        - "balanced": Moderate content with smart filtering (~50K tokens)  
        - "comprehensive": Maximum relevant content (~100K tokens)
        - "adaptive": Automatically choose mode based on context
        """
        start_time = time.time()
        
        print(f"🧠 Starting Intelligent Content Optimization")
        print(f"   Mode: {analysis_mode}")
        print(f"   Target tokens: {self.max_tokens_target:,}")
        
        # 1. Extract and score keywords
        keywords = self._extract_keywords_with_scoring(state_json)
        
        # 2. Determine optimal analysis mode
        if analysis_mode == "adaptive":
            analysis_mode = self._determine_optimal_mode(keywords, state_json)
            print(f"   Adaptive mode selected: {analysis_mode}")
        
        # 3. Set mode-specific parameters
        mode_config = self._get_mode_configuration(analysis_mode)
        
        # 4. Check cache for previously processed results
        cache_key = self._generate_cache_key(keywords, mode_config)
        cached_result = self._check_cache(cache_key) if self.enable_caching else None
        
        if cached_result:
            print(f"   ✅ Cache hit! Using cached results")
            self.metrics.cache_hits += 1
            return self._merge_cached_with_state(cached_result, state_json)
        
        # 5. Execute intelligent search with progressive filtering
        search_results = self._execute_intelligent_search(keywords, mode_config)
        
        # 6. Apply multi-tier content processing
        processed_content = self._apply_content_processing(search_results, mode_config)
        
        # 7. Validate token limits and adjust if needed
        final_content = self._validate_and_adjust_content(processed_content, mode_config)
        
        # 8. Cache results for future use
        if self.enable_caching:
            self._cache_results(cache_key, final_content)
        
        # 9. Update metrics and tracking
        self._update_metrics(start_time)
        
        # 10. Merge with original state
        result = self._merge_with_state(final_content, state_json)
        
        print(f"   🎯 Optimization complete:")
        print(f"      Documents: {self.metrics.docs_kept}")
        print(f"      Tokens: {self.metrics.estimated_tokens:,}")
        print(f"      Processing time: {self.metrics.processing_time_ms}ms")
        
        return result
    
    def _extract_keywords_with_scoring(self, state_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract keywords with relevance scoring for prioritization."""
        keywords = []
        
        # Extract from various state sources with different weights
        sources = [
            # High priority: Direct legal mappings
            {
                "path": ["legal", "geo2neo", "alias_input"],
                "weight": 1.0,
                "source": "legal_alias"
            },
            # Medium priority: Geo categories  
            {
                "path": ["geo", "structured_summary", "rows"],
                "weight": 0.8,
                "field": "categoria",
                "source": "geo_category"
            },
            # Lower priority: Geo types
            {
                "path": ["geo", "structured_summary", "rows"], 
                "weight": 0.6,
                "field": "tipo",
                "source": "geo_type"
            }
        ]
        
        for source_config in sources:
            extracted = self._extract_from_path(state_json, source_config)
            keywords.extend(extracted)
        
        # Deduplicate and score
        unique_keywords = self._deduplicate_and_score(keywords)
        
        # Sort by score (highest first)
        unique_keywords.sort(key=lambda x: x["score"], reverse=True)
        
        print(f"   📝 Keywords extracted: {len(unique_keywords)}")
        for i, kw in enumerate(unique_keywords[:5]):
            print(f"      {i+1}. {kw['keyword']} (score: {kw['score']:.2f})")
        
        return unique_keywords
    
    def _determine_optimal_mode(self, keywords: List[Dict[str, Any]], state_json: Dict[str, Any]) -> str:
        """Automatically determine the best analysis mode based on context."""
        # Factors to consider:
        num_keywords = len(keywords)
        has_geo_data = bool(state_json.get("geo", {}).get("structured_summary"))
        has_legal_data = bool(state_json.get("legal", {}).get("geo2neo"))
        
        # Simple heuristic for mode selection
        if num_keywords <= 3 and not has_geo_data:
            return "fast"
        elif num_keywords <= 8 and (has_geo_data or has_legal_data):
            return "balanced"
        else:
            return "comprehensive"
    
    def _get_mode_configuration(self, mode: str) -> Dict[str, Any]:
        """Get configuration parameters for each analysis mode."""
        configs = {
            "fast": {
                "max_keywords": 6,
                "docs_per_keyword": 1,
                "max_chars_per_doc": 8000,
                "skip_docs_larger_than": 200000,
                "target_tokens": 15000,
                "enable_summarization": False
            },
            "balanced": {
                "max_keywords": 10,
                "docs_per_keyword": 2,
                "max_chars_per_doc": 12000,
                "skip_docs_larger_than": 400000,
                "target_tokens": 50000,
                "enable_summarization": True
            },
            "comprehensive": {
                "max_keywords": 15,
                "docs_per_keyword": 3,
                "max_chars_per_doc": 20000,
                "skip_docs_larger_than": 800000,
                "target_tokens": 100000,
                "enable_summarization": True
            }
        }
        return configs.get(mode, configs["balanced"])
    
    def _execute_intelligent_search(self, keywords: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute search with intelligent keyword prioritization."""
        results = []
        
        # Limit to top keywords based on mode
        top_keywords = keywords[:config["max_keywords"]]
        
        for kw_data in top_keywords:
            keyword = kw_data["keyword"]
            
            # Apply rate limiting protection
            self._apply_rate_limit_protection()
            
            # Simulate MCP search (replace with actual _async_call_mcp_server call)
            search_result = self._simulate_mcp_search(keyword, config["docs_per_keyword"])
            
            if search_result.get("rows"):
                for doc in search_result["rows"]:
                    # Add keyword context and scoring
                    doc["_source_keyword"] = keyword
                    doc["_keyword_score"] = kw_data["score"]
                    doc["_document_score"] = self._score_document(doc, keyword)
                    results.append(doc)
            
            self.metrics.api_calls_made += 1
        
        return results
    
    def _apply_content_processing(self, results: List[Dict[str, Any]], config: Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply multi-tier content processing with intelligent filtering."""
        processed = []
        
        # Sort by document score (highest first)
        results.sort(key=lambda x: x.get("_document_score", {}).get("final_score", 0), reverse=True)
        
        current_tokens = 0
        target_tokens = config["target_tokens"]
        
        for doc in results:
            content = doc.get("content_md", "")
            content_length = len(content)
            
            self.metrics.total_docs_found += 1
            self.metrics.total_chars_before += content_length
            
            # Skip if too large (configurable threshold)
            if content_length > config["skip_docs_larger_than"]:
                self.metrics.docs_skipped += 1
                continue
            
            # Estimate tokens for this document
            doc_tokens = min(content_length // 4, config["max_chars_per_doc"] // 4)
            
            # Check if adding this doc would exceed target
            if current_tokens + doc_tokens > target_tokens:
                # Apply intelligent truncation or summarization
                if config.get("enable_summarization", False):
                    doc = self._apply_intelligent_summarization(doc, target_tokens - current_tokens)
                    doc_tokens = len(doc.get("content_md", "")) // 4
                else:
                    # Simple truncation
                    max_chars = (target_tokens - current_tokens) * 4
                    if max_chars > 1000:  # Only if we have meaningful space left
                        doc = self._apply_truncation(doc, max_chars)
                        doc_tokens = max_chars // 4
                    else:
                        break  # No more space
            
            # Apply standard truncation if needed
            if content_length > config["max_chars_per_doc"]:
                doc = self._apply_truncation(doc, config["max_chars_per_doc"])
                self.metrics.docs_truncated += 1
            else:
                self.metrics.docs_kept += 1
            
            processed.append(doc)
            current_tokens += doc_tokens
            self.metrics.total_chars_after += len(doc.get("content_md", ""))
            
            # Stop if we've reached our target
            if current_tokens >= target_tokens:
                break
        
        self.metrics.estimated_tokens = current_tokens
        return processed
    
    def _score_document(self, doc: Dict[str, Any], keyword: str) -> DocumentScore:
        """Score document for relevance and priority."""
        content = doc.get("content_md", "")
        title = doc.get("title", "")
        url = doc.get("url", "")
        
        score = DocumentScore()
        
        # Relevance scoring (keyword matches)
        keyword_lower = keyword.lower()
        title_matches = title.lower().count(keyword_lower)
        content_matches = content.lower().count(keyword_lower)
        score.relevance_score = min(1.0, (title_matches * 2 + content_matches) / max(len(content) / 1000, 1))
        
        # Size efficiency (content value per token)
        content_length = len(content)
        if content_length > 0:
            token_estimate = content_length // 4
            # Prefer documents with high information density
            score.size_efficiency = min(1.0, 10000 / max(token_estimate, 1000))
        
        # Authority scoring (government/official sources)
        authority_indicators = [
            "gov.co", "minambiente", "anla", "parquesnacionales",
            "resolución", "decreto", "ley", "normativa"
        ]
        authority_matches = sum(1 for indicator in authority_indicators if indicator in url.lower() or indicator in title.lower())
        score.authority_score = min(1.0, authority_matches / 3)
        
        # Recency score (placeholder - would need actual dates)
        score.recency_score = 0.5  # Default neutral score
        
        # Weighted final score
        weights = {
            "relevance": 0.4,
            "authority": 0.3,
            "size_efficiency": 0.2,
            "recency": 0.1
        }
        
        score.final_score = (
            score.relevance_score * weights["relevance"] +
            score.authority_score * weights["authority"] +
            score.size_efficiency * weights["size_efficiency"] +
            score.recency_score * weights["recency"]
        )
        
        return score
    
    def _apply_rate_limit_protection(self):
        """Implement intelligent rate limiting to prevent API throttling."""
        current_time = time.time()
        
        # Track calls per minute
        minute_ago = current_time - 60
        self.rate_limit_tracker["calls_per_minute"] = [
            t for t in self.rate_limit_tracker["calls_per_minute"] if t > minute_ago
        ]
        
        # Apply backoff if needed
        calls_this_minute = len(self.rate_limit_tracker["calls_per_minute"])
        
        if calls_this_minute > 50:  # Adjust based on your API limits
            backoff_time = self.rate_limit_tracker["backoff_multiplier"] * 2
            print(f"   ⏱️ Rate limit protection: waiting {backoff_time:.1f}s")
            time.sleep(backoff_time)
            self.rate_limit_tracker["backoff_multiplier"] *= 1.5
        else:
            self.rate_limit_tracker["backoff_multiplier"] = max(1.0, self.rate_limit_tracker["backoff_multiplier"] * 0.9)
        
        self.rate_limit_tracker["calls_per_minute"].append(current_time)
        self.rate_limit_tracker["last_call_time"] = current_time
    
    # Helper methods (simplified implementations)
    def _extract_from_path(self, data: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract keywords from nested data structure."""
        result = []
        try:
            current = data
            for key in config["path"]:
                current = current.get(key, {})
            
            if isinstance(current, list):
                if "field" in config:
                    # Extract from list items
                    for item in current:
                        if isinstance(item, dict) and item.get(config["field"]):
                            result.append({
                                "keyword": str(item[config["field"]]),
                                "weight": config["weight"],
                                "source": config["source"]
                            })
                else:
                    # Direct list of values
                    for item in current:
                        if item:
                            result.append({
                                "keyword": str(item),
                                "weight": config["weight"],
                                "source": config["source"]
                            })
        except Exception:
            pass
        
        return result
    
    def _deduplicate_and_score(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and calculate final scores."""
        seen = {}
        
        for kw_data in keywords:
            key = kw_data["keyword"].lower().strip()
            if key and key not in seen:
                seen[key] = {
                    "keyword": kw_data["keyword"],
                    "score": kw_data["weight"],
                    "sources": [kw_data["source"]]
                }
            elif key:
                # Boost score for keywords from multiple sources
                seen[key]["score"] = max(seen[key]["score"], kw_data["weight"])
                seen[key]["sources"].append(kw_data["source"])
        
        return list(seen.values())
    
    def _simulate_mcp_search(self, keyword: str, limit: int) -> Dict[str, Any]:
        """Simulate MCP search (replace with actual implementation)."""
        # This would be replaced with actual _async_call_mcp_server call
        return {
            "rows": [
                {
                    "url": f"https://example.gov.co/doc_{keyword}_{i}",
                    "title": f"Documento {keyword} {i}",
                    "content_md": f"Contenido relacionado con {keyword} " * (1000 + i * 500)
                }
                for i in range(limit)
            ]
        }
    
    def _apply_truncation(self, doc: Dict[str, Any], max_chars: int) -> Dict[str, Any]:
        """Apply intelligent content truncation."""
        content = doc.get("content_md", "")
        if len(content) > max_chars:
            doc = doc.copy()
            doc["content_md"] = content[:max_chars] + "\n\n[Content truncated...]"
            doc["_original_length"] = len(content)
            doc["_truncated"] = True
        return doc
    
    def _apply_intelligent_summarization(self, doc: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Apply AI-powered summarization (placeholder for future enhancement)."""
        # This would integrate with an LLM for intelligent summarization
        max_chars = max_tokens * 4
        return self._apply_truncation(doc, max_chars)
    
    def _generate_cache_key(self, keywords: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Generate cache key for results."""
        key_data = {
            "keywords": [kw["keyword"] for kw in keywords[:10]],  # Top 10 for cache key
            "config": {k: v for k, v in config.items() if k in ["max_keywords", "docs_per_keyword", "max_chars_per_doc"]}
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if cached results exist."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 3600:  # 1 hour cache
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    
    def _cache_results(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cache results for future use."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _merge_cached_with_state(self, cached_result: List[Dict[str, Any]], state_json: Dict[str, Any]) -> Dict[str, Any]:
        """Merge cached results with current state."""
        current = deepcopy(state_json)
        kb = current.setdefault("legal", {}).setdefault("kb", {})
        
        kb["scraped_pages"] = {
            "count": len(cached_result),
            "rows": cached_result,
            "_metadata": {
                "cached": True,
                "cache_timestamp": time.time()
            }
        }
        
        return current
    
    def _validate_and_adjust_content(self, content: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Final validation and adjustment of content to meet token limits."""
        total_tokens = sum(len(doc.get("content_md", "")) // 4 for doc in content)
        target_tokens = config["target_tokens"]
        
        if total_tokens <= target_tokens:
            return content
        
        # Need to reduce content
        print(f"   ⚡ Adjusting content: {total_tokens:,} → {target_tokens:,} tokens")
        
        # Remove lowest-scoring documents first
        content.sort(key=lambda x: x.get("_document_score", {}).get("final_score", 0), reverse=True)
        
        adjusted = []
        current_tokens = 0
        
        for doc in content:
            doc_tokens = len(doc.get("content_md", "")) // 4
            if current_tokens + doc_tokens <= target_tokens:
                adjusted.append(doc)
                current_tokens += doc_tokens
            else:
                # Try to fit a truncated version
                remaining_tokens = target_tokens - current_tokens
                if remaining_tokens > 250:  # Minimum meaningful content
                    doc = self._apply_truncation(doc, remaining_tokens * 4)
                    adjusted.append(doc)
                break
        
        return adjusted
    
    def _merge_with_state(self, content: List[Dict[str, Any]], state_json: Dict[str, Any]) -> Dict[str, Any]:
        """Merge processed content with original state."""
        current = deepcopy(state_json)
        kb = current.setdefault("legal", {}).setdefault("kb", {})
        
        kb["scraped_pages"] = {
            "count": len(content),
            "rows": content,
            "_metadata": asdict(self.metrics)
        }
        
        return current
    
    def _update_metrics(self, start_time: float):
        """Update performance metrics."""
        self.metrics.processing_time_ms = int((time.time() - start_time) * 1000)

# Factory function for easy integration
def create_optimized_geo_kb_search():
    """Create an optimized geo_kb_search function using the ContentOptimizer."""
    optimizer = ContentOptimizer(
        max_tokens_target=50000,  # Adjust based on your LLM limits
        enable_caching=True
    )
    
    def optimized_geo_kb_search(state_json: Dict[str, Any], 
                               analysis_mode: str = "adaptive") -> Dict[str, Any]:
        """Drop-in replacement for geo_kb_search_from_state with intelligent optimization."""
        return optimizer.optimize_geo_kb_search(state_json, analysis_mode)
    
    return optimized_geo_kb_search

if __name__ == "__main__":
    # Test the optimization strategy
    print("🧪 Testing Content Optimization Strategy")
    
    # Sample state data
    test_state = {
        "legal": {
            "geo2neo": {
                "alias_input": ["Biótico", "Compensación", "Gestión de Riesgo", "Hidrogeología", "Hidrología", "Suelos"]
            }
        },
        "geo": {
            "structured_summary": {
                "rows": [
                    {"categoria": "SOILS", "tipo": "Suelos"},
                    {"categoria": "HYDROLOGY", "tipo": "Hidrología"}
                ]
            }
        }
    }
    
    # Test different modes
    optimizer = ContentOptimizer(max_tokens_target=30000)
    
    for mode in ["fast", "balanced", "comprehensive", "adaptive"]:
        print(f"\n🧪 Testing {mode} mode:")
        result = optimizer.optimize_geo_kb_search(test_state, mode)
        
        metadata = result["legal"]["kb"]["scraped_pages"]["_metadata"]
        print(f"   Tokens: {metadata.estimated_tokens:,}")
        print(f"   Docs: {metadata.docs_kept}")
        print(f"   Time: {metadata.processing_time_ms}ms")
