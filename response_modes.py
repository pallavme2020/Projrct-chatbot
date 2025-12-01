"""
Response Mode Configurations
"""

# Mode configurations
MODE_CONFIGS = {
    'detail': {
        'name': 'DETAIL',
        'emoji': '📙📙📙',
        'num_docs': 15,
        'target_words': '400-600',
        'style': 'Comprehensive with examples',
        'use_two_stage': True,
        'show_cot': True,
        'search_mode': 'thorough',
        'expected_time': '~20 seconds'
    },
    'normal': {
        'name': 'NORMAL',
        'emoji': '📗📗',
        'num_docs': 7,
        'target_words': '150-250',
        'style': 'Balanced and clear',
        'use_two_stage': True,
        'show_cot': True,
        'search_mode': 'standard',
        'expected_time': '~10 seconds'
    },
    'shortconsize': {
        'name': 'SHORT & CONCISE',
        'emoji': '📕',
        'num_docs': 3,
        'target_words': '30-80',
        'style': 'Key points only',
        'use_two_stage': False,
        'show_cot': False,
        'search_mode': 'fast',
        'expected_time': '~4 seconds'
    }
}


# Mode instruction templates
MODE_INSTRUCTIONS = {
    'detail': """Provide comprehensive, detailed explanation:
- In-depth analysis with background context
- Multiple examples with clear explanations
- Step-by-step breakdowns where relevant
- Related concepts and connections
- Practical applications and use cases
- Common pitfalls and best practices
Target length: 400-600 words while maintaining accuracy""",
    
    'normal': """Provide balanced, clear explanation:
- Main concept clearly explained
- One practical example if relevant
- Key points highlighted
- Direct and focused response
- Avoid unnecessary details
Target length: 150-250 words""",
    
    'shortconsize': """Provide brief, concise answer:
- Essential information only
- No background or extra context
- Direct response to the question
- Use bullet points only if listing multiple items
Target length: 30-80 words maximum"""
}


# Stage 1 - Analysis prompt template
ANALYSIS_PROMPT = """You are analyzing documents to prepare an accurate answer.

Documents:
{documents}

Query: {query}

Your task is ONLY to analyze, NOT to answer yet.

Provide your analysis in this format:

1. RELEVANCE CHECK:
   - Which documents directly address the query?
   - Rate each source: High/Medium/Low relevance

2. KEY INFORMATION:
   - What facts are available?
   - Any specific data (numbers, specifications)?
   - Contradictions between sources?

3. GAPS:
   - What information is missing?
   - Any assumptions needed?

4. CITATION PLAN:
   - Which documents to cite?
   - Best order to present information?

5. CONFIDENCE:
   - Can I fully answer? (Yes/Partial/No)
   - Confidence level: High/Medium/Low
   - Reason for this confidence

DO NOT provide the final answer yet. Only analysis."""


# Stage 2 - Answer prompt template
ANSWER_PROMPT = """Based on your analysis:

{analysis}

Now provide the final answer following these guidelines:

MODE: {mode}

{mode_instructions}

Requirements:
- Use ONLY information identified as relevant in analysis
- Cite sources marked as authoritative using [1][2][3] format
- If gaps were noted, acknowledge them briefly
- Match the assessed confidence level
- Stay within target word count

Provide your answer now with proper citations."""


# Single-stage prompt for short mode
SHORT_PROMPT = """Documents:
{documents}

Query: {query}

{mode_instructions}

Provide a concise answer with citations [1][2][3]."""


def get_mode_banner(mode: str, config: dict) -> str:
    """Generate mode banner"""
    
    banner = f"""╔════════════════════════════════════════╗
║  {config['emoji']} MODE: {config['name']:<28} ║
║  📊 Method: {'Two-Stage Analysis' if config['use_two_stage'] else 'Single-Stage (optimized)':<26} ║
╚════════════════════════════════════════╝"""
    
    return banner


def format_analysis_display(analysis: str) -> str:
    """Format analysis for display"""
    
    return f"""💭 Analysis Phase:
────────────────────────────────────────
{analysis}
────────────────────────────────────────"""