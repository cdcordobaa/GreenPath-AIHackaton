#!/usr/bin/env python3
"""
Analyze token counts from the MCP search results and provide solutions.
"""

def analyze_tokens():
    print('📊 CONTENT SIZE ANALYSIS')
    print('=' * 50)
    
    # Actual results from our test
    content_sizes = [
        ('Biótico Doc 1', 27730, 'Small legal document'),
        ('Biótico Doc 2', 1534, 'Very small snippet'), 
        ('Biótico Doc 3', 322191, 'Large legal document'),
        ('Compensación Doc 1', 5734, 'Small resolution'),
        ('Compensación Doc 2', 27730, 'Duplicate of Biótico Doc 1'),
        ('Compensación Doc 3', 31075, 'Medium legal document'),
        ('Gestión de Riesgo Doc 1', 1650339, 'HUGE decree (1.6MB)'),
        ('Gestión de Riesgo Doc 2', 1975369, 'HUGE decree (1.9MB)'),
        ('Gestión de Riesgo Doc 3', 2154456, 'HUGE decree (2.1MB)'),
    ]
    
    total_chars = sum(size for _, size, _ in content_sizes)
    total_tokens = total_chars // 4
    
    print(f'Current results (9 docs, 3 keywords):')
    print(f'  Total: {total_chars:,} chars = ~{total_tokens:,} tokens')
    print(f'  That\'s ~{total_tokens/1000:.1f}K tokens!')
    
    print(f'\nIf we search all 12 keywords:')
    projected_tokens = total_tokens * 4  # 12 keywords vs 3
    print(f'  Projected: ~{projected_tokens:,} tokens (~{projected_tokens/1000:.1f}K)')
    
    print(f'\n🚨 PROBLEM:')
    print(f'  - Most LLMs have 32K-128K token limits')
    print(f'  - Gemini 2.5 Flash: 1M token limit')
    print(f'  - Current content would use most/all of context!')
    
    print(f'\n💡 SOLUTIONS:')
    print(f'1. LIMIT SEARCH RESULTS:')
    print(f'   - Use limit=1 instead of limit=3 per keyword')
    print(f'   - Projected tokens: ~{total_tokens//3:,} (~{total_tokens//3000:.1f}K)')
    
    print(f'\n2. FILTER BY SIZE:')
    print(f'   - Skip documents > 100K chars (~25K tokens)')
    filtered_sizes = [size for _, size, _ in content_sizes if size <= 100000]
    filtered_tokens = sum(filtered_sizes) // 4
    print(f'   - Would keep {len(filtered_sizes)} docs: ~{filtered_tokens:,} tokens')
    
    print(f'\n3. CONTENT TRUNCATION:')
    print(f'   - Take first 5K chars of each document')
    print(f'   - Projected: ~{12 * 5000 // 4:,} tokens (very manageable!)')
    
    print(f'\n4. SUMMARIZATION:')
    print(f'   - Summarize large docs before including')
    print(f'   - Use LLM to extract key points')
    
    print(f'\n📝 DETAILED BREAKDOWN:')
    for name, size, desc in content_sizes:
        tokens = size // 4
        if size > 500000:  # > 500K chars
            status = '🚨 HUGE'
        elif size > 100000:  # > 100K chars  
            status = '⚠️ LARGE'
        elif size > 10000:   # > 10K chars
            status = '📄 MEDIUM'
        else:
            status = '✅ SMALL'
        print(f'   {status} {name}: {size:,} chars → ~{tokens:,} tokens')
    
    print(f'\n🎯 RECOMMENDATIONS:')
    print(f'1. IMMEDIATE FIX: Reduce per_keyword_limit from 5 to 1')
    print(f'   - Current: limit=5, gets ~516K tokens per keyword')
    print(f'   - Fixed: limit=1, gets ~172K tokens per keyword')
    print(f'   - For 12 keywords: ~2M tokens → ~1.5M tokens')
    
    print(f'\n2. CONTENT TRUNCATION: Add max_chars_per_doc=10000')
    print(f'   - Truncate each doc to 10K chars (~2.5K tokens)')
    print(f'   - For 12 keywords × 1 doc: ~30K tokens (perfect!)')
    
    print(f'\n3. SMART FILTERING: Skip docs > 200K chars')
    print(f'   - Focus on more digestible legal documents')
    print(f'   - Large decrees are often too generic anyway')
    
    print(f'\n✅ OPTIMAL CONFIGURATION:')
    print(f'   per_keyword_limit = 1')
    print(f'   max_chars_per_doc = 10000') 
    print(f'   skip_docs_larger_than = 200000')
    print(f'   Expected result: ~{12 * 10000 // 4:,} tokens (excellent!)')

if __name__ == '__main__':
    analyze_tokens()

