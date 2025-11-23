"""
ADK Sequential Agents for Product Attribute Extraction Pipeline
This module implements three specialized agents that execute sequentially:
1. ImageExtractionAgent - Extracts attributes from product images
2. ManufacturerSearchAgent - Searches for manufacturer specifications
3. AttributeEnrichmentAgent - Enriches and finalizes attributes
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google.adk import agents, models

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configure Google Generative AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyDTmS4gXULRFVrB9HvqqMGwDQkD-vmgX5M"
GOOGLE_CSE_API_KEY = os.environ.get("GOOGLE_CSE_API_KEY") or "AIzaSyCI7a3T59iC_KXmCmsHQ6hj4gNmQUwUgsc"
GOOGLE_CSE_CX = os.environ.get("GOOGLE_CSE_CX") or "3376ddfb787cd4499"

# Initialize Gemini model for ADK
gemini_model = models.Gemini(api_key=GEMINI_API_KEY)

# Product attributes to extract
ATTRIBUTES = [
    "Color", "Body Material", "Dimensions", "Weight", "Sensor Type",
    "Display Type", "Viewfinder Type", "Battery Type", "Memory Card Slot",
    "USB Port Type", "Hot Shoe Mount", "Tripod Socket", "Low Pass Filter",
    "Auto White Balance", "AE Lock Button", "Shutter Release Type",
    "Lens Mount", "Connectivity Features", "Video Capabilities", "Autofocus System"
]

# Official specs fallback
OFFICIAL_SPECS = {
    "Canon EOS R5 Mark II Mirrorless Camera": {
        "Dimensions": "138.4 x 97.7 x 88.2 mm",
        "Weight": "738g"
    },
    "Sony Alpha a7 IV Mirrorless Camera": {
        "Dimensions": "133.9 x 96.3 x 84.4 mm",
        "Weight": "658g"
    }
}

# ============================================================================
# AGENT 1: IMAGE EXTRACTION AGENT
# Analyzes product images and extracts initial attributes
# ============================================================================

image_extraction_agent = agents.LlmAgent(
    name="ImageExtractionAgent",
    model=gemini_model,
    instruction="""You are a Product Attribute Analysis Expert for cameras.

Your task is to analyze the provided product image(s) and extract the following attributes:
{', '.join(ATTRIBUTES)}

**Special Instructions:**
1. For Dimensions: Look for any numbers with units (mm, cm) in the image. Format as "W x H x D mm" if found, otherwise null.
2. For Weight: Extract weight in grams (e.g., "738g"). Look for any packaging or specification labels.
3. For other attributes: Identify visible features, text, labels, or specifications in the image.
4. If an attribute is not visible or cannot be determined from the image, return null for that attribute.

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
    "attributes": {{
        "Color": "value or null",
        "Body Material": "value or null",
        "Dimensions": "W x H x D in mm or null",
        "Weight": "weight in grams or null",
        "Sensor Type": "value or null",
        "Display Type": "value or null",
        "Viewfinder Type": "value or null",
        "Battery Type": "value or null",
        "Memory Card Slot": "value or null",
        "USB Port Type": "value or null",
        "Hot Shoe Mount": "value or null",
        "Tripod Socket": "value or null",
        "Low Pass Filter": "value or null",
        "Auto White Balance": "value or null",
        "AE Lock Button": "value or null",
        "Shutter Release Type": "value or null",
        "Lens Mount": "value or null",
        "Connectivity Features": "value or null",
        "Video Capabilities": "value or null",
        "Autofocus System": "value or null"
    }},
    "product_description": "A detailed marketing description of the product based on the image",
    "confidence_score": "high/medium/low",
    "images_analyzed": 1,
    "extraction_notes": "Any important observations about the extraction"
}}

Be thorough but concise. Focus on accuracy over completeness.""",
    description="Extracts product attributes from camera images using vision analysis",
    output_key="extracted_attributes"  # Stores output in state['extracted_attributes']
)

# ============================================================================
# AGENT 2: MANUFACTURER SEARCH AGENT
# Searches for and extracts manufacturer specifications
# ============================================================================

manufacturer_search_agent = agents.LlmAgent(
    name="ManufacturerSearchAgent",
    model=gemini_model,
    instruction="""You are a Manufacturer Specification Research Agent.

**Context:**
Product Name: {product_name}
Already Extracted Attributes:
{extracted_attributes}

**Your Task:**
1. Analyze the previously extracted attributes above
2. Identify which attributes are missing or have null values
3. Generate 3-5 focused search queries to find manufacturer specifications for the missing attributes
4. Format each query to target official product specification pages (e.g., Canon, Sony official sites)

**Important:**
- Prioritize searches for: Dimensions, Weight, Sensor Type, Lens Mount, Battery Type
- Each query should be specific enough to find the manufacturer's official product page
- Include the official manufacturer domain in your search strategy (e.g., "site:canon.com", "site:sony.com")

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks):
{{
    "search_queries": [
        {{"query": "full search query 1", "priority": "high", "target_attributes": ["Dimensions", "Weight"]}},
        {{"query": "full search query 2", "priority": "high", "target_attributes": ["Sensor Type", "Lens Mount"]}},
        {{"query": "full search query 3", "priority": "medium", "target_attributes": ["Battery Type", "Memory Card Slot"]}}
    ],
    "search_strategy": "Brief explanation of your search approach",
    "target_websites": ["canon.com", "sony.com"],
    "research_focus": "The key attributes most important to find from manufacturer sources"
}}

Focus on generating queries that will retrieve official manufacturer specification sheets and product pages.""",
    description="Generates targeted search queries to find manufacturer specifications",
    output_key="search_queries"  # Stores output in state['search_queries']
)

# ============================================================================
# AGENT 3: ATTRIBUTE ENRICHMENT AGENT
# Enriches attributes with manufacturer data and finalizes results
# ============================================================================

attribute_enrichment_agent = agents.LlmAgent(
    name="AttributeEnrichmentAgent",
    model=gemini_model,
    instruction="""You are an Attribute Enrichment and Finalization Expert.

**Context:**
Product Name: {product_name}
Initial Extraction:
{extracted_attributes}

Search Queries Generated:
{search_queries}

Official Specs Available:
{official_specs_json}

**Your Task:**
1. Review the initially extracted attributes
2. Consider the search queries that were generated to find missing data
3. Apply any available official specifications from the OFFICIAL_SPECS_AVAILABLE section
4. Fill in null values with the most reliable information available
5. Provide a final, complete product profile

**Enrichment Rules:**
- Only fill attributes that were missing (null) from initial extraction
- Prioritize official manufacturer specs over other sources
- If a value remains unknown, keep it as null
- Ensure consistency across all attribute values
- Add confidence scores for each filled-in attribute

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks):
{{
    "product_name": "{product_name}",
    "attributes": {{
        "Color": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Body Material": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Dimensions": {{"value": "W x H x D in mm or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Weight": {{"value": "weight in grams or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Sensor Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Display Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Viewfinder Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Battery Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Memory Card Slot": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "USB Port Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Hot Shoe Mount": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Tripod Socket": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Low Pass Filter": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Auto White Balance": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "AE Lock Button": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Shutter Release Type": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Lens Mount": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Connectivity Features": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Video Capabilities": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}},
        "Autofocus System": {{"value": "value or null", "source": "image/official/inferred", "confidence": "high/medium/low"}}
    }},
    "product_description": "{product_description}",
    "enrichment_summary": {{
        "total_attributes": 20,
        "filled_attributes": "number of non-null values",
        "sources_used": ["image", "official_specs"],
        "high_confidence_count": "number of high confidence attributes"
    }},
    "final_status": "complete"
}}

Produce a comprehensive, accurate product profile ready for export.""",
    description="Enriches attributes and produces final product profile",
    output_key="final_product_profile"  # Stores output in state['final_product_profile']
)

# ============================================================================
# SEQUENTIAL AGENT ORCHESTRATOR
# Chains the three agents together in sequence
# ============================================================================

product_extraction_sequential_agent = agents.SequentialAgent(
    name="ProductExtractionPipeline",
    sub_agents=[
        image_extraction_agent,
        manufacturer_search_agent,
        attribute_enrichment_agent
    ],
    description="Sequential pipeline: Extract attributes from images -> Search for manufacturer specs -> Enrich and finalize attributes"
)

# Root agent for ADK compatibility
root_agent = product_extraction_sequential_agent

if __name__ == "__main__":
    print("ADK Sequential Agents Module")
    print(f"- Image Extraction Agent: {image_extraction_agent.name}")
    print(f"- Manufacturer Search Agent: {manufacturer_search_agent.name}")
    print(f"- Attribute Enrichment Agent: {attribute_enrichment_agent.name}")
    print(f"- Sequential Agent: {product_extraction_sequential_agent.name}")
    print("\nRoot agent ready for deployment")
