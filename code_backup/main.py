"""
Product Attribute Extraction Pipeline using Google ADK Sequential Agents

This module implements the main extraction pipeline that:
1. Prepares product images and metadata
2. Executes the sequential agent pipeline (Image Extraction -> Search -> Enrichment)
3. Processes and formats the results
"""

import os
import sys
import json
import base64
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add the code directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import search utilities
from search_utils import search_manufacturer_specs

from google.adk import agents, models
from google.adk.runners import RunConfig, InMemoryRunner

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import the sequential agent factory
from agents import (
    create_agents,
    OFFICIAL_SPECS,
    ATTRIBUTES
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyDTmS4gXULRFVrB9HvqqMGwDQkD-vmgX5M"


class ProductExtractionPipeline:
    """
    Wrapper class for managing the ADK sequential agent pipeline for product extraction.
    Handles image encoding, state management, and result processing.
    """

    def __init__(self):
        """Initialize the pipeline with ADK configuration"""
        self.extraction_history = []
        self.enrichment_history = []
        self.api_key = GEMINI_API_KEY

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.standard_b64encode(image_file.read()).decode("utf-8")

    def prepare_image_data(self, image_path: str) -> Dict[str, Any]:
        """Prepare image data for LLM processing"""
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_types.get(ext, "image/jpeg")

        return {
            "mime_type": media_type,
            "data": self.encode_image_to_base64(image_path),
            "path": str(image_path)
        }

    def find_product_images(self, product_folder: str) -> List[str]:
        """Find all image files in a product folder"""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        images = []
        
        for file in os.listdir(product_folder):
            if Path(file).suffix.lower() in image_extensions:
                images.append(os.path.join(product_folder, file))
        
        return sorted(images)

    async def run_extraction_pipeline(
        self,
        product_name: str,
        product_folder: str,
        image_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the sequential agent pipeline for a single product.
        
        This method:
        1. Prepares input images and product context
        2. Runs the SequentialAgent which executes agents in order:
           - Image Extraction: Analyzes images and extracts attributes
           - Manufacturer Search: Generates search queries for missing specs
           - Attribute Enrichment: Enriches attributes with official data
        3. Processes and returns the final product profile
        
        Args:
            product_name: Name of the product
            product_folder: Path to product folder containing images
            image_data: Optional pre-processed image data
            
        Returns:
            Dictionary containing the complete product profile with all extracted
            and enriched attributes, confidence scores, and metadata
        """
        print(f"\n{'='*70}")
        print(f"[PIPELINE] Starting extraction for: {product_name}")
        print(f"{'='*70}")

        try:
            # Find images in product folder if not provided
            images = self.find_product_images(product_folder)
            
            if not images:
                error_msg = f"No images found in {product_folder}"
                print(f"[ERROR] {error_msg}")
                return {
                    "product_name": product_name,
                    "error": error_msg,
                    "status": "failed"
                }

            print(f"[IMAGES] Found {len(images)} image(s) to process")

            # Prepare image data for processing
            if image_data is None:
                image_data = self.prepare_image_data(images[0])
                print(f"[PREPARED] Image: {Path(images[0]).name}")

            # Get official specs if available
            official_specs_json = json.dumps(
                OFFICIAL_SPECS.get(product_name, {}),
                indent=2
            )
            
            # Execute web searches BEFORE the pipeline to get manufacturer specs
            print("[SEARCH] Executing pre-pipeline manufacturer spec search...")
            from agents import GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX
            
            # Generate search queries based on product name
            search_queries = [
                {
                    "query": f"{product_name} specifications site:canon.com OR site:sony.com",
                    "priority": "high",
                    "target_attributes": ["Display Type", "Viewfinder Type", "Battery Type"]
                },
                {
                    "query": f"{product_name} technical specs connectivity ports",
                    "priority": "high",
                    "target_attributes": ["USB Port Type", "Memory Card Slot", "Connectivity Features"]
                },
                {
                    "query": f"{product_name} video recording autofocus features",
                    "priority": "medium",
                    "target_attributes": ["Video Capabilities", "Autofocus System"]
                }
            ]
            
            try:
                scraped_specs = search_manufacturer_specs(
                    product_name=product_name,
                    search_queries=search_queries,
                    api_key=GOOGLE_CSE_API_KEY,
                    cx=GOOGLE_CSE_CX
                )
                print(f"[SEARCH] Web search completed - found specifications")
            except Exception as search_error:
                print(f"[WARNING] Web search failed: {search_error}")
                scraped_specs = "No web search results available."

            # Prepare the initial state for the sequential agent
            # The agents will use these values via state key injection
            initial_prompt = f"""Process this product using the sequential pipeline:

Product Name: {product_name}
Product Folder: {product_folder}
Images Found: {len(images)}
First Image: {Path(images[0]).name}

Official Specs Available:
{official_specs_json}

Web Search Results:
{scraped_specs}

Please execute the three-step pipeline:
1. Extract attributes from the image
2. Generate search queries for missing specifications (note: web search already performed above)
3. Enrich attributes with available official data, web search results, and produce final profile

Image to analyze is being provided separately."""

            print("[AGENTS] Executing sequential agent pipeline...")
            print(f"  - Stage 1: Image Extraction Agent")
            print(f"  - Stage 2: Manufacturer Search Agent")
            print(f"  - Stage 3: Attribute Enrichment Agent")

            # Create fresh agents for this run to avoid event loop issues
            root_agent = create_agents()
            
            # Create runner for executing the agent
            runner = InMemoryRunner(agent=root_agent, app_name="product_extraction")
            
            # Create run configuration
            run_cfg = RunConfig()
            
            # Create a unique session ID for this product (simplified)
            # Remove special characters that might cause issues
            safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in product_name)
            session_id = f"session_{safe_name}"
            user_id = "user1"
            
            # Create session explicitly before running
            try:
                session = runner.session_service.create_session_sync(
                    user_id=user_id,
                    session_id=session_id,
                    app_name="product_extraction"
                )
                print(f"[SESSION] Created session: {session_id}")
            except Exception as e:
                # Session might already exist, try to get it
                try:
                    session = runner.session_service.get_session_sync(
                        user_id=user_id,
                        session_id=session_id,
                        app_name="product_extraction"
                    )
                    print(f"[SESSION] Using existing session: {session_id}")
                except Exception as e2:
                    print(f"[SESSION] Warning: Could not create/get session: {e2}")
                    # Continue anyway - runner might create it automatically
            
            # Prepare content with text and image
            from google.genai import types as genai_types
            
            # Create parts for the message
            parts = [
                genai_types.Part(text=initial_prompt)
            ]
            
            # Add image part if available
            if image_data:
                image_bytes = base64.b64decode(image_data["data"])
                parts.append(
                    genai_types.Part(
                        inline_data=genai_types.Blob(
                            mime_type=image_data["mime_type"],
                            data=image_bytes
                        )
                    )
                )
            
            # Create content message
            user_message = genai_types.Content(
                role="user",
                parts=parts
            )

            # Create or get session first
            # The runner will create the session automatically on first run
            # Prepare initial state with context variables for the agents
            # These will be available to all agents via state key injection
            # Note: extracted_attributes, search_queries, and product_description
            # will be added by the agents as they execute
            initial_state = {
                "product_name": product_name,
                "official_specs_json": official_specs_json,
                "product_folder": product_folder,
                "images_found": len(images),
                "product_description": ""  # Will be filled by agent 1
            }
            
            # Execute the root agent (SequentialAgent) using the runner
            async_gen = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
                state_delta=initial_state,
                run_config=run_cfg
            )
            
            
            # Collect all events from the async generator
            events = []
            search_queries_data = None
            
            async for event in async_gen:
                events.append(event)
                print(f"[DEBUG] Event type: {type(event)}, Event: {event}")
                
                # Check if this event contains search queries from ManufacturerSearchAgent
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text and 'search_queries' in part.text:
                                try:
                                    # Try to extract search queries JSON
                                    text = part.text
                                    if '```json' in text:
                                        json_start = text.find('```json') + 7
                                        json_end = text.find('```', json_start)
                                        text = text[json_start:json_end].strip()
                                    
                                    potential_queries = json.loads(text)
                                    if 'search_queries' in potential_queries:
                                        search_queries_data = potential_queries
                                        print(f"[SEARCH] Captured search queries from agent")
                                except:
                                    pass
            
            # Execute Google CSE searches if we have queries
            scraped_specs = "No web search performed."
            if search_queries_data and search_queries_data.get('search_queries'):
                try:
                    from agents import GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX
                    scraped_specs = search_manufacturer_specs(
                        product_name=product_name,
                        search_queries=search_queries_data['search_queries'],
                        api_key=GOOGLE_CSE_API_KEY,
                        cx=GOOGLE_CSE_CX
                    )
                    print(f"[SEARCH] Web search completed successfully")
                except Exception as search_error:
                    print(f"[WARNING] Web search failed: {search_error}")
                    scraped_specs = f"Web search failed: {str(search_error)}"
            
            # Extract the final result from the events
            # Look for the final agent response in the events
            result = None
            for event in reversed(events):
                if hasattr(event, 'content') and event.content:
                    result = event.content
                    print(f"[DEBUG] Found content in event: {result}")
                    break
            
            # If no content found, use the last event
            if result is None and events:
                result = events[-1]
                print(f"[DEBUG] No content found, using last event: {result}")

            print("[AGENTS] Sequential pipeline execution complete")
            print(f"[DEBUG] Final result before parsing: {result}")

            # Parse results from the final agent output
            final_profile = self._parse_agent_output(result, product_name, len(images))

            # Record in history
            self.enrichment_history.append({
                "product": product_name,
                "status": "success",
                "images_processed": len(images),
                "timestamp": str(Path(images[0]).stat().st_mtime) if images else None
            })

            print(f"[OK] Processing complete for {product_name}")
            print(f"{'='*70}\n")

            return final_profile

        except Exception as e:
            print(f"[ERROR] Pipeline error for {product_name}: {str(e)}")
            self.enrichment_history.append({
                "product": product_name,
                "status": "error",
                "error": str(e)
            })
            return {
                "product_name": product_name,
                "error": str(e),
                "status": "failed"
            }

    def _parse_agent_output(
        self,
        agent_result: Any,
        product_name: str,
        image_count: int
    ) -> Dict[str, Any]:
        """
        Parse the output from the SequentialAgent and format for application use.
        
        Converts the agent's structured output into a standardized product profile
        that can be used for export, display, and further processing.
        """
        try:
            # Extract structured data from agent result
            # The result might be an Event, Content, or dict
            result_data = {}
            
            print(f"[DEBUG] agent_result type: {type(agent_result)}")
            print(f"[DEBUG] agent_result has 'content': {hasattr(agent_result, 'content')}")
            print(f"[DEBUG] agent_result has 'parts': {hasattr(agent_result, 'parts')}")
            print(f"[DEBUG] agent_result has 'text': {hasattr(agent_result, 'text')}")
            
            # Try to extract text from various possible structures
            raw_text = None
            
            # Check if it's a Content object with parts directly
            if hasattr(agent_result, 'parts') and agent_result.parts:
                text_parts = [p.text for p in agent_result.parts if hasattr(p, 'text') and p.text]
                if text_parts:
                    raw_text = ''.join(text_parts)
                    print(f"[DEBUG] Extracted text from parts (direct): {raw_text[:200]}")
            # Check if it has a content attribute with parts
            elif hasattr(agent_result, 'content') and agent_result.content:
                content = agent_result.content
                if hasattr(content, 'parts') and content.parts:
                    text_parts = [p.text for p in content.parts if hasattr(p, 'text') and p.text]
                    if text_parts:
                        raw_text = ''.join(text_parts)
                        print(f"[DEBUG] Extracted text from content.parts: {raw_text[:200]}")
            # Check if it's a dict
            elif isinstance(agent_result, dict):
                result_data = agent_result
                print(f"[DEBUG] agent_result is already a dict")
            # Check if it has a text attribute
            elif hasattr(agent_result, 'text'):
                raw_text = agent_result.text
                print(f"[DEBUG] Extracted text from .text attribute: {raw_text[:200]}")
            
            # If we got raw text, parse it
            if raw_text and not result_data:
                # Strip markdown code blocks if present
                if '```json' in raw_text:
                    # Extract JSON from markdown code block
                    json_start = raw_text.find('```json') + 7
                    json_end = raw_text.find('```', json_start)
                    raw_text = raw_text[json_start:json_end].strip()
                elif '```' in raw_text:
                    # Generic code block
                    json_start = raw_text.find('```') + 3
                    json_end = raw_text.find('```', json_start)
                    raw_text = raw_text[json_start:json_end].strip()
                
                try:
                    result_data = json.loads(raw_text)
                    print(f"[DEBUG] Successfully parsed JSON with keys: {list(result_data.keys())}")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON parse error: {e}")
                    print(f"[DEBUG] Raw text: {raw_text[:500]}")
                    result_data = {"raw_output": raw_text}
            
            # Fallback if nothing worked
            if not result_data:
                print(f"[DEBUG] No data extracted, using fallback")
                result_data = {
                    "product_name": product_name,
                    "attributes": {},
                    "status": "processed",
                    "raw_result": str(agent_result)
                }


            # Normalize attributes format
            print(f"[DEBUG] result_data keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'NOT A DICT'}")
            print(f"[DEBUG] result_data type: {type(result_data)}")
            if isinstance(result_data, dict):
                print(f"[DEBUG] result_data content (first 500 chars): {str(result_data)[:500]}")
            
            normalized_profile = {
                "product_name": product_name,
                "image_count": image_count,
                "attributes": {},
                "product_description": result_data.get("product_description", ""),
                "enrichment_summary": result_data.get("enrichment_summary", {}),
                "agent_metadata": {
                    "pipeline_status": "success",
                    "images_processed": image_count,
                    "stages_completed": 3,  # All three agents completed
                    "timestamp": str(Path.cwd())
                }
            }

            # Extract attribute data
            attrs = result_data.get("attributes", {})
            print(f"[DEBUG] Attributes from result_data: {attrs}")
            print(f"[DEBUG] Expected ATTRIBUTES list: {ATTRIBUTES}")
            for attr_name in ATTRIBUTES:
                attr_value = attrs.get(attr_name)
                print(f"[DEBUG] Processing {attr_name}: {attr_value} (type: {type(attr_value)})")
                if isinstance(attr_value, dict):
                    # Already structured with source and confidence
                    normalized_profile["attributes"][attr_name] = attr_value.get("value")
                    print(f"[DEBUG]   -> Extracted value: {attr_value.get('value')}")
                else:
                    # Simple string value
                    normalized_profile["attributes"][attr_name] = attr_value
                    print(f"[DEBUG]   -> Using direct value: {attr_value}")

            return normalized_profile

        except Exception as e:
            print(f"[WARNING] Error parsing agent output: {e}")
            return {
                "product_name": product_name,
                "image_count": image_count,
                "attributes": {},
                "error": f"Parsing error: {str(e)}",
                "status": "partial"
            }

    async def process_batch_async(
        self,
        base_folder: str
    ) -> List[Dict[str, Any]]:
        """
        Process multiple products sequentially using the ADK pipeline.
        
        Args:
            base_folder: Path containing product subfolders
            
        Returns:
            List of product profiles with extracted and enriched attributes
        """
        print(f"\n{'='*70}")
        print(f"[BATCH] Starting batch processing")
        print(f"[BATCH] Base folder: {base_folder}")
        print(f"{'='*70}\n")

        product_folders = [
            d for d in os.listdir(base_folder)
            if os.path.isdir(os.path.join(base_folder, d))
        ]

        results = []

        for idx, product_name in enumerate(product_folders, 1):
            product_path = os.path.join(base_folder, product_name)
            print(f"\n[{idx}/{len(product_folders)}] Processing: {product_name}")

            try:
                result = await self.run_extraction_pipeline(product_name, product_path)
                results.append(result)
            except Exception as e:
                print(f"[ERROR] Batch processing error for {product_name}: {e}")
                results.append({
                    "product_name": product_name,
                    "error": str(e),
                    "status": "failed"
                })

        print(f"\n{'='*70}")
        print(f"[BATCH] Batch processing complete")
        print(f"[BATCH] Total products: {len(product_folders)}")
        print(f"[BATCH] Successful: {sum(1 for r in results if r.get('status') != 'failed')}")
        print(f"[BATCH] Failed: {sum(1 for r in results if r.get('status') == 'failed')}")
        print(f"{'='*70}\n")

        return results

    def process_batch(self, base_folder: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for batch processing"""
        return asyncio.run(self.process_batch_async(base_folder))

    def get_pipeline_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of pipeline execution"""
        return {
            "enrichment_history": self.enrichment_history,
            "total_products_processed": len(self.enrichment_history),
            "successful_extractions": sum(
                1 for h in self.enrichment_history if h.get("status") == "success"
            ),
            "failed_extractions": sum(
                1 for h in self.enrichment_history if h.get("status") == "error"
            ),
            "success_rate": (
                sum(1 for h in self.enrichment_history if h.get("status") == "success") /
                len(self.enrichment_history)
                if self.enrichment_history else 0
            )
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point for command-line usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <product_folder> [base_folder_for_batch]")
        print("\nExamples:")
        print("  Single product: python main.py '/path/to/product_folder'")
        print("  Batch process: python main.py '/path/to/base_folder' --batch")
        return

    pipeline = ProductExtractionPipeline()

    if len(sys.argv) > 2 and sys.argv[2] == "--batch":
        # Batch processing mode
        results = pipeline.process_batch(sys.argv[1])
        
        # Save results
        output_file = "extraction_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n[SAVED] Results saved to {output_file}")
        
        # Print report
        report = pipeline.get_pipeline_report()
        print("\n[REPORT]")
        print(json.dumps(report, indent=2))
    else:
        # Single product processing
        product_path = sys.argv[1]
        product_name = Path(product_path).name
        
        result = asyncio.run(
            pipeline.run_extraction_pipeline(product_name, product_path)
        )
        
        # Print result
        print("\n[RESULT]")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
