"""
Query Processing Module - Enhance queries without big LLMs
"""

import re
from typing import List
import nltk

try:
    from nltk.corpus import wordnet, stopwords
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)


class QueryProcessor:
    """Process and enhance queries using lightweight techniques"""
    
    def __init__(self):
        self.stopwords = set(stopwords.words('english'))
        
        self.question_patterns = {
            'what': ['definition', 'explanation', 'meaning'],
            'how': ['process', 'method', 'steps', 'way'],
            'why': ['reason', 'cause', 'purpose'],
            'when': ['time', 'date', 'period'],
            'where': ['location', 'place', 'position']
        }
    
    def decompose_query(self, query: str) -> List[str]:
        """Break complex queries into sub-queries"""
        
        sub_queries = [query]
        query_lower = query.lower()
        
        # Split by "and"
        if " and " in query_lower:
            parts = query_lower.split(" and ")
            sub_queries.extend([part.strip() for part in parts if len(part.strip()) > 3])
        
        # Add question-focused sub-queries
        for question_word, keywords in self.question_patterns.items():
            if query_lower.startswith(question_word):
                main_topic = ' '.join(query.split()[-5:])
                for keyword in keywords[:2]:
                    sub_queries.append(f"{keyword} {main_topic}")
                break
        
        # Extract entities (capitalized phrases)
        entities = self.extract_entities(query)
        sub_queries.extend(entities)
        
        # Deduplicate and limit
        return list(dict.fromkeys(sub_queries))[:5]
    
    def generate_search_variations(self, query: str) -> List[str]:
        """Generate search query variations"""
        
        variations = [query]
        query_lower = query.lower()
        
        # Add question forms if not already a question
        if not query.strip().endswith('?'):
            variations.append(f"what is {query}")
            variations.append(f"explain {query}")
        
        # Remove question words for keyword search
        clean_query = query_lower
        for word in ['what is', 'how does', 'why', 'when', 'where', 'who']:
            clean_query = clean_query.replace(word, '').strip()
        if clean_query and clean_query != query_lower:
            variations.append(clean_query)
        
        # Expand with synonyms
        synonym_query = self.expand_with_synonyms(query)
        if synonym_query != query:
            variations.append(synonym_query)
        
        return list(dict.fromkeys(variations))[:5]
    
    def expand_with_synonyms(self, query: str) -> str:
        """Add synonyms to important words"""
        
        words = query.split()
        expanded_words = []
        
        for word in words:
            word_lower = word.lower()
            
            # Skip stopwords and short words
            if word_lower in self.stopwords or len(word) < 4:
                expanded_words.append(word)
                continue
            
            # Get synonyms
            synonyms = self.get_word_synonyms(word_lower)
            
            if synonyms:
                # Add word with top synonym
                expanded_words.append(f"{word} {synonyms[0]}")
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def get_word_synonyms(self, word: str) -> List[str]:
        """Get synonyms from WordNet"""
        
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym != word and len(synonym) > 3:
                    synonyms.add(synonym)
        
        return list(synonyms)[:2]
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract capitalized phrases (likely entities)"""
        
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entities = re.findall(pattern, text)
        return [e for e in entities if len(e) > 2][:3]
    
    def create_hypothetical_document(self, query: str) -> str:
        """Create hypothetical document using templates"""
        
        templates = {
            'what is': "{topic} is a concept that refers to {description}. It involves {aspects} and is commonly used in {context}.",
            'how': "{topic} works through {process}. The main steps include {steps}. This approach is effective because {reason}.",
            'why': "{topic} occurs due to {cause}. This results in {effect}. Understanding this helps {benefit}.",
            'when': "{topic} typically happens {timeframe}. This timing is important because {significance}.",
            'where': "{topic} is found in {location}. It exists in this context because {reason}.",
            'default': "{topic} represents {description}. Key characteristics include {features}. This is relevant for {application}."
        }
        
        # Select template
        query_lower = query.lower()
        template = templates['default']
        for key in templates:
            if query_lower.startswith(key):
                template = templates[key]
                break
        
        # Extract main topic
        topic = self.extract_main_topic(query)
        
        # Fill template with generic terms
        hypothetical = template.format(
            topic=topic,
            description="an important concept",
            aspects="multiple components and principles",
            context="various applications and scenarios",
            process="systematic methods and techniques",
            steps="planning, execution, and evaluation",
            reason="fundamental principles and best practices",
            cause="underlying factors and conditions",
            effect="significant outcomes and implications",
            benefit="better understanding and decision-making",
            timeframe="during specific conditions or periods",
            significance="its impact and relevance",
            location="relevant environments and settings",
            features="distinct properties and attributes",
            application="practical use cases and implementations"
        )
        
        return hypothetical
    
    def extract_main_topic(self, query: str) -> str:
        """Extract the main subject of the query"""
        
        # Remove question words
        topic = query.lower()
        for word in ['what is', 'how does', 'how do', 'why', 'when', 'where', 'who', 'explain', 'define']:
            topic = topic.replace(word, '').strip()
        
        # Take last 3-5 words as topic
        words = topic.split()
        if len(words) > 3:
            return ' '.join(words[-3:])
        return topic
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract important terms from text"""
        
        from collections import Counter
        
        # Find words (4+ letters)
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # Remove stopwords
        keywords = [w for w in words if w not in self.stopwords]
        
        # Return most frequent
        return [word for word, _ in Counter(keywords).most_common(10)]


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]