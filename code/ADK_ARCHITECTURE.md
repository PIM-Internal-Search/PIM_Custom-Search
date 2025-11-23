"""
ADK SEQUENTIAL AGENTS ARCHITECTURE DOCUMENTATION

This document describes the refactored codebase implementing Google's Agent Development Kit (ADK)
with Sequential Agents for product attribute extraction.
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

## Sequential Agent Pipeline

The application now uses Google's Agent Development Kit (ADK) with Sequential Agents to create
a deterministic, ordered execution pipeline for product attribute extraction.

### Three-Stage Pipeline

1. **Image Extraction Agent** (Stage 1)
   - Analyzes product images using Gemini 2.0 Flash vision capabilities
   - Extracts visible attributes (Color, Dimensions, Weight, Sensor Type, etc.)
   - Outputs: Extracted attributes, product description, confidence scores

2. **Manufacturer Search Agent** (Stage 2)
   - Receives output from Stage 1
   - Analyzes which attributes are missing or incomplete
   - Generates targeted search queries to find manufacturer specifications
   - Strategy: Prioritizes official manufacturer domains (canon.com, sony.com)
   - Outputs: Search queries with priority levels and target websites

3. **Attribute Enrichment Agent** (Stage 3)
   - Receives both original extraction and search query results
   - Applies official specifications from known sources
   - Enriches missing attributes with manufacturer data
   - Produces final, complete product profile with confidence scores
   - Outputs: Complete product profile with all attributes filled

## Sequential Execution Flow

```
Input: Product Name + Images
    ↓
[Stage 1: Image Extraction]
    ↓
[State: extracted_attributes]
    ↓
[Stage 2: Manufacturer Search]
    ↓
[State: search_queries]
    ↓
[Stage 3: Attribute Enrichment]
    ↓
Output: final_product_profile
```

# ============================================================================
# FILE STRUCTURE
# ============================================================================

## Core Modules

### agents.py
- **Purpose**: Defines the three LLM agents and the sequential agent orchestrator
- **Key Components**:
  - `image_extraction_agent`: LlmAgent for vision-based attribute extraction
  - `manufacturer_search_agent`: LlmAgent for generating search queries
  - `attribute_enrichment_agent`: LlmAgent for enriching and finalizing attributes
  - `product_extraction_sequential_agent`: SequentialAgent that chains all three
  - `root_agent`: Export point for ADK compatibility

### main.py
- **Purpose**: Entry point and pipeline orchestration
- **Key Classes**:
  - `ProductExtractionPipeline`: Main pipeline manager
    - `run_extraction_pipeline()`: Async method to process a single product
    - `process_batch_async()`: Async batch processing
    - `get_pipeline_report()`: Generate execution statistics

### batch_processor.py
- **Purpose**: High-level batch processing and export utilities
- **Key Classes**:
  - `BatchProcessor`: Orchestrates batch processing and result export
    - `process_directory()`: Process all products in a directory
    - `export_results_to_json()`: Export to JSON format
    - `export_results_to_csv()`: Export to CSV format
    - `generate_summary_report()`: Create comprehensive reports

### app.py
- **Purpose**: Streamlit web interface for the ADK pipeline
- **Features**:
  - Folder path or ZIP file input
  - Real-time progress tracking
  - Pipeline execution report
  - Result visualization with images and attributes
  - JSON and CSV export

## Legacy Modules (Kept for Reference)

### extractor.py
- Original attribute extraction logic
- Kept for reference; new pipeline uses LLM agents instead

### agent.py (Old)
- Original ProductExtractionAgent class
- Kept for reference; replaced by ADK sequential agents

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

## State Key Injection

ADK's SequentialAgent uses state key injection to pass data between agents:

```python
# Agent 1 stores result with output_key
output_key="extracted_attributes"

# Agent 2 retrieves from state using {extracted_attributes} in instruction
instruction="""
Already Extracted Attributes:
{extracted_attributes}
"""
```

## Data Flow Between Agents

1. **Agent 1 → Agent 2**:
   - State Key: `extracted_attributes`
   - Data: Initial attribute extraction with confidence scores

2. **Agent 2 → Agent 3**:
   - State Key: `search_queries`
   - Data: Targeted search queries for missing attributes

3. **Agent 3 Output**:
   - State Key: `final_product_profile`
   - Data: Complete, enriched product profile

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

## 1. Using the Streamlit Web Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# In browser: http://localhost:8501
# - Upload folder path or ZIP file
# - Click "Start Extraction Pipeline"
# - Download results as JSON or CSV
```

## 2. Using the Main Module (CLI)

```bash
# Single product processing
python main.py "/path/to/product_folder"

# Batch processing
python main.py "/path/to/raw_images" --batch
```

## 3. Using the Batch Processor

```bash
# Process directory and export results
python batch_processor.py "./raw_images" "./output"

# Generates:
# - extraction_results_<timestamp>.json
# - extraction_results_<timestamp>.csv
# - summary_report_<timestamp>.json
```

## 4. Programmatic Usage

```python
from main import ProductExtractionPipeline
import asyncio

# Initialize pipeline
pipeline = ProductExtractionPipeline()

# Single product
result = asyncio.run(
    pipeline.run_extraction_pipeline(
        product_name="Canon EOS R5 Mark II",
        product_folder="/path/to/product_images"
    )
)

# Batch processing
results = pipeline.process_batch("/path/to/raw_images")

# Get report
report = pipeline.get_pipeline_report()
```

# ============================================================================
# PRODUCT ATTRIBUTES
# ============================================================================

The system extracts 20 key camera attributes:

1. Color - Physical body color
2. Body Material - Material composition (magnesium, polycarbonate, etc.)
3. Dimensions - Physical dimensions in mm
4. Weight - Weight in grams
5. Sensor Type - Camera sensor type (Full Frame, APS-C, etc.)
6. Display Type - LCD, OLED, touchscreen, etc.
7. Viewfinder Type - Electronic or optical
8. Battery Type - Battery model/type
9. Memory Card Slot - SD, CFexpress, XQD, etc.
10. USB Port Type - USB Type-C, micro-USB, etc.
11. Hot Shoe Mount - Presence/type of hot shoe
12. Tripod Socket - Presence/type of tripod mount
13. Low Pass Filter - Presence of low-pass filter
14. Auto White Balance - AWB capabilities
15. AE Lock Button - Presence/features of AE lock
16. Shutter Release Type - Shutter release mechanism
17. Lens Mount - RF Mount, E-Mount, EF Mount, Z Mount, etc.
18. Connectivity Features - Wi-Fi, Bluetooth, NFC, etc.
19. Video Capabilities - 4K, 8K, frame rates, etc.
20. Autofocus System - Dual Pixel, Phase Detection, Face Detection, etc.

# ============================================================================
# OUTPUT FORMAT
# ============================================================================

## Product Profile JSON

```json
{
  "product_name": "Canon EOS R5 Mark II Mirrorless Camera",
  "image_count": 3,
  "attributes": {
    "Color": "Black",
    "Body Material": "Magnesium alloy",
    "Dimensions": "138.4 x 97.7 x 88.2 mm",
    "Weight": "738g",
    "Sensor Type": "Full Frame CMOS",
    ...
  },
  "product_description": "Professional mirrorless camera...",
  "enrichment_summary": {
    "total_attributes": 20,
    "filled_attributes": 18,
    "sources_used": ["image", "official_specs"],
    "high_confidence_count": 15
  },
  "agent_metadata": {
    "pipeline_status": "success",
    "images_processed": 3,
    "stages_completed": 3
  }
}
```

## Batch Summary Report

```json
{
  "timestamp": "2025-11-22T10:30:00",
  "total_products": 2,
  "successful": 2,
  "failed": 0,
  "success_rate": "100%",
  "total_images_processed": 5,
  "attribute_completion_rates": {
    "Dimensions": {
      "completion_rate": "100%",
      "filled": 2,
      "total": 2
    },
    ...
  }
}
```

# ============================================================================
# ADVANTAGES OF ADK SEQUENTIAL AGENTS
# ============================================================================

1. **Deterministic Execution**: Agents execute in fixed, strict order
2. **State Sharing**: All agents share the same InvocationContext for easy data passing
3. **Modular Design**: Each agent has a single responsibility
4. **Scalability**: Easy to add or modify agents without affecting others
5. **Error Handling**: Built-in error tracking and reporting
6. **Type Safety**: Structured input/output with defined schemas
7. **Observability**: Clear execution flow and logging
8. **Reusability**: Each agent can be used independently if needed

# ============================================================================
# MIGRATION FROM LEGACY CODE
# ============================================================================

## What Changed

**Before (Legacy Code)**:
- Single ProductExtractionAgent class
- Linear attribute extraction with search
- Manual enrichment logic
- No clear separation of concerns

**After (ADK Architecture)**:
- Three specialized LLM agents
- Sequential execution pipeline
- State-managed data flow
- Clear single responsibility for each agent

## Backward Compatibility

- Legacy modules (extractor.py, agent.py) are kept but not used
- New code is independent and doesn't rely on legacy code
- Can be removed in future cleanup

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

Required:
- `GEMINI_API_KEY`: Google Generative AI API key

Optional:
- `GOOGLE_CSE_API_KEY`: Google Custom Search API key (for enrichment)
- `GOOGLE_CSE_CX`: Google Custom Search engine ID

# ============================================================================
# REQUIREMENTS
# ============================================================================

Install dependencies:
```bash
pip install -r requirements.txt
```

Key packages:
- google-adk-python >= 0.1.0
- google-generativeai >= 0.3.0
- streamlit >= 1.0.0
- requests >= 2.28.0

# ============================================================================
# FUTURE ENHANCEMENTS
# ============================================================================

1. **Parallel Agents**: Use ParallelAgent for concurrent attribute extraction
2. **Loop Agents**: Use LoopAgent to retry failed extractions
3. **Custom Tools**: Add specialized tools for web scraping or database lookup
4. **Caching**: Implement result caching to avoid re-processing
5. **Advanced Routing**: Use ConditionalAgent to route based on product type
6. **Multi-language Support**: Extend agents to handle products in different languages
7. **Quality Scoring**: Add confidence scoring and quality metrics
8. **Feedback Loop**: Implement user feedback to improve extraction accuracy

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

## Issue: "No images found in product folder"
- Ensure images are in supported formats (.jpg, .jpeg, .png, .gif, .webp)
- Check folder permissions

## Issue: "API key not found"
- Set GEMINI_API_KEY environment variable
- Verify API key is valid in Google Cloud Console

## Issue: Streamlit not starting
- Check if port 8501 is available
- Try: streamlit run app.py --server.port 8502

## Issue: Slow processing
- ADK agents make API calls which may take time
- Check internet connectivity
- Verify Gemini API quota

# ============================================================================
"""

# CODE EXAMPLES FOR REFERENCE

print(__doc__)

# Example 1: Single Product Processing
"""
from main import ProductExtractionPipeline
import asyncio

pipeline = ProductExtractionPipeline()
result = asyncio.run(
    pipeline.run_extraction_pipeline(
        "Canon EOS R5 Mark II Mirrorless Camera",
        "./raw_images/Canon EOS R5 Mark II Mirrorless Camera"
    )
)
print(result)
"""

# Example 2: Batch Processing
"""
from batch_processor import process_and_export

output_files = process_and_export(
    base_folder="./raw_images",
    output_dir="./output",
    export_json=True,
    export_csv=True,
    save_report=True
)

print("Generated files:", output_files)
"""

# Example 3: Custom Processing
"""
from batch_processor import BatchProcessor

processor = BatchProcessor(output_dir="./results")
results = processor.process_directory("./raw_images")

# Generate reports
report = processor.generate_summary_report(results)
processor.print_report(report)

# Export
processor.export_results_to_json(results, "custom_results.json")
processor.export_results_to_csv(results, "custom_results.csv")
"""
