"""
Custom ADK Tool for Google Custom Search API
Enables agents to perform real-time web searches for manufacturer specifications
"""

import os
from typing import Dict, Any
from google.adk.tools import FunctionTool
from search_utils import search_google_cse


def google_custom_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using Google Custom Search API to find manufacturer 
    specifications, product details, and technical information.
    
    Args:
        query: The search query to execute
        num_results: Number of results to return (1-10), default is 5
        
    Returns:
        Dictionary with search results including titles, URLs, and snippets
    """
    # Get API credentials from environment
    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX")
    
    if not api_key or not cx:
        return {
            "success": False,
            "query": query,
            "results_count": 0,
            "message": "Google Custom Search API credentials not configured",
            "results": []
        }
    
    print(f"[TOOL] Executing Google Custom Search: {query}")
    
    # Execute the search
    results = search_google_cse(
        query=query,
        api_key=api_key,
        cx=cx,
        num_results=num_results
    )
    
    if not results:
        return {
            "success": False,
            "query": query,
            "results_count": 0,
            "message": "No results found",
            "results": []
        }
    
    # Format results for the agent
    formatted_results = []
    for result in results:
        formatted_results.append({
            "title": result.get("title", ""),
            "url": result.get("link", ""),
            "snippet": result.get("snippet", ""),
            "source": result.get("displayLink", "")
        })
    
    # Create a summary text for easy consumption
    summary = f"Found {len(results)} results for '{query}':\n\n"
    for i, result in enumerate(formatted_results, 1):
        summary += f"{i}. {result['title']}\n"
        summary += f"   Source: {result['source']}\n"
        summary += f"   {result['snippet']}\n\n"
    
    print(f"[TOOL] Search completed - found {len(results)} results")
    
    return {
        "success": True,
        "query": query,
        "results_count": len(results),
        "results": formatted_results,
        "summary": summary
    }


def create_google_search_tool() -> FunctionTool:
    """
    Factory function to create a Google Custom Search tool for ADK agents.
    
    Returns:
        FunctionTool instance configured for Google Custom Search
    """
    # FunctionTool takes the function as the first positional argument
    return FunctionTool(google_custom_search)
