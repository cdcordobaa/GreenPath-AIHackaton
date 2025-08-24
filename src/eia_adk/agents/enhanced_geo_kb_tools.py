#!/usr/bin/env python3
"""
Enhanced geo_kb_tools with integrated optimization strategy.
This module provides drop-in replacements for the geo_kb functions with intelligent content management.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy
import asyncio
import sys

# Import the existing tools structure
from src.eia_adk.agents.tools import _run_coro_blocking, _async_call_mcp_server


class IntelligentGeoKBSearcher:
    """
    Enhanced version of geo_kb_search_from_state with intelligent content optimization.
    This is a drop-in replacement that maintains compatibility while adding optimization.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("cache/geo_kb")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics = {
            "total_calls": 0,
            "cache_hits": 0,
            "total_tokens_saved": 0,
            "average_processing_time": 0
        }
        
        # Rate limiting protection
        self.rate_limiter = {
            "last_call_time": 0,
            "calls_in_window": [],
            "backoff_factor": 1.0
        }
    
    def enhanced_geo_kb_search_from_state(
        self,
        state_json: Dict[str, Any], 
        per_keyword_limit: int = 2,
        max_keywords: int = 12,
        max_chars_per_doc: int = 15000,
        skip_docs_larger_than: int = 500000,
        optimization_mode: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Enhanced geo_kb_search with intelligent content optimization.
        
        Optimization Modes:
        - "fast": Quick results, minimal content (~15K tokens)
        - "balanced": Good balance of speed and content (~50K tokens) 
        - "comprehensive": Maximum relevant content (~100K tokens)
        - "adaptive": Automatically choose based on context
        """
        start_time = time.time()
        self.metrics["total_calls"] += 1
        
        print(f"🧠 Enhanced geo_kb_search - Mode: {optimization_mode}")
        
        # Step 1: Apply mode-specific configuration
        config = self._get_optimization_config(optimization_mode)
        
        # Override defaults with mode-specific values
        per_keyword_limit = config.get("per_keyword_limit", per_keyword_limit)
        max_keywords = config.get("max_keywords", max_keywords)
        max_chars_per_doc = config.get("max_chars_per_doc", max_chars_per_doc)
        skip_docs_larger_than = config.get("skip_docs_larger_than", skip_docs_larger_than)
        
        print(f"   Config: {per_keyword_limit} docs/keyword, {max_chars_per_doc:,} chars/doc")
        
        # Step 2: Extract and prioritize keywords
        keywords = self._extract_keywords_intelligently(state_json, max_keywords)
        
        # Step 3: Check cache if available
        cache_key = self._generate_cache_key(keywords, config)
        cached_result = self._check_cache(cache_key)
        
        if cached_result:
            print(f"   ✅ Cache hit! Using cached results")
            self.metrics["cache_hits"] += 1
            return self._merge_cached_with_state(cached_result, state_json)
        
        # Step 4: Execute search with rate limiting protection
        search_results = self._execute_protected_search(keywords, per_keyword_limit, config)
        
        # Step 5: Apply intelligent content processing
        processed_docs = self._process_documents_intelligently(
            search_results, 
            max_chars_per_doc, 
            skip_docs_larger_than,
            config
        )
        
        # Step 6: Final validation and optimization
        final_docs = self._validate_token_limits(processed_docs, config)
        
        # Step 7: Cache results
        self._cache_results(cache_key, final_docs)
        
        # Step 8: Create final state structure
        result = self._create_final_state(state_json, keywords, final_docs, config)
        
        # Step 9: Update metrics
        processing_time = time.time() - start_time
        self._update_metrics(processing_time)
        
        # Log final statistics
        total_chars = sum(len(doc.get("content_md", "")) for doc in final_docs)
        estimated_tokens = total_chars // 4
        
        print(f"   🎯 Results: {len(final_docs)} docs, {estimated_tokens:,} tokens, {processing_time:.1f}s")
        
        return result
    
    def _get_optimization_config(self, mode: str) -> Dict[str, Any]:
        """Get configuration for each optimization mode."""
        configs = {
            "fast": {
                "per_keyword_limit": 1,
                "max_keywords": 6,
                "max_chars_per_doc": 8000,
                "skip_docs_larger_than": 200000,
                "target_token_limit": 15000,
                "enable_smart_ranking": True,
                "enable_content_analysis": False
            },
            "balanced": {
                "per_keyword_limit": 2,
                "max_keywords": 10,
                "max_chars_per_doc": 15000,
                "skip_docs_larger_than": 500000,
                "target_token_limit": 50000,
                "enable_smart_ranking": True,
                "enable_content_analysis": True
            },
            "comprehensive": {
                "per_keyword_limit": 3,
                "max_keywords": 15,
                "max_chars_per_doc": 25000,
                "skip_docs_larger_than": 1000000,
                "target_token_limit": 100000,
                "enable_smart_ranking": True,
                "enable_content_analysis": True
            },
            "adaptive": {
                # Will be determined dynamically
                "enable_smart_ranking": True,
                "enable_content_analysis": True
            }
        }
        
        if mode == "adaptive":
            # Simple adaptive logic - choose based on available keywords
            return configs["balanced"]  # Default to balanced for now
        
        return configs.get(mode, configs["balanced"])
    
    def _extract_keywords_intelligently(self, state_json: Dict[str, Any], max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords with scoring and prioritization."""
        current = deepcopy(state_json or {})
        keyword_sources = []
        
        # Source 1: Legal aliases (highest priority)
        try:
            aliases = list(((current.get("legal") or {}).get("geo2neo") or {}).get("alias_input") or [])
            for alias in aliases:
                if alias:
                    keyword_sources.append({
                        "keyword": str(alias),
                        "score": 1.0,
                        "source": "legal_alias",
                        "priority": 1
                    })
        except Exception:
            pass
        
        # Source 2: Geo2neo mapping results (high priority)
        try:
            results = ((current.get("legal") or {}).get("geo2neo") or {}).get("alias_mapping", {}).get("results") or []
            for item in results:
                cat = item.get("category")
                if cat:
                    keyword_sources.append({
                        "keyword": str(cat),
                        "score": 0.9,
                        "source": "mapping_category",
                        "priority": 2
                    })
                    
                for inst in item.get("instrumentsAndPermits", []) or []:
                    name = inst.get("instrumentName")
                    if name:
                        keyword_sources.append({
                            "keyword": str(name),
                            "score": 0.8,
                            "source": "instrument_name",
                            "priority": 3
                        })
        except Exception:
            pass
        
        # Source 3: Structured summary (medium priority)
        try:
            rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
            for r in rows:
                if r.get("categoria"):
                    keyword_sources.append({
                        "keyword": str(r.get("categoria")),
                        "score": 0.7,
                        "source": "geo_category",
                        "priority": 4
                    })
                if r.get("tipo"):
                    keyword_sources.append({
                        "keyword": str(r.get("tipo")),
                        "score": 0.6,
                        "source": "geo_type",
                        "priority": 5
                    })
        except Exception:
            pass
        
        # Deduplicate and prioritize
        unique_keywords = self._deduplicate_keywords(keyword_sources)
        
        # Sort by score (highest first) and limit
        unique_keywords.sort(key=lambda x: (x["score"], -x["priority"]), reverse=True)
        limited_keywords = unique_keywords[:max_keywords]
        
        print(f"   📝 Keywords: {len(limited_keywords)} selected from {len(keyword_sources)} candidates")
        for i, kw in enumerate(limited_keywords[:5]):
            print(f"      {i+1}. {kw['keyword']} (score: {kw['score']:.1f}, source: {kw['source']})")
        
        return limited_keywords
    
    def _deduplicate_keywords(self, keyword_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate keywords and combine scores."""
        seen = {}
        
        for kw_data in keyword_sources:
            key = kw_data["keyword"].lower().strip()
            if key and len(key) > 2:  # Filter out very short keywords
                if key not in seen:
                    seen[key] = kw_data.copy()
                else:
                    # Boost score for keywords from multiple sources
                    seen[key]["score"] = max(seen[key]["score"], kw_data["score"]) + 0.1
                    seen[key]["priority"] = min(seen[key]["priority"], kw_data["priority"])
        
        return list(seen.values())
    
    def _execute_protected_search(self, keywords: List[Dict[str, Any]], per_keyword_limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute MCP search with rate limiting protection."""
        all_results = []
        
        for kw_data in keywords:
            keyword = kw_data["keyword"]
            
            # Apply rate limiting
            self._apply_rate_limiting()
            
            try:
                print(f"   🔍 Searching: '{keyword}' (limit: {per_keyword_limit})")
                
                args = {"text_contains": keyword, "limit": per_keyword_limit}
                result = _run_coro_blocking(_async_call_mcp_server("geo-fetch-mcp", "search_scraped_pages", args))
                
                if result.get("rows"):
                    for doc in result["rows"]:
                        # Add metadata for later processing
                        doc["_source_keyword"] = keyword
                        doc["_keyword_score"] = kw_data["score"]
                        doc["_search_priority"] = kw_data["priority"]
                        all_results.append(doc)
                        
                    print(f"      ✅ Found {len(result['rows'])} documents")
                else:
                    print(f"      ⚠️ No results for '{keyword}'")
                    
            except Exception as exc:
                print(f"      ❌ Search failed for '{keyword}': {exc}")
                continue
        
        print(f"   📊 Total documents found: {len(all_results)}")
        return all_results
    
    def _apply_rate_limiting(self):
        """Apply intelligent rate limiting to prevent API throttling."""
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        minute_ago = current_time - 60
        self.rate_limiter["calls_in_window"] = [
            t for t in self.rate_limiter["calls_in_window"] if t > minute_ago
        ]
        
        # Check if we need to apply backoff
        calls_this_minute = len(self.rate_limiter["calls_in_window"])
        
        if calls_this_minute > 30:  # Conservative limit
            backoff_time = self.rate_limiter["backoff_factor"]
            print(f"   ⏱️ Rate limiting: waiting {backoff_time:.1f}s")
            time.sleep(backoff_time)
            self.rate_limiter["backoff_factor"] = min(10.0, self.rate_limiter["backoff_factor"] * 1.5)
        else:
            # Gradually reduce backoff when not hitting limits
            self.rate_limiter["backoff_factor"] = max(1.0, self.rate_limiter["backoff_factor"] * 0.9)
        
        # Record this call
        self.rate_limiter["calls_in_window"].append(current_time)
        self.rate_limiter["last_call_time"] = current_time
    
    def _process_documents_intelligently(self, docs: List[Dict[str, Any]], max_chars_per_doc: int, skip_docs_larger_than: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process documents with intelligent filtering and ranking."""
        if not docs:
            return []
        
        # Step 1: Score and rank documents
        scored_docs = []
        for doc in docs:
            score = self._score_document(doc)
            doc["_relevance_score"] = score
            scored_docs.append(doc)
        
        # Step 2: Sort by relevance score (highest first)
        scored_docs.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
        
        # Step 3: Apply size filtering and truncation
        processed_docs = []
        total_tokens = 0
        target_tokens = config.get("target_token_limit", 50000)
        
        stats = {"kept": 0, "truncated": 0, "skipped_size": 0, "skipped_limit": 0}
        
        for doc in scored_docs:
            content = doc.get("content_md", "")
            content_length = len(content)
            
            # Skip if too large
            if content_length > skip_docs_larger_than:
                stats["skipped_size"] += 1
                continue
            
            # Estimate tokens for this document
            estimated_tokens = min(content_length // 4, max_chars_per_doc // 4)
            
            # Check if we're approaching token limit
            if total_tokens + estimated_tokens > target_tokens:
                # Try to fit a smaller version if we have space
                remaining_tokens = target_tokens - total_tokens
                if remaining_tokens > 500:  # Minimum meaningful content
                    truncated_chars = remaining_tokens * 4
                    doc = self._apply_smart_truncation(doc, truncated_chars)
                    processed_docs.append(doc)
                    stats["truncated"] += 1
                    total_tokens += remaining_tokens
                else:
                    stats["skipped_limit"] += 1
                break
            
            # Apply standard truncation if needed
            if content_length > max_chars_per_doc:
                doc = self._apply_smart_truncation(doc, max_chars_per_doc)
                stats["truncated"] += 1
            else:
                stats["kept"] += 1
            
            processed_docs.append(doc)
            total_tokens += estimated_tokens
        
        print(f"   📊 Document processing:")
        print(f"      ✅ Kept as-is: {stats['kept']}")
        print(f"      ✂️ Truncated: {stats['truncated']}")
        print(f"      🚫 Skipped (size): {stats['skipped_size']}")
        print(f"      🚫 Skipped (limit): {stats['skipped_limit']}")
        print(f"      📈 Final tokens: {total_tokens:,}")
        
        return processed_docs
    
    def _score_document(self, doc: Dict[str, Any]) -> float:
        """Score document for relevance and quality."""
        content = doc.get("content_md", "") or ""
        title = doc.get("title", "") or ""
        url = doc.get("url", "") or ""
        keyword = doc.get("_source_keyword", "") or ""
        keyword_score = doc.get("_keyword_score", 0.5)
        
        # Base score from keyword importance
        score = keyword_score
        
        # Boost for keyword matches in title (more important)
        if keyword and title and keyword.lower() in title.lower():
            score += 0.3
        
        # Boost for official government sources
        authority_indicators = ["gov.co", "minambiente", "anla", "parquesnacionales"]
        if url and any(indicator in url.lower() for indicator in authority_indicators):
            score += 0.2
        
        # Boost for legal documents
        legal_indicators = ["resolución", "decreto", "ley", "normativa", "reglamento"]
        if title and any(indicator in title.lower() for indicator in legal_indicators):
            score += 0.15
        
        # Slight penalty for very long documents (less efficient)
        content_length = len(content)
        if content_length > 100000:
            score -= 0.1
        elif content_length < 1000:
            score -= 0.05  # Very short docs might not be comprehensive
        
        return max(0.0, min(2.0, score))  # Clamp to reasonable range
    
    def _apply_smart_truncation(self, doc: Dict[str, Any], max_chars: int) -> Dict[str, Any]:
        """Apply intelligent content truncation preserving important information."""
        content = doc.get("content_md", "")
        if len(content) <= max_chars:
            return doc
        
        # Try to preserve structure by keeping paragraphs intact
        paragraphs = content.split('\n\n')
        truncated_content = ""
        current_length = 0
        
        for paragraph in paragraphs:
            if current_length + len(paragraph) + 2 <= max_chars - 50:  # Leave space for truncation note
                truncated_content += paragraph + "\n\n"
                current_length += len(paragraph) + 2
            else:
                break
        
        # Add truncation note
        truncated_content += "\n\n[Content truncated for efficiency...]"
        
        # Create modified document
        doc_copy = doc.copy()
        doc_copy["content_md"] = truncated_content
        doc_copy["_original_length"] = len(content)
        doc_copy["_truncated"] = True
        doc_copy["_truncation_ratio"] = len(truncated_content) / len(content)
        
        return doc_copy
    
    def _validate_token_limits(self, docs: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Final validation to ensure we stay within token limits."""
        total_chars = sum(len(doc.get("content_md", "")) for doc in docs)
        estimated_tokens = total_chars // 4
        target_limit = config.get("target_token_limit", 50000)
        
        if estimated_tokens <= target_limit:
            return docs
        
        print(f"   ⚡ Final adjustment: {estimated_tokens:,} → {target_limit:,} tokens")
        
        # Keep highest scoring documents that fit within limit
        adjusted_docs = []
        current_tokens = 0
        
        for doc in docs:
            doc_tokens = len(doc.get("content_md", "")) // 4
            if current_tokens + doc_tokens <= target_limit:
                adjusted_docs.append(doc)
                current_tokens += doc_tokens
            else:
                break
        
        return adjusted_docs
    
    def _generate_cache_key(self, keywords: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Generate cache key for search results."""
        key_data = {
            "keywords": sorted([kw["keyword"] for kw in keywords[:10]]),
            "mode": config.get("target_token_limit", 50000),
            "version": "v2"  # Update when algorithm changes
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Check for cached results."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            # Check if cache is not too old (1 hour)
            if time.time() - cache_file.stat().st_mtime < 3600:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
        
        return None
    
    def _cache_results(self, cache_key: str, docs: List[Dict[str, Any]]):
        """Cache results for future use."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Only cache if we have meaningful results
            if docs and len(docs) > 0:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   ⚠️ Cache write failed: {e}")
    
    def _merge_cached_with_state(self, cached_docs: List[Dict[str, Any]], state_json: Dict[str, Any]) -> Dict[str, Any]:
        """Merge cached results with current state."""
        current = deepcopy(state_json)
        kb = current.setdefault("legal", {}).setdefault("kb", {})
        
        # Extract keywords from cached docs
        keywords = list(set(doc.get("_source_keyword", "") for doc in cached_docs if doc.get("_source_keyword")))
        
        kb["keywords"] = keywords
        kb["scraped_pages"] = {
            "count": len(cached_docs),
            "rows": cached_docs,
            "_metadata": {
                "cached": True,
                "cache_timestamp": time.time(),
                "estimated_tokens": sum(len(doc.get("content_md", "")) // 4 for doc in cached_docs)
            }
        }
        
        return current
    
    def _create_final_state(self, state_json: Dict[str, Any], keywords: List[Dict[str, Any]], docs: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Create final state structure with processed documents."""
        current = deepcopy(state_json)
        kb = current.setdefault("legal", {}).setdefault("kb", {})
        
        # Calculate final statistics
        total_chars = sum(len(doc.get("content_md", "")) for doc in docs)
        estimated_tokens = total_chars // 4
        truncated_count = sum(1 for doc in docs if doc.get("_truncated", False))
        
        kb["keywords"] = [kw["keyword"] for kw in keywords]
        kb["scraped_pages"] = {
            "count": len(docs),
            "rows": docs,
            "_metadata": {
                "optimization_mode": config.get("target_token_limit", "unknown"),
                "total_chars": total_chars,
                "estimated_tokens": estimated_tokens,
                "truncated_docs": truncated_count,
                "processing_timestamp": time.time(),
                "keyword_sources": len(set(doc.get("_source_keyword", "") for doc in docs)),
                "average_relevance_score": sum(doc.get("_relevance_score", 0) for doc in docs) / max(len(docs), 1)
            }
        }
        
        return current
    
    def _update_metrics(self, processing_time: float):
        """Update performance metrics."""
        self.metrics["average_processing_time"] = (
            (self.metrics["average_processing_time"] * (self.metrics["total_calls"] - 1) + processing_time) 
            / self.metrics["total_calls"]
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        return {
            "total_calls": self.metrics["total_calls"],
            "cache_hit_rate": self.metrics["cache_hits"] / max(self.metrics["total_calls"], 1),
            "average_processing_time": self.metrics["average_processing_time"],
            "tokens_saved": self.metrics["total_tokens_saved"]
        }


# Global instance for easy integration
_global_searcher = IntelligentGeoKBSearcher()

def enhanced_geo_kb_search_from_state(
    state_json: Dict[str, Any], 
    per_keyword_limit: int = 2,
    max_keywords: int = 12,
    max_chars_per_doc: int = 15000,
    skip_docs_larger_than: int = 500000,
    optimization_mode: str = "balanced"
) -> Dict[str, Any]:
    """
    Drop-in replacement for geo_kb_search_from_state with intelligent optimization.
    
    This function provides the same interface but with advanced content management:
    - Intelligent keyword extraction and prioritization
    - Smart document ranking and filtering  
    - Adaptive content truncation
    - Caching for improved performance
    - Rate limiting protection
    """
    return _global_searcher.enhanced_geo_kb_search_from_state(
        state_json=state_json,
        per_keyword_limit=per_keyword_limit,
        max_keywords=max_keywords,
        max_chars_per_doc=max_chars_per_doc,
        skip_docs_larger_than=skip_docs_larger_than,
        optimization_mode=optimization_mode
    )


if __name__ == "__main__":
    # Test the enhanced function
    print("🧪 Testing Enhanced geo_kb_search")
    
    test_state = {
        "legal": {
            "geo2neo": {
                "alias_input": ["Biótico", "Compensación", "Gestión de Riesgo"]
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
    
    for mode in ["fast", "balanced", "comprehensive"]:
        print(f"\n🧪 Testing {mode} mode:")
        result = enhanced_geo_kb_search_from_state(test_state, optimization_mode=mode)
        
        metadata = result["legal"]["kb"]["scraped_pages"]["_metadata"]
        print(f"   📊 Tokens: {metadata['estimated_tokens']:,}")
        print(f"   📄 Docs: {metadata.get('count', 0)}")
        print(f"   ✂️ Truncated: {metadata.get('truncated_docs', 0)}")
    
    # Show performance stats
    print(f"\n📈 Performance Stats:")
    stats = _global_searcher.get_performance_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
