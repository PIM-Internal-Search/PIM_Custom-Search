"""
Pipeline Orchestrator for Product Attribute Extraction
Handles image loading, agent execution, and result processing
"""

import os
import json
import base64
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image

from google.adk.runners import RunConfig, InMemoryRunner
from google.genai import types as genai_types
import requests

from agents import create_sequential_agent, ATTRIBUTES
from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX


class ProductExtractionPipeline:
    """Orchestrates the product attribute extraction workflow"""
    
    def __init__(self):
        """Initialize the pipeline"""
        self.agent = create_sequential_agent()
        self.runner = InMemoryRunner(agent=self.agent, app_name="product_extraction")
    
    def find_product_images(self, product_folder: str) -> List[str]:
        """Find all image files in a product folder"""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        images = []
        
        for file in os.listdir(product_folder):
            if Path(file).suffix.lower() in image_extensions:
                images.append(os.path.join(product_folder, file))
        
        return sorted(images)
    
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
    
    def search_google_custom(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Execute Google Custom Search API query"""
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": GOOGLE_CSE_API_KEY,
            "cx": GOOGLE_CSE_CX,
            "q": query,
            "num": min(num_results, 10)
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
                    "snippet": item.get("snippet", "")
                })
            
            return results
        except Exception as e:
            print(f"[WARNING] Google CSE search failed: {e}")
            return []
    
    async def extract_product_attributes(
        self,
        product_name: str,
        product_folder: str
    ) -> Dict[str, Any]:
        """
        Execute the sequential agent pipeline for a single product.
        
        Args:
            product_name: Name of the product
            product_folder: Path to product folder containing images
            
        Returns:
            Dictionary containing the complete product profile
        """
        print(f"\n{'='*70}")
        print(f"[PIPELINE] Processing: {product_name}")
        print(f"{'='*70}")
        
        try:
            # Find images
            images = self.find_product_images(product_folder)
            
            if not images:
                return {
                    "product_name": product_name,
                    "error": f"No images found in {product_folder}",
                    "status": "failed"
                }
            
            print(f"[IMAGES] Found {len(images)} image(s)")
            
            # Prepare first image
            image_data = self.prepare_image_data(images[0])
            print(f"[IMAGE] Processing: {Path(images[0]).name}")
            
            # Create user message with image
            image_bytes = base64.b64decode(image_data["data"])
            
            parts = [
                genai_types.Part(text=f"""Analyze this product and extract attributes.

Product Name: {product_name}
Product Folder: {product_folder}
Total Images: {len(images)}

Please execute the two-stage pipeline:
1. Extract attributes from the image
2. Enhance attributes using search (if needed)

Image to analyze is provided below."""),
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type=image_data["mime_type"],
                        data=image_bytes
                    )
                )
            ]
            
            user_message = genai_types.Content(role="user", parts=parts)
            
            # Create unique session ID with timestamp to avoid conflicts
            import time
            timestamp = int(time.time() * 1000)  # milliseconds
            safe_name = "".join(c if c.isalnum() else '_' for c in product_name)
            session_id = f"session_{safe_name}_{timestamp}"
            user_id = "user1"
            
            # Initial state
            initial_state = {
                "product_name": product_name,
                "product_folder": product_folder,
                "images_found": len(images)
            }
            
            print("[AGENTS] Executing sequential pipeline...")
            print("  Stage 1: Image Analysis Agent")
            print("  Stage 2: Search Enhancement Agent")
            
            # Execute agent pipeline
            run_cfg = RunConfig()
            async_gen = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
                state_delta=initial_state,
                run_config=run_cfg
            )
            
            # Collect events
            events = []
            async for event in async_gen:
                events.append(event)
            
            # Extract final result
            result = None
            for event in reversed(events):
                if hasattr(event, 'content') and event.content:
                    result = event.content
                    break
            
            if result is None and events:
                result = events[-1]
            
            print("[AGENTS] Pipeline execution complete")
            
            # Parse result
            final_profile = self._parse_agent_output(result, product_name, len(images), images)
            
            print(f"[SUCCESS] Processed {product_name}")
            print(f"{'='*70}\n")
            
            return final_profile
            
        except Exception as e:
            print(f"[ERROR] Pipeline error for {product_name}: {str(e)}")
            return {
                "product_name": product_name,
                "error": str(e),
                "status": "failed"
            }
    
    def _parse_agent_output(
        self,
        agent_result: Any,
        product_name: str,
        image_count: int,
        image_paths: List[str]
    ) -> Dict[str, Any]:
        """Parse the output from the SequentialAgent"""
        try:
            # Extract text from agent result
            raw_text = None
            
            if hasattr(agent_result, 'parts') and agent_result.parts:
                text_parts = [p.text for p in agent_result.parts if hasattr(p, 'text') and p.text]
                if text_parts:
                    raw_text = ''.join(text_parts)
            elif hasattr(agent_result, 'content') and agent_result.content:
                content = agent_result.content
                if hasattr(content, 'parts') and content.parts:
                    text_parts = [p.text for p in content.parts if hasattr(p, 'text') and p.text]
                    if text_parts:
                        raw_text = ''.join(text_parts)
            elif isinstance(agent_result, dict):
                return self._format_result(agent_result, product_name, image_count, image_paths)
            
            # Parse JSON from text
            if raw_text:
                # Remove markdown code blocks
                if '```json' in raw_text:
                    json_start = raw_text.find('```json') + 7
                    json_end = raw_text.find('```', json_start)
                    raw_text = raw_text[json_start:json_end].strip()
                elif '```' in raw_text:
                    json_start = raw_text.find('```') + 3
                    json_end = raw_text.find('```', json_start)
                    raw_text = raw_text[json_start:json_end].strip()
                
                try:
                    result_data = json.loads(raw_text)
                    return self._format_result(result_data, product_name, image_count, image_paths)
                except json.JSONDecodeError:
                    pass
            
            # Fallback
            return {
                "product_name": product_name,
                "image_count": image_count,
                "image_paths": image_paths,
                "attributes": {},
                "product_description": "",
                "status": "partial",
                "error": "Could not parse agent output"
            }
            
        except Exception as e:
            print(f"[WARNING] Error parsing agent output: {e}")
            return {
                "product_name": product_name,
                "image_count": image_count,
                "image_paths": image_paths,
                "attributes": {},
                "error": f"Parsing error: {str(e)}",
                "status": "partial"
            }
    
    def _format_result(
        self,
        result_data: Dict[str, Any],
        product_name: str,
        image_count: int,
        image_paths: List[str]
    ) -> Dict[str, Any]:
        """Format the result data into a standardized structure"""
        # Extract attributes
        attributes = {}
        raw_attrs = result_data.get("attributes", {})
        
        for attr_name in ATTRIBUTES:
            attr_value = raw_attrs.get(attr_name)
            if isinstance(attr_value, dict):
                # Has source/confidence info
                attributes[attr_name] = attr_value.get("value")
            else:
                # Simple value
                attributes[attr_name] = attr_value
        
        # Calculate fill rate
        filled = sum(1 for v in attributes.values() if v is not None and v != "null")
        fill_rate = f"{(filled / len(ATTRIBUTES) * 100):.1f}%"
        
        return {
            "product_name": product_name,
            "image_count": image_count,
            "image_paths": image_paths,
            "attributes": attributes,
            "product_description": result_data.get("product_description", ""),
            "fill_rate": fill_rate,
            "filled_attributes": filled,
            "total_attributes": len(ATTRIBUTES),
            "status": "success"
        }
    
    async def process_batch_async(self, base_folder: str) -> List[Dict[str, Any]]:
        """Process multiple products from a base folder"""
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
                result = await self.extract_product_attributes(product_name, product_path)
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
        print(f"[BATCH] Successful: {sum(1 for r in results if r.get('status') == 'success')}")
        print(f"[BATCH] Failed: {sum(1 for r in results if r.get('status') == 'failed')}")
        print(f"{'='*70}\n")
        
        return results
    
    def process_batch(self, base_folder: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for batch processing"""
        return asyncio.run(self.process_batch_async(base_folder))


# CLI entry point
def main():
    """Main entry point for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <product_folder> [--batch]")
        print("\nExamples:")
        print("  Single product: python pipeline.py 'c:\\path\\to\\product_folder'")
        print("  Batch process: python pipeline.py 'c:\\path\\to\\base_folder' --batch")
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
    else:
        # Single product processing
        product_path = sys.argv[1]
        product_name = Path(product_path).name
        
        result = asyncio.run(
            pipeline.extract_product_attributes(product_name, product_path)
        )
        
        # Print result
        print("\n[RESULT]")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
