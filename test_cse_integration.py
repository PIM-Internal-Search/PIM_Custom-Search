"""
Test script for Google CSE integration
"""
import asyncio
from main import ProductExtractionPipeline

async def test_cse_integration():
    pipeline = ProductExtractionPipeline()
    
    result = await pipeline.run_extraction_pipeline(
        product_name='Canon EOS R5 Mark II Mirrorless Camera',
        product_folder=r'c:\AI Projects\attribute_extraction_app_agentic\raw_images\Canon EOS R5 Mark II Mirrorless Camera'
    )
    
    print('\n\n=== FINAL FILL RATE ===')
    attrs = {k: v for k, v in result['attributes'].items() if v}
    print(f'{len(attrs)}/20 ({len(attrs)*5}%)')
    
    print('\n=== EXTRACTED ATTRIBUTES ===')
    for k, v in attrs.items():
        print(f'{k}: {v}')
    
    print('\n=== PRODUCT DESCRIPTION ===')
    print(result.get('product_description', 'N/A'))

if __name__ == '__main__':
    asyncio.run(test_cse_integration())
