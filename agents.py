"""
Google ADK Sequential Agents for Product Attribute Extraction
Two-agent pipeline: Image Analysis -> Search Enhancement
"""

import os
from google.adk import agents, models

# Import API keys from config
from config import GEMINI_API_KEY, GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX

# Camera attributes to extract (20+ attributes)
ATTRIBUTES = [
    # Physical Attributes
    "Color", "Body Material", "Dimensions", "Weight",
    # Camera Specifications
    "Sensor Type", "Sensor Size", "Megapixels", "ISO Range",
    "Lens Mount", "Viewfinder Type", "Display Type", "Display Size",
    # Features
    "Autofocus System", "Video Capabilities", "Connectivity Features",
    "Battery Type", "Memory Card Slot", "USB Port Type", "Hot Shoe Mount",
    "Image Stabilization",
    # Additional
    "Shutter Speed Range", "Continuous Shooting Speed"
]


def create_sequential_agent():
    """
    Creates a sequential agent pipeline with two specialized agents.
    
    Returns:
        SequentialAgent: Configured agent pipeline
    """
    
    # Initialize Gemini model
    gemini_model = models.Gemini(
        api_key=GEMINI_API_KEY,
        model_name="gemini-2.0-flash-exp"
    )
    
    # ========================================================================
    # AGENT 1: IMAGE ANALYSIS AGENT
    # Analyzes product images and extracts attributes
    # ========================================================================
    
    image_analysis_agent = agents.LlmAgent(
        name="ImageAnalysisAgent",
        model=gemini_model,
        instruction=f"""You are an expert product analyst specializing in camera equipment.

**Your Task:**
Analyze the provided product image(s) and extract as many of these attributes as possible:
{', '.join(ATTRIBUTES)}

**Instructions:**
1. Examine the image VERY carefully for all visible details
2. Look for: buttons, ports, displays, viewfinders, hot shoes, tripod mounts, labels, text, specifications
3. For dimensions/weight: Check for any packaging labels or specification stickers
4. If an attribute is not visible or determinable, set it to null
5. Be thorough but only report what you can actually see

**Product Description:**
Write a compelling 2-3 sentence e-commerce product description that:
- Highlights key features visible in the image
- Appeals to photographers and videographers
- Uses professional, persuasive language
- Focuses on benefits and capabilities

**Output Format (JSON only, no markdown):**
{{
    "attributes": {{
        "Color": "value or null",
        "Body Material": "value or null",
        "Dimensions": "W x H x D mm or null",
        "Weight": "grams or null",
        "Sensor Type": "value or null",
        "Sensor Size": "value or null",
        "Megapixels": "value or null",
        "ISO Range": "value or null",
        "Lens Mount": "value or null",
        "Viewfinder Type": "value or null",
        "Display Type": "value or null",
        "Display Size": "value or null",
        "Autofocus System": "value or null",
        "Video Capabilities": "value or null",
        "Connectivity Features": "value or null",
        "Battery Type": "value or null",
        "Memory Card Slot": "value or null",
        "USB Port Type": "value or null",
        "Hot Shoe Mount": "value or null",
        "Image Stabilization": "value or null",
        "Shutter Speed Range": "value or null",
        "Continuous Shooting Speed": "value or null"
    }},
    "product_description": "Your compelling e-commerce description here",
    "extraction_confidence": "high/medium/low",
    "visible_features": ["list", "of", "key", "features", "seen"]
}}

Return ONLY valid JSON, no code blocks or markdown.""",
        description="Analyzes product images and extracts camera attributes",
        output_key="image_analysis_result"
    )
    
    # ========================================================================
    # AGENT 2: SEARCH ENHANCEMENT AGENT
    # Uses Google Custom Search to enhance attributes
    # ========================================================================
    
    search_enhancement_agent = agents.LlmAgent(
        name="SearchEnhancementAgent",
        model=gemini_model,
        instruction="""You are a product data enrichment specialist.

**Context:**
Product Name: {product_name}
Initial Extraction Results:
{image_analysis_result}

**Your Task:**
1. Review the extracted attributes from the image analysis
2. Identify missing attributes (null values)
3. Generate 3-5 targeted Google search queries to find official manufacturer specifications
4. Use the search results to fill in missing attributes
5. Enhance the product description with additional compelling details
6. Calculate the fill rate (percentage of non-null attributes)

**Search Query Guidelines:**
- Target official manufacturer websites (Canon, Sony, Nikon, etc.)
- Be specific: include model name and "specifications" or "specs"
- Examples:
  * "{product_name} official specifications site:canon.com"
  * "{product_name} technical specs sensor battery"
  * "{product_name} dimensions weight official"

**Output Format (JSON only, no markdown):**
{{
    "product_name": "{product_name}",
    "attributes": {{
        "Color": {{"value": "value or null", "source": "image/search/inferred"}},
        "Body Material": {{"value": "value or null", "source": "image/search/inferred"}},
        "Dimensions": {{"value": "W x H x D mm or null", "source": "image/search/inferred"}},
        "Weight": {{"value": "grams or null", "source": "image/search/inferred"}},
        "Sensor Type": {{"value": "value or null", "source": "image/search/inferred"}},
        "Sensor Size": {{"value": "value or null", "source": "image/search/inferred"}},
        "Megapixels": {{"value": "value or null", "source": "image/search/inferred"}},
        "ISO Range": {{"value": "value or null", "source": "image/search/inferred"}},
        "Lens Mount": {{"value": "value or null", "source": "image/search/inferred"}},
        "Viewfinder Type": {{"value": "value or null", "source": "image/search/inferred"}},
        "Display Type": {{"value": "value or null", "source": "image/search/inferred"}},
        "Display Size": {{"value": "value or null", "source": "image/search/inferred"}},
        "Autofocus System": {{"value": "value or null", "source": "image/search/inferred"}},
        "Video Capabilities": {{"value": "value or null", "source": "image/search/inferred"}},
        "Connectivity Features": {{"value": "value or null", "source": "image/search/inferred"}},
        "Battery Type": {{"value": "value or null", "source": "image/search/inferred"}},
        "Memory Card Slot": {{"value": "value or null", "source": "image/search/inferred"}},
        "USB Port Type": {{"value": "value or null", "source": "image/search/inferred"}},
        "Hot Shoe Mount": {{"value": "value or null", "source": "image/search/inferred"}},
        "Image Stabilization": {{"value": "value or null", "source": "image/search/inferred"}},
        "Shutter Speed Range": {{"value": "value or null", "source": "image/search/inferred"}},
        "Continuous Shooting Speed": {{"value": "value or null", "source": "image/search/inferred"}}
    }},
    "product_description": "Enhanced e-commerce description with search insights",
    "search_queries_used": ["query1", "query2", "query3"],
    "fill_rate": "percentage of non-null attributes",
    "total_attributes": 22,
    "filled_attributes": "count of non-null values"
}}

Return ONLY valid JSON, no code blocks or markdown.""",
        description="Enhances attributes using Google Custom Search API",
        output_key="final_result"
    )
    
    # ========================================================================
    # SEQUENTIAL AGENT ORCHESTRATOR
    # Chains the two agents together
    # ========================================================================
    
    sequential_pipeline = agents.SequentialAgent(
        name="ProductAttributeExtractionPipeline",
        sub_agents=[
            image_analysis_agent,
            search_enhancement_agent
        ],
        description="Two-stage pipeline: Image Analysis -> Search Enhancement"
    )
    
    return sequential_pipeline


# Create default instance
root_agent = create_sequential_agent()

if __name__ == "__main__":
    print("Google ADK Sequential Agent Pipeline")
    print(f"Agent: {root_agent.name}")
    print(f"Sub-agents: {len(root_agent.sub_agents)}")
    for i, agent in enumerate(root_agent.sub_agents, 1):
        print(f"  {i}. {agent.name}")
