"""
Streamlit Application for Product Attribute Extraction
Clean UI with folder selection and product listing
"""

import os
import json
import asyncio
from pathlib import Path
import streamlit as st
from PIL import Image
import pandas as pd

from pipeline import ProductExtractionPipeline


# Page configuration
st.set_page_config(
    page_title="Product Attribute Extraction",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎯 Product Attribute Extraction Agent")
st.markdown("""
**Powered by Google ADK Sequential Agents**

Upload product images and let AI extract attributes automatically using:
1. 🖼️ **Image Analysis Agent** - Extracts visible attributes from images
2. 🔍 **Search Enhancement Agent** - Enhances attributes using Google Custom Search
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Status")
    from config import GEMINI_API_KEY, GOOGLE_CSE_API_KEY
    
    if GEMINI_API_KEY:
        st.success("✓ Gemini API configured")
    else:
        st.error("✗ Gemini API key missing")
    
    if GOOGLE_CSE_API_KEY:
        st.success("✓ Google Custom Search configured")
    else:
        st.warning("⚠ Google Custom Search not configured")
    
    st.markdown("---")
    
    if st.button("🔄 Clear Cache"):
        st.cache_resource.clear()
        st.success("Cache cleared!")


# Initialize pipeline
@st.cache_resource
def get_pipeline():
    """Initialize the extraction pipeline"""
    return ProductExtractionPipeline()

pipeline = get_pipeline()


# Main UI
st.markdown("---")
st.subheader("📁 Select Product Folder")

# Folder input
col1, col2 = st.columns([4, 1])

with col1:
    folder_path = st.text_input(
        "Folder path containing product subfolders",
        value=r"c:\AI Projects\attribute_extraction_app_agentic\raw_images",
        placeholder="e.g., c:\\path\\to\\raw_images"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    load_folder = st.button("📂 Load Folder", use_container_width=True)

# Session state
if 'folder_loaded' not in st.session_state:
    st.session_state.folder_loaded = False
if 'product_folders' not in st.session_state:
    st.session_state.product_folders = []
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = []

# Load folder
if load_folder:
    if os.path.isdir(folder_path):
        product_folders = [
            p for p in Path(folder_path).iterdir()
            if p.is_dir() and not p.name.startswith('_')
        ]
        
        if product_folders:
            st.session_state.folder_loaded = True
            st.session_state.product_folders = product_folders
            st.session_state.base_folder = folder_path
            st.success(f"✓ Found {len(product_folders)} product folder(s)")
        else:
            st.error("❌ No product folders found")
    else:
        st.error(f"❌ Folder not found: {folder_path}")

# Show loaded folders
if st.session_state.folder_loaded and st.session_state.product_folders:
    st.markdown("---")
    st.subheader("📦 Products Found")
    
    # Display product folders
    cols = st.columns(min(4, len(st.session_state.product_folders)))
    for idx, product_folder in enumerate(st.session_state.product_folders):
        with cols[idx % 4]:
            st.write(f"📷 {product_folder.name}")
    
    st.markdown("---")
    
    # Start extraction button
    if st.button("🚀 Start Attribute Extraction", use_container_width=True, type="primary"):
        st.session_state.extraction_started = True
        st.session_state.extraction_results = []
    
    # Process extraction
    if st.session_state.get('extraction_started', False):
        st.info("⏳ Processing products... This may take a few minutes.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        # Create event loop for async processing
        if 'event_loop' not in st.session_state:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            st.session_state.event_loop = loop
        else:
            loop = st.session_state.event_loop
            asyncio.set_event_loop(loop)
        
        # Process each product
        for idx, product_folder in enumerate(st.session_state.product_folders):
            product_name = product_folder.name
            product_path = str(product_folder)
            
            status_text.write(f"**[{idx+1}/{len(st.session_state.product_folders)}]** Processing: {product_name}")
            
            try:
                with st.spinner(f"Analyzing {product_name}..."):
                    result = loop.run_until_complete(
                        pipeline.extract_product_attributes(product_name, product_path)
                    )
                    results.append(result)
            except Exception as e:
                st.error(f"❌ Error processing {product_name}: {str(e)}")
                results.append({
                    "product_name": product_name,
                    "error": str(e),
                    "status": "failed"
                })
            
            progress_bar.progress((idx + 1) / len(st.session_state.product_folders))
        
        # Store results
        st.session_state.extraction_results = results
        st.session_state.extraction_started = False
        
        status_text.empty()
        st.success(f"✅ Processing complete! Processed {len(results)} product(s).")

# Display results
if st.session_state.extraction_results:
    st.markdown("---")
    st.subheader("📊 Extraction Results")
    
    # Summary metrics
    results = st.session_state.extraction_results
    successful = sum(1 for r in results if r.get('status') == 'success')
    failed = sum(1 for r in results if r.get('status') == 'failed')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", len(results))
    with col2:
        st.metric("Successful", successful)
    with col3:
        st.metric("Failed", failed)
    
    st.markdown("---")
    
    # Product listing
    for result in results:
        product_name = result.get("product_name", "Unknown")
        
        with st.expander(f"📷 {product_name}", expanded=True):
            if result.get("status") == "failed":
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            else:
                # Layout: Images | Description & Attributes
                img_col, info_col = st.columns([1, 2])
                
                # ========== IMAGE COLUMN ==========
                with img_col:
                    st.write("**Product Images:**")
                    
                    image_paths = result.get("image_paths", [])
                    if image_paths:
                        # Show first image
                        try:
                            img = Image.open(image_paths[0])
                            st.image(img, caption=Path(image_paths[0]).name, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not load image: {e}")
                        
                        # Show additional images if available
                        if len(image_paths) > 1:
                            with st.expander(f"View all {len(image_paths)} images"):
                                for img_path in image_paths[1:]:
                                    try:
                                        img = Image.open(img_path)
                                        st.image(img, caption=Path(img_path).name, use_container_width=True)
                                    except:
                                        pass
                    else:
                        st.info("No images available")
                
                # ========== INFO COLUMN ==========
                with info_col:
                    # Product Description
                    st.write("**Product Description:**")
                    description = result.get("product_description", "")
                    if description:
                        st.info(description)
                    else:
                        st.warning("No description available")
                    
                    # Attributes
                    st.write("**Extracted Attributes:**")
                    attributes = result.get("attributes", {})
                    
                    if attributes:
                        # Filter non-null attributes
                        filled_attrs = {k: v for k, v in attributes.items() if v is not None and v != "null"}
                        
                        if filled_attrs:
                            # Display as table
                            df = pd.DataFrame([
                                {"Attribute": k, "Value": v}
                                for k, v in filled_attrs.items()
                            ])
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            # Fill rate
                            fill_rate = result.get("fill_rate", "N/A")
                            filled = result.get("filled_attributes", 0)
                            total = result.get("total_attributes", 0)
                            st.metric("Fill Rate", fill_rate, f"{filled}/{total} attributes")
                        else:
                            st.warning("No attributes extracted")
                    else:
                        st.warning("No attributes available")
    
    # Download section
    st.markdown("---")
    st.subheader("📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON export
        json_data = json.dumps(st.session_state.extraction_results, indent=2)
        st.download_button(
            "📄 Download JSON",
            json_data.encode("utf-8"),
            file_name="extraction_results.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # CSV export
        import csv
        import io
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Headers
        headers = ["Product Name", "Description", "Fill Rate"]
        if results and results[0].get("attributes"):
            headers.extend(results[0]["attributes"].keys())
        
        writer.writerow(headers)
        
        # Data rows
        for result in results:
            if result.get("status") == "success":
                row = [
                    result.get("product_name", ""),
                    result.get("product_description", ""),
                    result.get("fill_rate", "")
                ]
                
                for attr in headers[3:]:
                    row.append(result.get("attributes", {}).get(attr, ""))
                
                writer.writerow(row)
        
        csv_bytes = csv_buffer.getvalue().encode("utf-8")
        st.download_button(
            "📊 Download CSV",
            csv_bytes,
            file_name="extraction_results.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Powered by Google Agent Development Kit (ADK) | Sequential Agents Pipeline</p>
    <p>Image Analysis → Search Enhancement</p>
</div>
""", unsafe_allow_html=True)
