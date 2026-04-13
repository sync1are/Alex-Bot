#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
from bs4 import BeautifulSoup
from exa_py import Exa
from typing import Dict, List
import os
import re
import requests


class WebLookup:
    def __init__(self, use_exa: bool = True):
        """
        Initialize WebLookup with both Google Custom Search and Exa support

        Args:
            use_exa: If True, prefer Exa for semantic search (default: True)
        """
        # Google Custom Search API
        self.google_api_key = "AIzaSyBbjHnT6EP1I_nuyykXzDli-DISXQWG1pY"
        self.cse_id = "82df5170554a243dd"
        self.google_base_url = "https://www.googleapis.com/customsearch/v1"

        # Exa API
        self.exa_api_key = os.getenv("EXA_API_KEY")
        self.exa_client = None
        if self.exa_api_key:
            try:
                self.exa_client = Exa(self.exa_api_key)
            except Exception as e:
                print(f"Exa initialization failed: {e}")

        self.use_exa = use_exa and self.exa_client is not None
        self.session = requests.Session()

        # Print which search engine is being used
        if self.use_exa:
            print("🔍 Using Exa AI (semantic search)")
        else:
            print("🔍 Using Google Custom Search (keyword search)")

    def search_google(self, query: str) -> List[Dict]:
        """Traditional Google Custom Search"""
        try:
            params = {
                'key': self.google_api_key,
                "cx": self.cse_id,
                'q': query,
                'num': 3  # Get top 3 results
            }
            response = self.session.get(self.google_base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            print(f"Google search error: {e}")
            return []

    def search_exa(self, query: str) -> List[Dict]:
        """
        Exa AI semantic search - better for natural language queries
        Returns results in same format as Google for compatibility
        """
        if not self.exa_client:
            print("⚠️ Exa not available, falling back to Google")
            return self.search_google(query)

        try:
            # Exa's neural search with content extraction
            results = self.exa_client.search_and_contents(
                query,
                type="auto",  # Auto-detect best search type
                num_results=3,
                text=True,  # Get full text content
 highlights = True # Get key highlights
            )

            # Convert Exa results to Google-compatible format
            formatted_results = []
            for result in results.results:
                formatted_results.append({
                    'title': result.title,
                    'link': result.url,
                    'snippet': result.highlights[0] if result.highlights else '',
                    'content': result.text[:2000] if result.text else ''  # Exa provides clean content!
                })

            return formatted_results

        except Exception as e:
            print(f"Exa search error: {e}")
            # Fallback to Google if Exa fails
            print("Falling back to Google Custom Search...")
            return self.search_google(query)

    def scrape_content(self, url: str) -> str:
        """
        Scrape content from URL
        Note: When using Exa, this is often unnecessary as Exa provides clean content
        """
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Get text from paragraphs
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text() for p in paragraphs)
            return text[:2000]  # Limit length
        except:
            return ""

    def handle_command(self, text: str) -> str:
        """
        Main search and answer function
        Automatically uses best search engine available
        """
        # Clean up query
        query = text.lower().replace("search", "").replace("for", "").strip()

        # Choose search engine
        if self.use_exa:
            results = self.search_exa(query)
        else:
            results = self.search_google(query)

        if not results:
            return "Sorry, I couldn't find anything about that."

        # Build context from search results
        context = []
        for i, result in enumerate(results, 1):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')

            # Check if Exa already provided content
            if "content" in result and result['content']:
                content = result['content']
            else:
                # Scrape additional content if needed (for Google results)
                content = self.scrape_content(link)

            context.append(f"Source [{i}]:\nTitle: {title}\nURL: {link}\n")
            context.append(f"Content: {snippet}\n{content}\n")

        # Prepare prompt for LLM
        system_prompt = """You are a helpful AI assistant. Answer the question using ONLY the provided sources.
        If you can't find the answer in the sources, say "I couldn't find specific information about that."
        Use [1], [2], etc. to cite sources. Be concise but informative."""

        user_prompt = f"""Question: {query}

Sources:
{'\n'.join(context)}

Please answer the question using only these sources."""

        try:
            from core.llm import query_llm
            answer = query_llm(
                user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200
            )
            return answer
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def smart_search(self, query: str, force_engine: str = None) -> str:
        """
        Smart search that chooses the best engine based on query type

        Args:
            query: Search query
            force_engine: Force specific engine ("exa" or "google")
        """
        # Override engine preference if specified
        if force_engine == "exa" and self.exa_client:
            results = self.search_exa(query)
        elif force_engine == "google":
            results = self.search_google(query)
        else:
            # Auto-detect best engine based on query characteristics
            is_semantic_query = any(word in query.lower() for word in 
                ["article about", 'explain', 'how does', 'what is', 
                'interesting', 'best', 'guide to', 'deep dive'])

            if is_semantic_query and self.use_exa:
                print("📊 Detected semantic query, using Exa...")
                results = self.search_exa(query)
            else:
                print("🔑 Detected keyword query, using Google...")
                results = self.search_google(query)

        # Process results same as handle_command
        if not results:
            return "Sorry, I couldn't find anything about that."

        # ... rest of the processing (same as handle_command)
        context = []
        for i, result in enumerate(results, 1):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            content = result.get('content', '') or self.scrape_content(link)

            context.append(f"Source [{i}]:\nTitle: {title}\nURL: {link}\n")
            context.append(f"Content: {snippet}\n{content}\n")

        return '\n'.join(context)

# Create instances with different configurations
# Default: Use Exa if available, fallback to Google
web_lookup = WebLookup(use_exa=True)

# Force Google only
# web_lookup_google = WebLookup(use_exa=False)

# Usage examples:
# result = web_lookup.handle_command("search for latest AI developments")
# result = web_lookup.smart_search("fascinating article about quantum computing")
# result = web_lookup.smart_search("Python tutorial", force_engine="google")