"""
Google Custom Search Engine (CSE) Utility Module
Provides functions to search for manufacturer specifications using Google CSE API
"""

import requests
import json
from typing import List, Dict, Any, Optional
import time


def search_google_cse(
    query: str,
    api_key: str,
    cx: str,
    num_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search Google Custom Search Engine for manufacturer specifications.
    
    Args:
        query: Search query string
        api_key: Google CSE API key
        cx: Custom Search Engine ID
        num_results: Number of results to return (max 10)
    
    Returns:
        List of search results with title, link, and snippet
    """
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num_results, 10)  # Google CSE max is 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "displayLink": item.get("displayLink", "")
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Google CSE search failed: {e}")
        return []
    except Exception as e:
        print(f"[WARNING] Unexpected error in Google CSE search: {e}")
        return []


def execute_search_queries(
    queries: List[Dict[str, Any]],
    api_key: str,
    cx: str,
    max_queries: int = 3,
    delay_between_queries: float = 0.5
) -> Dict[str, Any]:
    """
    Execute multiple search queries and aggregate results.
    
    Args:
        queries: List of query dictionaries with 'query' and 'priority' keys
        api_key: Google CSE API key
        cx: Custom Search Engine ID
        max_queries: Maximum number of queries to execute
        delay_between_queries: Delay in seconds between queries to avoid rate limiting
    
    Returns:
        Dictionary with aggregated search results
    """
    all_results = []
    queries_executed = 0
    
    # Sort by priority (high first)
    sorted_queries = sorted(
        queries,
        key=lambda x: 0 if x.get("priority") == "high" else 1
    )
    
    for query_info in sorted_queries[:max_queries]:
        query = query_info.get("query", "")
        if not query:
            continue
        
        print(f"[SEARCH] Executing query: {query}")
        results = search_google_cse(query, api_key, cx, num_results=5)
        
        if results:
            all_results.extend(results)
            queries_executed += 1
            
            # Add delay to avoid rate limiting
            if queries_executed < max_queries:
                time.sleep(delay_between_queries)
    
    return {
        "queries_executed": queries_executed,
        "total_results": len(all_results),
        "results": all_results
    }


def extract_specs_from_results(
    results: List[Dict[str, Any]],
    product_name: str
) -> str:
    """
    Extract relevant specifications from search results.
    
    Args:
        results: List of search result dictionaries
        product_name: Name of the product being searched
    
    Returns:
        Formatted string with extracted specifications
    """
    if not results:
        return "No search results available."
    
    specs_text = f"Search Results for {product_name}:\n\n"
    
    for i, result in enumerate(results[:10], 1):  # Limit to top 10
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        
        specs_text += f"{i}. {title}\n"
        specs_text += f"   Source: {link}\n"
        specs_text += f"   {snippet}\n\n"
    
    return specs_text


def search_manufacturer_specs(
    product_name: str,
    search_queries: List[Dict[str, Any]],
    api_key: str,
    cx: str
) -> str:
    """
    High-level function to search for manufacturer specifications.
    
    Args:
        product_name: Name of the product
        search_queries: List of search query dictionaries
        api_key: Google CSE API key
        cx: Custom Search Engine ID
    
    Returns:
        Formatted string with search results and extracted specs
    """
    print(f"[SEARCH] Starting manufacturer spec search for: {product_name}")
    print(f"[SEARCH] Executing {len(search_queries)} search queries...")
    
    # Execute searches
    search_data = execute_search_queries(
        queries=search_queries,
        api_key=api_key,
        cx=cx,
        max_queries=3  # Limit to 3 queries to save API quota
    )
    
    print(f"[SEARCH] Completed {search_data['queries_executed']} queries")
    print(f"[SEARCH] Found {search_data['total_results']} total results")
    
    # Extract and format specs
    specs_text = extract_specs_from_results(
        results=search_data["results"],
        product_name=product_name
    )
    
    return specs_text


if __name__ == "__main__":
    # Test the search functionality
    test_query = "Canon EOS R5 Mark II specifications"
    test_api_key = "YOUR_API_KEY"
    test_cx = "YOUR_CX"
    
    results = search_google_cse(test_query, test_api_key, test_cx)
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result['title']}")
