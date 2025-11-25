# ADK Sequential Agents - Implementation Guide

## Overview

This guide explains the implementation of Google's Agent Development Kit (ADK) with Sequential Agents in the camera attribute extraction system.

## Key Concepts

### 1. Sequential Agents

**What is a SequentialAgent?**
- A workflow agent that executes sub-agents in a strict, deterministic order
- All sub-agents share the same `InvocationContext` and session state
- Data passes between agents via state key injection

**When to Use:**
- Pipelines with fixed execution order
- Multi-step processes where each step depends on the previous
- Deterministic workflows (no LLM decides the flow)

**Advantages over LLM-only agents:**
- No token wasted on routing decisions
- Guaranteed execution order
- Clear, predictable flow
- Easier debugging and monitoring

### 2. State Key Injection

**How it Works:**
```python
# Agent 1 generates data and stores it with an output_key
agent1 = LlmAgent(
    name="Stage1",
    output_key="stage1_result"  # ← Stores output here
)

# Agent 2 retrieves it using {stage1_result} in instruction
agent2 = LlmAgent(
    instruction="""
    Previous result: {stage1_result}
    Now do the next step...
    """,
    output_key="stage2_result"
)
```

**Benefits:**
- Automatic context passing
- No manual state management
- Clean, readable code
- Built-in type safety

## Implementation Details

### Agent 1: Image Extraction Agent

**Purpose:** Extract attributes from images

**Input:**
- Product image (base64 encoded)
- List of attributes to extract

**Processing:**
1. Encode image to base64
2. Send to Gemini vision model
3. Parse JSON response
4. Extract attributes with confidence scores

**Output (stored in `extracted_attributes`):**
```json
{
  "attributes": {
    "Color": "Black",
    "Weight": "738g",
    ...
  },
  "product_description": "...",
  "confidence_score": "high"
}
```

**Key Instruction Points:**
- Structured JSON output required
- Special handling for Dimensions and Weight
- Confidence scoring for accuracy tracking
- Null values for unknown attributes

### Agent 2: Manufacturer Search Agent

**Purpose:** Generate targeted search queries for missing specs

**Input:**
- Product name (from context)
- Previously extracted attributes (from `{extracted_attributes}`)
- List of official domains to search

**Processing:**
1. Identify missing/incomplete attributes
2. Generate 3-5 focused search queries
3. Prioritize important attributes
4. Target official manufacturer domains

**Output (stored in `search_queries`):**
```json
{
  "search_queries": [
    {
      "query": "Canon EOS R5 Mark II official specifications",
      "priority": "high",
      "target_attributes": ["Dimensions", "Weight"]
    }
  ],
  "target_websites": ["canon.com", "sony.com"]
}
```

**Key Design:**
- Doesn't actually perform searches (that's the Enrichment Agent's job)
- Focuses on query generation strategy
- Plans research approach
- Identifies key information to find

### Agent 3: Attribute Enrichment Agent

**Purpose:** Enrich attributes with official data and produce final profile

**Input:**
- Original extracted attributes (from `{extracted_attributes}`)
- Search queries (from `{search_queries}`)
- Product name
- Official specs (if available)

**Processing:**
1. Review initial extraction
2. Apply official specifications
3. Fill in missing attributes
4. Add confidence scores
5. Compile final profile

**Output (stored in `final_product_profile`):**
```json
{
  "product_name": "...",
  "attributes": {
    "Dimensions": {
      "value": "138.4 x 97.7 x 88.2 mm",
      "source": "official",
      "confidence": "high"
    }
  },
  "enrichment_summary": {
    "filled_attributes": 18,
    "sources_used": ["image", "official_specs"],
    "high_confidence_count": 15
  }
}
```

**Key Design:**
- Consolidates information from multiple sources
- Maintains confidence metadata
- Produces market-ready data
- Prioritizes official sources

## Data Flow Architecture

### State Namespace

ADK maintains a shared state namespace where agents can:
- **Store:** Using `output_key`
- **Retrieve:** Using `{key_name}` in instructions

```
Session State:
├── extracted_attributes (Agent 1 output)
├── search_queries (Agent 2 output)
└── final_product_profile (Agent 3 output)
```

### Message Passing Example

```
Step 1: Image Extraction Agent
   Input: Product images
   Process: Vision analysis
   Output: extracted_attributes = {...}
   ↓
   (State updated in shared context)
   ↓

Step 2: Manufacturer Search Agent
   Input: product_name + {extracted_attributes}
   Process: Strategy generation
   Output: search_queries = {...}
   ↓
   (State updated in shared context)
   ↓

Step 3: Enrichment Agent
   Input: product_name + {extracted_attributes} + {search_queries}
   Process: Consolidation
   Output: final_product_profile = {...}
```

## Implementation Best Practices

### 1. Prompt Engineering

**Use Clear, Structured Instructions:**
```python
instruction="""You are a [Role].
Your task is to [Specific Task].

**Input:**
- [What you receive]

**Processing Rules:**
1. [Rule 1]
2. [Rule 2]

**Output Format:**
Return ONLY valid JSON (no markdown):
{...}
"""
```

### 2. JSON Reliability

**Always specify:**
- Exact JSON structure expected
- No markdown code blocks
- Valid JSON only
- Handle null values explicitly

```python
# BAD ❌
instruction="Extract attributes and return JSON"

# GOOD ✅
instruction="""Return ONLY valid JSON (no markdown, no code blocks):
{
  "attributes": {...},
  "confidence": "high/medium/low"
}
"""
```

### 3. State Key Naming

**Use descriptive names:**
```python
# BAD ❌
output_key="result"

# GOOD ✅
output_key="extracted_attributes"
output_key="search_queries"
output_key="final_product_profile"
```

### 4. Error Handling

**Implement graceful fallbacks:**
```python
def parse_agent_output(result):
    try:
        # Try to parse JSON
        return json.loads(result)
    except:
        # Fallback to structured response
        return {
            "status": "error",
            "message": result,
            "partial_result": {}
        }
```

## Extending the Pipeline

### Adding a New Agent

**Step 1: Define the new agent**
```python
new_agent = agents.LlmAgent(
    name="ValidatorAgent",
    model=gemini_model,
    instruction="""You are a data validator.
    Review the extracted attributes:
    {final_product_profile}
    
    Check for consistency and completeness...
    """,
    output_key="validation_result"
)
```

**Step 2: Add to sequence**
```python
root_agent = agents.SequentialAgent(
    name="ExtendedPipeline",
    sub_agents=[
        image_extraction_agent,
        manufacturer_search_agent,
        attribute_enrichment_agent,
        new_agent  # ← Add here
    ]
)
```

### Creating Conditional Logic

Use `ConditionalAgent` for branching:
```python
# If high confidence, skip enrichment
# If low confidence, search for more data

from google.adk import agents

skip_enrichment_condition = lambda ctx: ctx.get("confidence") == "high"

conditional_agent = agents.ConditionalAgent(
    condition=skip_enrichment_condition,
    if_true=image_extraction_agent,
    if_false=sequential_pipeline
)
```

### Parallel Processing

Use `ParallelAgent` for concurrent operations:
```python
# Extract multiple attributes simultaneously

parallel_agent = agents.ParallelAgent(
    sub_agents=[
        dimension_extractor,
        weight_extractor,
        material_extractor
    ]
)
```

## Deployment Considerations

### 1. API Key Management

**Development:**
```bash
export GEMINI_API_KEY="your-key"
```

**Production (Cloud Run):**
```python
from google.cloud import secretmanager

def access_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={...})
    return response.payload.data.decode('UTF-8')

GEMINI_API_KEY = access_secret("gemini-api-key")
```

### 2. Rate Limiting

Implement backoff for API calls:
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_agent(product_name, folder):
    return await pipeline.run_extraction_pipeline(...)
```

### 3. Monitoring & Logging

Track agent execution:
```python
import logging

logger = logging.getLogger(__name__)

async def run_pipeline(product_name, folder):
    logger.info(f"Starting extraction for {product_name}")
    
    try:
        result = await pipeline.run_extraction_pipeline(product_name, folder)
        logger.info(f"Completed: {product_name}")
        return result
    except Exception as e:
        logger.error(f"Failed {product_name}: {str(e)}")
        raise
```

## Testing

### Unit Tests

```python
import unittest

class TestImageExtractionAgent(unittest.TestCase):
    def test_valid_image_extraction(self):
        result = pipeline.run_extraction_pipeline(
            "Test Product",
            "test_images/"
        )
        
        self.assertIn("attributes", result)
        self.assertIn("confidence_score", result)
        self.assertIsNotNone(result["product_description"])
    
    def test_missing_image_handling(self):
        result = pipeline.run_extraction_pipeline(
            "Test Product",
            "empty_folder/"
        )
        
        self.assertIn("error", result)
```

### Integration Tests

```python
def test_full_pipeline():
    results = pipeline.process_batch("test_products/")
    
    assert len(results) > 0
    assert all("product_name" in r for r in results)
    assert sum(1 for r in results if "error" not in r) > 0
```

## Troubleshooting

### Issue: State Key Not Found

**Symptom:** KeyError when accessing `{attribute_name}`

**Solution:**
1. Check output_key in previous agent
2. Verify attribute name matches exactly
3. Ensure agent completed successfully

```python
# Debug: Print available state keys
print(context.get_state().keys())
```

### Issue: JSON Parsing Fails

**Symptom:** "Unable to parse JSON response"

**Solution:**
1. Update instruction to be more specific
2. Remove markdown requirements
3. Add fallback parsing logic

### Issue: Timeout or Rate Limit

**Symptom:** "API request timed out" or "429 Too Many Requests"

**Solution:**
1. Add retry logic with exponential backoff
2. Reduce batch size
3. Increase timeout values
4. Check API quota and limits

## Performance Optimization

### 1. Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_product(product_name):
    return pipeline.run_extraction_pipeline(product_name, folder)
```

### 2. Batch Processing

```python
# Process multiple products efficiently
results = pipeline.process_batch(
    base_folder,
    max_concurrent=5  # Limit concurrent requests
)
```

### 3. Result Compression

```python
import gzip

compressed = gzip.compress(json.dumps(results).encode())
with open("results.json.gz", "wb") as f:
    f.write(compressed)
```

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Sequential Agents Guide](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)
- [Gemini API Reference](https://ai.google.dev/api/rest/google.ai.generativelanguage.v1/models)
- [State Management](https://google.github.io/adk-docs/sessions/state/)

---

Last Updated: November 2025
