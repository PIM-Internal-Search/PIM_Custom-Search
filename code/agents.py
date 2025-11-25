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



# Product attributes to extract
ATTRIBUTES = [
    "Color", "Body Material", "Dimensions", "Weight", "Sensor Type",
    "Display Type", "Viewfinder Type", "Battery Type", "Memory Card Slot",
    "USB Port Type", "Hot Shoe Mount", "Tripod Socket", "Low Pass Filter",
    "Auto White Balance", "AE Lock Button", "Shutter Release Type",
    "Lens Mount", "Connectivity Features", "Video Capabilities", "Autofocus System"
]




def create_agents():
    """
    Factory function to create agents with fresh clients.
    This ensures that clients (like Gemini) are initialized within the current event loop context.
    """
    # Initialize Gemini model for ADK
    gemini_model = models.Gemini(api_key=GEMINI_API_KEY)

    # ============================================================================
    # AGENT 1: IMAGE EXTRACTION AGENT
    # Analyzes product images and extracts initial attributes
    # ============================================================================

    image_extraction_agent = agents.LlmAgent(
        name="ImageExtractionAgent",
        model=gemini_model,
        instruction=f"""You are an Expert Camera Product Analyst with deep knowledge of camera specifications.

Your PRIMARY GOAL: Extract or intelligently infer ALL {len(ATTRIBUTES)} attributes. Aim for 100% fill rate.

**Attributes to Extract:**
{', '.join(ATTRIBUTES)}

**CRITICAL INSTRUCTIONS:**

1. **VISIBLE ATTRIBUTES** - Extract from image:
   - Color, Body Material, Physical features (buttons, ports, mounts)
   - Display Type, Viewfinder Type, Hot Shoe Mount, Tripod Socket
   - USB Port Type, Memory Card Slot, Lens Mount
   - Any text/labels showing specs (Dimensions, Weight, Battery Type)

2. **INTELLIGENT INFERENCE** - For attributes not visible:
   - **Brand Specifics:**
     - "Canon EOS" → Infer: Lens Mount = "Canon EF/RF", Sensor Type = "Full-frame CMOS" or "APS-C CMOS"
     - "Sony Alpha" → Infer: Lens Mount = "Sony E-mount", Sensor Type = "Full-frame CMOS"
     - "Nikon Z" → Infer: Lens Mount = "Nikon Z mount"
     - "Fujifilm X" → Infer: Lens Mount = "Fujifilm X mount", Sensor Type = "APS-C X-Trans CMOS"
   - **Type Specifics:**
     - Mirrorless → Infer: Viewfinder Type = "Electronic (EVF)", Low Pass Filter = "Yes" (usually)
     - DSLR → Infer: Viewfinder Type = "Optical (OVF)"
     - Compact/Point-and-Shoot → Infer: Lens Mount = "Fixed Lens"
   - **Modern Standards (Post-2020):**
     - Auto White Balance = "Yes"
     - AE Lock Button = "Yes"
     - Connectivity Features = "Wi-Fi, Bluetooth, USB-C"
     - Video Capabilities = "4K video recording"
     - Tripod Socket = "1/4-inch standard thread"
     - Hot Shoe Mount = "Yes" (for interchangeable lens cameras)

3. **AVOID NULLS AT ALL COSTS:**
   - If you are 50% sure, INFER it and mark as "medium" confidence.
   - If you are unsure, provide a "Likely [value]" based on the camera class.
   - ONLY use null if the image is completely unrecognizable as a camera.

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks):
{{
    "attributes": {{
        "Color": "value",
        "Body Material": "value",
        "Dimensions": "W x H x D mm",
        "Weight": "weight in grams",
        "Sensor Type": "value",
        "Display Type": "value",
        "Viewfinder Type": "value",
        "Battery Type": "value",
        "Memory Card Slot": "value",
        "USB Port Type": "value",
        "Hot Shoe Mount": "value",
        "Tripod Socket": "value",
        "Low Pass Filter": "value",
        "Auto White Balance": "value",
        "AE Lock Button": "value",
        "Shutter Release Type": "value",
        "Lens Mount": "value",
        "Connectivity Features": "value",
        "Video Capabilities": "value",
        "Autofocus System": "value"
    }},
    "product_description": "2-3 compelling sentences for e-commerce",
    "confidence_score": "high/medium/low",
    "images_analyzed": 1,
    "extraction_notes": "What was extracted vs inferred"
}}

**TARGET: Fill ALL 20 attributes. Use your camera expertise to make intelligent inferences!**""",
        description="Extracts product attributes from camera images using vision analysis",
        output_key="extracted_attributes"  # Stores output in state['extracted_attributes']
    )

    # ============================================================================
    # AGENT 2: MANUFACTURER SEARCH AGENT
    # Searches for and extracts manufacturer specifications using Google CSE
    # ============================================================================

    # Import and create the Google Custom Search tool
    from google_search_tool import create_google_search_tool
    
    try:
        # create_google_search_tool() reads API credentials from environment variables
        google_search_tool = create_google_search_tool()
    except ValueError as e:
        print(f"[WARNING] Could not create Google Search tool: {e}")
        google_search_tool = None

    manufacturer_search_agent = agents.LlmAgent(
        name="ManufacturerSearchAgent",
        model=gemini_model,
        tools=[google_search_tool] if google_search_tool else [],
        instruction="""You are an Aggressive Specification Hunter with Google Custom Search access.

**Context:**
Product Name: {product_name}
Current Attributes:
{extracted_attributes}

**YOUR MISSION: Find specifications for EVERY missing or uncertain attribute!**

**Task:**
1. Identify ALL attributes that are null, uncertain, or could be improved
2. Execute 3-5 targeted Google searches using the google_custom_search tool
3. Extract EVERY possible specification from search results
4. Return comprehensive specifications

**Search Strategy - Execute ALL of these:**

Search 1: "{product_name} full specifications site:canon.com OR site:sony.com OR site:nikon.com"
Search 2: "{product_name} dimensions weight battery specifications"
Search 3: "{product_name} sensor lens mount connectivity features"
Search 4: "{product_name} technical specs datasheet PDF"
Search 5: "{product_name} review detailed specifications"

**FALLBACK SEARCH:**
If the exact model is not found, search for the **series** or **family** (e.g., "Canon EOS R series specs") to find likely shared attributes like Mount, Battery, or Connectivity.

**CRITICAL:**
- MUST use google_custom_search tool for EACH search above
- Extract EVERY spec mentioned in search results
- Look for: dimensions, weight, sensor, lens mount, battery, ports, video, autofocus
- Parse snippets carefully - specs are often in the snippet text

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks):
{{
    "searches_performed": [
        {{"query": "query 1", "results_found": 5, "useful": true}},
        {{"query": "query 2", "results_found": 5, "useful": true}}
    ],
    "specifications_found": {{
        "Dimensions": {{"value": "exact dimensions", "source": "url", "confidence": "high"}},
        "Weight": {{"value": "exact weight", "source": "url", "confidence": "high"}},
        "Sensor Type": {{"value": "sensor type", "source": "url", "confidence": "high"}},
        "Battery Type": {{"value": "battery model", "source": "url", "confidence": "high"}},
        "Lens Mount": {{"value": "mount type", "source": "url", "confidence": "high"}},
        "Video Capabilities": {{"value": "video specs", "source": "url", "confidence": "high"}},
        "Autofocus System": {{"value": "AF system", "source": "url", "confidence": "high"}},
        "Connectivity Features": {{"value": "connectivity", "source": "url", "confidence": "high"}},
        "Memory Card Slot": {{"value": "card type", "source": "url", "confidence": "high"}},
        "USB Port Type": {{"value": "USB type", "source": "url", "confidence": "high"}}
    }},
    "search_summary": "Found X specifications from Y sources",
    "missing_attributes": ["Only list if truly not found anywhere"]
}}

**TARGET: Find specifications for AT LEAST 10 attributes. Be aggressive and thorough!**""",
        description="Searches for manufacturer specifications using Google Custom Search API",
        output_key="search_results"  # Stores output in state['search_results']
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

Search Results from Web:
{search_results}

**YOUR MISSION: Achieve 100% attribute fill rate! NO NULLS ALLOWED.**

**Task:**
1. Review image-extracted attributes
2. Review web search specifications
3. **FILL EVERY SINGLE ATTRIBUTE** using this priority:
   - Priority 1: Official manufacturer specs from search results (highest confidence)
   - Priority 2: Image-extracted values
   - Priority 3: Intelligent inference based on product type/brand
   - Priority 4: **MANDATORY DEFAULTS** (See below) - Use these if all else fails.

**MANDATORY DEFAULTS (Use these instead of null):**
- **Color**: "Black" (Most common for cameras)
- **Body Material**: "Magnesium Alloy / Polycarbonate"
- **Dimensions**: "Not Specified" (Better than null, but try to infer "Standard DSLR size" etc.)
- **Weight**: "Not Specified"
- **Sensor Type**: "CMOS Sensor"
- **Display Type**: "LCD Touchscreen"
- **Viewfinder Type**: "Electronic Viewfinder (EVF)" (Safe bet for modern, Optical for DSLR)
- **Battery Type**: "Rechargeable Li-ion Battery"
- **Memory Card Slot**: "SD / SDHC / SDXC"
- **USB Port Type**: "USB Type-C" (Standard on modern cameras)
- **Hot Shoe Mount**: "Yes"
- **Tripod Socket**: "1/4-inch standard thread"
- **Low Pass Filter**: "Built-in"
- **Auto White Balance**: "Yes"
- **AE Lock Button**: "Yes"
- **Shutter Release Type**: "Electronic & Mechanical"
- **Lens Mount**: "Interchangeable Mount" (or "Fixed Lens" if compact)
- **Connectivity Features**: "Wi-Fi, Bluetooth"
- **Video Capabilities**: "Full HD / 4K Video"
- **Autofocus System**: "Phase Detection AF"

**Enrichment Rules:**
- **NEVER leave an attribute as null**.
- Manufacturer specs > Image extraction > Inference > Defaults.
- For missing specs, use your camera knowledge to infer:
  - Canon cameras → Canon EF/RF mount, LP-E6 battery series
  - Sony cameras → Sony E-mount, NP-FZ100 battery series
  - Mirrorless → Electronic viewfinder, typically lighter
  - Professional → 4K video, advanced AF, Wi-Fi/Bluetooth
- Confidence: "high" for manufacturer specs, "medium" for inference, "low" for defaults.

**Product Description Guidelines:**
- Write 2-3 compelling sentences that would appear on an e-commerce website.
- Highlight key features and benefits that appeal to photographers.
- Use persuasive, professional language.
- Focus on what makes this camera special and desirable.

**Output Format:**
Return ONLY valid JSON (no markdown, no code blocks):
{{
    "product_name": "{product_name}",
    "attributes": {{
        "Color": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Body Material": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Dimensions": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Weight": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Sensor Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Display Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Viewfinder Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Battery Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Memory Card Slot": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "USB Port Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Hot Shoe Mount": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Tripod Socket": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Low Pass Filter": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Auto White Balance": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "AE Lock Button": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Shutter Release Type": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Lens Mount": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Connectivity Features": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Video Capabilities": {{"value": "value", "source": "source", "confidence": "high/medium/low"}},
        "Autofocus System": {{"value": "value", "source": "source", "confidence": "high/medium/low"}}
    }},
    "product_description": "Write a compelling 2-3 sentence e-commerce description here",
    "enrichment_summary": {{
        "total_attributes": 20,
        "filled_attributes": 20,
        "sources_used": ["image", "search_results", "inference", "defaults"],
        "high_confidence_count": "number of high confidence attributes"
    }},
    "final_status": "complete"
}}

Produce a comprehensive, accurate product profile with compelling e-commerce copy ready for export.""",
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

    return product_extraction_sequential_agent

# Create a default instance for backward compatibility if needed, 
# but prefer using create_agents()
try:
    root_agent = create_agents()
except Exception:
    root_agent = None

if __name__ == "__main__":
    agent = create_agents()
    print("ADK Sequential Agents Module")
    print(f"- Sequential Agent: {agent.name}")
    print("\nRoot agent ready for deployment")

