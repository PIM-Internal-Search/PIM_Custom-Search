
import asyncio
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.append(os.path.join(os.getcwd(), 'code'))

from main import ProductExtractionPipeline

async def run_test():
    print("Initializing pipeline...")
    pipeline = ProductExtractionPipeline()
    
    # Mock data
    product_name = "Test Product"
    product_folder = "c:\\AI Projects\\attribute_extraction_app_agentic\\raw_images\\Canon_EOS_R5_Mark_II"
    
    # Create dummy folder if not exists
    os.makedirs(product_folder, exist_ok=True)
    # Create dummy image
    with open(os.path.join(product_folder, "test.jpg"), "wb") as f:
        f.write(b"dummy image data")

    print("Running pipeline run 1...")
    try:
        # We expect this to fail if we don't have API keys, but we want to check for Event Loop errors
        # We are mocking the runner execution effectively by checking if we get past agent creation
        # But since we need to run it, we will catch the API error but look for Loop error
        await pipeline.run_extraction_pipeline(product_name, product_folder)
    except Exception as e:
        print(f"Run 1 result: {e}")

    print("Running pipeline run 2...")
    try:
        await pipeline.run_extraction_pipeline(product_name, product_folder)
    except Exception as e:
        print(f"Run 2 result: {e}")

if __name__ == "__main__":
    # Simulate what Streamlit does: asyncio.run called multiple times? 
    # Or just running in a loop.
    # Actually Streamlit might call asyncio.run multiple times if using the pattern in app.py
    
    print("--- Simulation 1: Single Event Loop ---")
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"Simulation 1 failed: {e}")

    print("\n--- Simulation 3: Persistent Loop (App Pattern) ---")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    print("Run A with persistent loop...")
    try:
        loop.run_until_complete(run_test())
    except Exception as e:
        print(f"Simulation 3 run A failed: {e}")
        
    print("Run B with persistent loop...")
    try:
        loop.run_until_complete(run_test())
    except Exception as e:
        print(f"Simulation 3 run B failed: {e}")
        
    loop.close()
