"""
Streamlit Application for Camera Attribute Extraction
Powered by Google Agent Development Kit (ADK) Sequential Agents
"""

import zipfile
import tempfile
import io
import json
import asyncio
from pathlib import Path
import streamlit as st
from main import ProductExtractionPipeline
import os
from PIL import Image


# Page configuration
st.set_page_config(
    page_title="Camera Attribute Extraction Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Autonomous Camera Attribute Extraction Agent")

st.write("""
Powered by **Google Agent Development Kit (ADK)** with Sequential Agents.
Upload product images and the autonomous agent will analyze, search for manufacturer specs, 
and extract all product attributes automatically.

**Pipeline Architecture:**
1. 🖼️ **Image Extraction Agent** - Analyzes product images and extracts visible attributes
2. 🔍 **Manufacturer Search Agent** - Generates targeted queries to find official specifications
3. ✨ **Attribute Enrichment Agent** - Enriches attributes with manufacturer data and finalizes results
""")

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.header("⚙️ Configuration & Settings")

with st.sidebar:
    st.subheader("Pipeline Settings")
    
    # Agent execution mode
    execution_mode = st.radio(
        "Execution Mode",
        options=["Standard Sequential", "Verbose with Tracing"],
        help="Standard: Fast execution. Verbose: Shows agent reasoning."
    )
    
    # Cache control
    if st.button("🔄 Clear Agent Cache", key="clear_cache"):
        st.cache_resource.clear()
        st.success("Cache cleared!")
    
    st.markdown("---")
    st.subheader("API Configuration")
    
    # Display API status
    gemini_key = os.environ.get("GEMINI_API_KEY")
    cse_key = os.environ.get("GOOGLE_CSE_API_KEY")
    
    if gemini_key:
        st.success("✓ Gemini API configured")
    else:
        st.warning("⚠️ Gemini API key not found")
    
    if cse_key:
        st.success("✓ Google Custom Search configured")
    else:
        st.info("ℹ️ Optional: Google Custom Search for enrichment")


# ============================================================================
# PIPELINE INITIALIZATION
# ============================================================================

@st.cache_resource
def get_pipeline():
    """Initialize the ADK extraction pipeline"""
    return ProductExtractionPipeline()

pipeline = get_pipeline()

# ============================================================================
# INPUT METHOD SELECTION
# ============================================================================

st.markdown("---")
st.subheader("📥 Input Configuration")

input_method = st.radio(
    "Select input method:",
    ["📁 Folder Path", "📦 Upload ZIP File"],
    horizontal=True
)

# Initialize session state for inputs
if 'source_folder' not in st.session_state:
    st.session_state.source_folder = None
if 'product_folders' not in st.session_state:
    st.session_state.product_folders = None

source_folder = st.session_state.source_folder
product_folders = st.session_state.product_folders
base_path = st.session_state.source_folder # simplified


# ============================================================================
# FOLDER PATH INPUT
# ============================================================================

if input_method == "📁 Folder Path":
    col1, col2 = st.columns([3, 1])
    
    with col1:
        folder_input = st.text_input(
            "Folder path",
            value="c:\\AI Projects\\attribute_extraction_app_agentic\\raw_images",
            placeholder="e.g., c:\\path\\to\\images or /home/user/images"
        )
    
    with col2:
        load_button = st.button("📂 Load Folder", use_container_width=True)
    
    if load_button:
        if os.path.isdir(folder_input):
            st.session_state.source_folder = folder_input
            st.session_state.product_folders = [
                p for p in Path(folder_input).iterdir() 
                if p.is_dir() and not p.name.startswith('__')
            ]
            source_folder = st.session_state.source_folder
            product_folders = st.session_state.product_folders
            base_path = folder_input
            st.success(f"✓ Folder loaded: {folder_input}")
            if product_folders:
                st.info(f"Found {len(product_folders)} product folder(s)")
        else:
            st.error(f"❌ Folder not found: {folder_input}")

# ============================================================================
# ZIP FILE UPLOAD
# ============================================================================

else:  # ZIP upload
    uploaded_file = st.file_uploader(
        "Upload a ZIP file containing product folders",
        type=["zip"],
        help="Each folder should contain images for a single product"
    )
    
    if uploaded_file is not None:
        tmpdir = tempfile.mkdtemp()
        zip_path = Path(tmpdir) / "upload.zip"
        
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmpdir)
            
            st.session_state.product_folders = [
                p for p in Path(tmpdir).iterdir()
                if p.is_dir() and not p.name.startswith('__')
            ]
            st.session_state.source_folder = "zip"
            source_folder = st.session_state.source_folder
            product_folders = st.session_state.product_folders
            base_path = tmpdir
            st.success(f"✓ ZIP file uploaded successfully")
            st.info(f"Found {len(product_folders)} product folder(s)")
        except Exception as e:
            st.error(f"Error extracting ZIP: {str(e)}")
            product_folders = None

# ============================================================================
# PROCESSING
# ============================================================================

if source_folder and product_folders and len(product_folders) > 0:
    st.markdown("---")
    
    # Initialize session state
    if 'extraction_results' not in st.session_state:
        st.session_state.extraction_results = []
    if 'processing_started' not in st.session_state:
        st.session_state.processing_started = False
    
    # Button to start processing
    button_clicked = st.button("🚀 Start Extraction Pipeline", key="process_btn", use_container_width=True)
    
    # Debug: Show button state
    if button_clicked:
        st.session_state.processing_started = True
        st.session_state.extraction_results = []  # Reset results
        st.success("✅ Button clicked! Initializing pipeline...")
    
    # Process if button was clicked or processing is in progress
    if button_clicked or st.session_state.processing_started:

        st.info("⏳ Starting ADK Sequential Agent Pipeline...")
        st.write(f"📁 Processing {len(product_folders)} product folder(s)...")
        
        # Show status
        if st.session_state.processing_started:
            st.write("🔄 Pipeline is running...")
        
        results = []
        progress_bar = st.progress(0)
        status_container = st.container()
        
        # Debug: Show what we're processing
        with status_container:
            st.write(f"**Found {len(product_folders)} product folder(s) to process**")
            for pf in product_folders:
                st.write(f"- {pf.name}")
        
        # Process each product
        for idx, product_folder in enumerate(product_folders):
            product_name = product_folder.name
            product_path = str(product_folder)
            
            with status_container:
                st.write(f"**[{idx+1}/{len(product_folders)}]** Processing: {product_name}")
                st.write(f"Path: {product_path}")
                
                # Create three columns for pipeline stages
                stage1, stage2, stage3 = st.columns(3)
                with stage1:
                    st.write("🖼️ Extraction")
                with stage2:
                    st.write("🔍 Search")
                with stage3:
                    st.write("✨ Enrichment")
            
            try:
                # Check if folder exists and has images
                if not os.path.exists(product_path):
                    raise FileNotFoundError(f"Folder not found: {product_path}")
                
                # List images in folder
                image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
                images = [f for f in os.listdir(product_path) 
                         if Path(f).suffix.lower() in image_extensions]
                
                if not images:
                    raise ValueError(f"No images found in {product_path}")
                
                with status_container:
                    st.write(f"✅ Found {len(images)} image(s)")
                    st.write("🔄 Running pipeline...")
                
                
                # Run the ADK pipeline with better error handling
                try:
                    # Use a persistent loop to avoid "Event loop is closed" errors
                    if 'event_loop' not in st.session_state:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        st.session_state.event_loop = loop
                    else:
                        loop = st.session_state.event_loop
                        # Ensure it's the current loop
                        asyncio.set_event_loop(loop)

                    with status_container:
                        st.write("⏳ Executing async pipeline...")
                    
                    # Use spinner for better UX
                    with st.spinner(f"Processing {product_name}... This may take 1-3 minutes."):
                        result = loop.run_until_complete(
                            pipeline.run_extraction_pipeline(
                                product_name,
                                product_path
                            )
                        )

                    
                    results.append(result)
                    
                    with status_container:
                        if result.get("error"):
                            st.warning(f"⚠️ Partial result: {result.get('error', 'Unknown error')}")
                            if result.get("error"):
                                st.expander("Error Details").code(result.get("error"), language='text')
                        else:
                            st.success(f"✅ Completed successfully")
                            attrs = result.get('attributes', {})
                            filled = sum(1 for v in attrs.values() if v)
                            st.write(f"📊 Extracted {filled}/{len(attrs)} attributes")
                
                except asyncio.TimeoutError:
                    error_msg = "Pipeline execution timed out"
                    st.error(f"❌ {error_msg}")
                    results.append({
                        "product_name": product_name,
                        "error": error_msg,
                        "status": "failed"
                    })
                except Exception as pipeline_error:
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"❌ Pipeline execution error: {str(pipeline_error)}")
                    with st.expander("Full Error Details"):
                        st.code(error_details, language='python')
                    results.append({
                        "product_name": product_name,
                        "error": str(pipeline_error),
                        "status": "failed",
                        "traceback": error_details
                    })
            
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                st.error(f"❌ Error processing {product_name}: {str(e)}")
                with st.expander("Full Error Details"):
                    st.code(error_details, language='python')
                results.append({
                    "product_name": product_name,
                    "error": str(e),
                    "status": "failed",
                    "traceback": error_details
                })
            
            progress_bar.progress((idx + 1) / len(product_folders))
        
        # Store results in session state
        st.session_state.extraction_results = results
        st.session_state.processing_started = False  # Reset processing flag
        
        # Show completion message
        st.success(f"✅ Processing complete! Processed {len(results)} product(s).")
        
        # Display Results
        st.markdown("---")
        st.subheader("📊 Extracted Product Attributes")
        
        # Use results from session state if available
        display_results = st.session_state.extraction_results if st.session_state.extraction_results else results
        
        if not display_results:
            st.warning("No results to display. Check the error messages above.")
        else:
            for prod in display_results:
                product_name = prod.get("product_name", "Unknown")
            
                with st.expander(f"📷 {product_name}", expanded=True):
                    if "error" in prod and prod.get("status") == "failed":
                        st.error(f"❌ Error: {prod['error']}")
                    else:
                        # Create layout: image left, attributes right
                        img_col, attr_col = st.columns([1, 1.5])
                        
                        # ==================== IMAGE COLUMN ====================
                        with img_col:
                            st.write("**Product Image:**")
                            
                            # Find images in the original product folder
                            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
                            
                            # Try to find the original product folder
                            original_folder = None
                            for pf in product_folders:
                                if pf.name == product_name:
                                    original_folder = pf
                                    break
                            
                            if original_folder:
                                images = sorted([
                                    f for f in original_folder.iterdir()
                                    if f.suffix.lower() in image_extensions
                                ])
                                
                                if images:
                                    try:
                                        img = Image.open(images[0])
                                        st.image(img, caption=images[0].name, use_container_width=True)
                                    except Exception as e:
                                        st.warning(f"Could not load image: {e}")
                                else:
                                    st.info("No images found")
                            else:
                                st.info("Original product folder not accessible")
                        
                        # ==================== ATTRIBUTES COLUMN ====================
                        with attr_col:
                            # Product Description
                            st.write("**Product Description:**")
                            description = prod.get("product_description", "N/A")
                            st.write(description if description else "No description available")
                            
                            # Extracted Attributes
                            st.write("**Extracted Attributes:**")
                            attributes = prod.get("attributes", {})
                            
                            if attributes:
                                # Filter non-null attributes
                                attr_dict = {k: v for k, v in attributes.items() if v}
                                
                                if attr_dict:
                                    st.table(attr_dict)
                                else:
                                    st.info("No attributes extracted.")
                            else:
                                st.info("No attributes available.")
                            
                            # Enrichment Summary
                            enrichment = prod.get("enrichment_summary", {})
                            if enrichment:
                                st.write("**Enrichment Summary:**")
                                st.metric(
                                    "Filled Attributes",
                                    enrichment.get("filled_attributes", "N/A")
                                )
                            
                            # Agent Metadata
                            if prod.get("agent_metadata"):
                                with st.expander("🤖 Agent Execution Details"):
                                    metadata = prod["agent_metadata"]
                                    st.json(metadata)
            
            # Only show download section if we have results
            if display_results and len(display_results) > 0:
                # ====================================================================
                # DOWNLOAD OPTIONS
                # ====================================================================
                
                st.markdown("---")
                st.subheader("📥 Download Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # JSON Export
                    export_results = st.session_state.extraction_results if st.session_state.extraction_results else results
                    json_data = json.dumps(export_results, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📄 Download as JSON",
                        json_data.encode("utf-8"),
                        file_name="extraction_results.json",
                        mime="application/json"
                    )
                
                with col2:
                    # CSV Export
                    import csv
                    csv_buffer = io.StringIO()
                    writer = csv.writer(csv_buffer)
                    
                    # Build headers from first result
                    export_results = st.session_state.extraction_results if st.session_state.extraction_results else results
                    headers = ["Product Name", "Description"]
                    if export_results and export_results[0].get("attributes"):
                        headers.extend(export_results[0]["attributes"].keys())
                    
                    writer.writerow(headers)
                    
                    # Write data rows
                    for prod in export_results:
                        if "error" not in prod or prod.get("status") != "failed":
                            row = [
                                prod.get("product_name", ""),
                                prod.get("product_description", "")
                            ]
                            
                            for attr in headers[2:]:
                                row.append(prod.get("attributes", {}).get(attr, ""))
                            
                            writer.writerow(row)
                    
                    csv_bytes = csv_buffer.getvalue().encode("utf-8")
                    st.download_button(
                        "📊 Download as CSV",
                        csv_bytes,
                        file_name="extraction_results.csv",
                        mime="text/csv"
                    )

# ============================================================================
# INITIAL GUIDANCE
# ============================================================================

elif input_method == "📁 Folder Path" and not source_folder:
    st.info("👉 Enter a folder path and click '📂 Load Folder' to start")
else:
    st.info("👉 Upload a ZIP file to start processing")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Powered by Google Agent Development Kit (ADK) | Sequential Agents Pipeline</p>
    <p>Image Analysis • Manufacturer Search • Attribute Enrichment</p>
</div>
""", unsafe_allow_html=True)
