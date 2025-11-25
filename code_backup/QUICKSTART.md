# Quick Start Guide - ADK Sequential Agents

Get up and running with the camera attribute extraction system in 5 minutes.

## 🚀 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export GEMINI_API_KEY="your-api-key-here"

# 3. Run Streamlit app
streamlit run app.py

# 4. Open browser to http://localhost:8501
```

## 📋 Detailed Setup

### Prerequisites
- Python 3.8+
- Google Generative AI API key (get from https://ai.google.dev)
- Product images in folders

### Step-by-Step Installation

#### 1. Clone/Navigate to Project
```bash
cd c:\AI Projects\attribute_extraction_app_agentic\code
```

#### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Output should show:
```
Successfully installed google-adk-python google-generativeai streamlit requests
```

#### 4. Set Environment Variables

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
$env:GOOGLE_CSE_API_KEY = "optional-cse-key"
$env:GOOGLE_CSE_CX = "optional-cse-cx"
```

**macOS/Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
export GOOGLE_CSE_API_KEY="optional-cse-key"
export GOOGLE_CSE_CX="optional-cse-cx"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

## 🎯 Running the Application

### Option 1: Web Interface (Easiest)

```bash
streamlit run app.py
```

**Then:**
1. Open browser to http://localhost:8501
2. Enter folder path or upload ZIP file
3. Click "🚀 Start Extraction Pipeline"
4. Download results when complete

**Expected Output:**
- Pipeline execution report (success rate, filled attributes)
- Product details with extracted attributes
- Download buttons for JSON and CSV

### Option 2: Command Line

**Single Product:**
```bash
python main.py "c:\path\to\product_folder"
```

**Batch Processing:**
```bash
python main.py "c:\path\to\raw_images" --batch
```

**Output:**
- Console logs showing progress
- Final results printed as JSON

### Option 3: Batch Processing Script

```bash
python batch_processor.py "./raw_images" "./output"
```

**Generates:**
- `extraction_results_<timestamp>.json` - Full results
- `extraction_results_<timestamp>.csv` - Spreadsheet format
- `summary_report_<timestamp>.json` - Statistics

## 📁 Input Format

### Folder Structure

```
raw_images/                              (Base folder)
├── Canon EOS R5 Mark II/                (Product folder 1)
│   ├── image1.jpg
│   ├── image2.jpg
│   └── image3.png
│
└── Sony Alpha a7 IV/                    (Product folder 2)
    ├── photo1.jpg
    ├── photo2.png
    └── photo3.webp
```

**Requirements:**
- Each product in its own folder
- Folder name = product name
- Images must be: .jpg, .jpeg, .png, .gif, or .webp
- At least 1 image per product

### Or Upload as ZIP

Same structure, compressed as ZIP file. Upload in Streamlit interface.

## 📊 Understanding Output

### JSON Output Example

```json
{
  "product_name": "Canon EOS R5 Mark II Mirrorless Camera",
  "image_count": 2,
  "attributes": {
    "Color": "Black",
    "Dimensions": "138.4 x 97.7 x 88.2 mm",
    "Weight": "738g",
    "Sensor Type": "Full Frame CMOS",
    ...
  },
  "product_description": "Professional mirrorless camera with...",
  "enrichment_summary": {
    "filled_attributes": 18,
    "sources_used": ["image", "official_specs"]
  }
}
```

### CSV Output

| Product Name | Description | Color | Dimensions | Weight | ... |
|---|---|---|---|---|---|
| Canon EOS R5 Mark II | Professional mirrorless camera... | Black | 138.4 x 97.7 x 88.2 mm | 738g | ... |

### Summary Report

```
BATCH PROCESSING SUMMARY REPORT
────────────────────────────────────────────────────────────────────────────────
Total Products Processed: 2
Successful: 2
Failed: 0
Success Rate: 100.0%

ATTRIBUTE COMPLETION RATES
────────────────────────────────────────────────────────────────────────────────
  Color                         : 100% (2/2)
  Dimensions                    : 100% (2/2)
  Weight                        : 100% (2/2)
  Sensor Type                   : 100% (2/2)
  ...
```

## ⚠️ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "API key not configured" | Set `GEMINI_API_KEY` environment variable |
| "No images found" | Check images are in `.jpg`, `.png`, etc. format |
| "Streamlit not found" | Run `pip install -r requirements.txt` again |
| "Port 8501 already in use" | Use `streamlit run app.py --server.port 8502` |
| "Timeout error" | Check internet connection, increase timeout |
| "JSON parsing error" | Agent response format issue, check API quota |

## 🔧 Configuration

### Model Selection

Edit `agents.py` to change model:
```python
# Current
gemini_model = models.GeminiModel(
    model_name="gemini-2.0-flash",
    api_key=GEMINI_API_KEY
)

# Alternative
gemini_model = models.GeminiModel(
    model_name="gemini-1.5-pro",
    api_key=GEMINI_API_KEY
)
```

### Attributes to Extract

Edit `agents.py` to add/remove attributes:
```python
ATTRIBUTES = [
    "Color",
    "Body Material",
    "Dimensions",
    # Add more here
]
```

### Official Specs

Edit `agents.py` to add known specifications:
```python
OFFICIAL_SPECS = {
    "Camera Model": {
        "Dimensions": "W x H x D mm",
        "Weight": "XXXg"
    }
}
```

## 📚 Learning Resources

| Resource | Link |
|----------|------|
| Architecture Overview | See `ADK_ARCHITECTURE.md` |
| Implementation Details | See `IMPLEMENTATION_GUIDE.md` |
| Refactoring Summary | See `REFACTORING_SUMMARY.md` |
| ADK Documentation | https://google.github.io/adk-docs/ |
| Gemini API Docs | https://ai.google.dev/ |

## 🎓 Example Workflows

### Workflow 1: Extract Single Camera

```bash
# Run extraction for one product
python main.py "C:\Products\Canon EOS R5"

# Result appears in console
```

### Workflow 2: Batch Process Multiple Products

```bash
# Run batch processor
python batch_processor.py "./raw_images" "./results"

# Generates JSON, CSV, and report in ./results folder
```

### Workflow 3: Web Interface with ZIP Upload

1. Prepare `my_cameras.zip` with folder structure
2. Open Streamlit app: `streamlit run app.py`
3. Select "📦 Upload ZIP File"
4. Choose `my_cameras.zip`
5. Click "🚀 Start Extraction Pipeline"
6. Download results

### Workflow 4: Programmatic Integration

```python
from main import ProductExtractionPipeline
import asyncio
import json

async def extract_products():
    pipeline = ProductExtractionPipeline()
    
    results = await pipeline.run_extraction_pipeline(
        "My Camera",
        "./camera_images"
    )
    
    print(json.dumps(results, indent=2))

# Run
asyncio.run(extract_products())
```

## 🚦 Performance Tips

1. **Use high-quality images** - Better images = better extraction
2. **Include product labels** - Dimensions/weight labels help
3. **Multiple images per product** - Front, back, details
4. **Check API quota** - Gemini API has rate limits
5. **Batch processing** - More efficient than single products

## 📝 Next Steps

1. ✅ Install and verify setup
2. ✅ Run with sample products
3. ✅ Review output quality
4. ✅ Adjust configuration if needed
5. ✅ Scale to production

## 💡 Pro Tips

- **Save API calls:** Results are deterministic, no need to re-run
- **Use CSV for spreadsheets:** Import directly to Excel/Sheets
- **Check confidence scores:** High scores = more reliable data
- **Monitor batch reports:** Track completion rates and improvement areas

## 🆘 Getting Help

1. Check output error messages (usually very descriptive)
2. Review `IMPLEMENTATION_GUIDE.md` for troubleshooting
3. Check agent instructions in `agents.py` comments
4. Verify API key and quotas at https://aistudio.google.com

## 📞 Support Resources

- **Agent Architecture:** `ADK_ARCHITECTURE.md`
- **Implementation Guide:** `IMPLEMENTATION_GUIDE.md`
- **Code Comments:** Throughout `agents.py`, `main.py`, `batch_processor.py`
- **Official Docs:** https://google.github.io/adk-docs/

---

**Ready to extract product attributes?** Run `streamlit run app.py` and get started! 🚀
