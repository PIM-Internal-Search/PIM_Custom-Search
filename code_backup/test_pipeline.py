"""Simple test script to verify the pipeline works"""
import asyncio
import sys
from pathlib import Path
from main import ProductExtractionPipeline

async def test_pipeline():
    """Test the extraction pipeline with a sample folder"""
    pipeline = ProductExtractionPipeline()
    
    # Test with the first available product folder
    base_folder = Path("../raw_images")
    
    if not base_folder.exists():
        print(f"Error: {base_folder} does not exist")
        print("Please ensure the raw_images folder exists with product subfolders")
        return
    
    # Get first product folder
    product_folders = [d for d in base_folder.iterdir() if d.is_dir()]
    
    if not product_folders:
        print(f"Error: No product folders found in {base_folder}")
        return
    
    test_folder = product_folders[0]
    product_name = test_folder.name
    
    print(f"Testing with: {product_name}")
    print(f"Folder: {test_folder}")
    print("-" * 70)
    
    try:
        result = await pipeline.run_extraction_pipeline(
            product_name,
            str(test_folder)
        )
        
        print("\n" + "=" * 70)
        print("RESULT:")
        print("=" * 70)
        print(f"Product: {result.get('product_name')}")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        else:
            attrs = result.get('attributes', {})
            print(f"Attributes extracted: {len(attrs)}")
            for key, value in list(attrs.items())[:5]:  # Show first 5
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Product Extraction Pipeline...")
    print("=" * 70)
    asyncio.run(test_pipeline())

