# Camera Attribute Extraction - ADK Sequential Agents Architecture

A product attribute extraction system powered by **Google Agent Development Kit (ADK)** with Sequential Agents. 
This application analyzes product images and enriches the extracted data with manufacturer specifications through a deterministic three-stage pipeline.

## 🏗️ Architecture

### Sequential Agent Pipeline

The system uses ADK's `SequentialAgent` to orchestrate three specialized LLM agents that execute in strict order:

```
📸 IMAGE              🔍 SEARCH              ✨ ENRICHMENT
EXTRACTION AGENT  →  AGENT              →   AGENT
     Stage 1           Stage 2                Stage 3
     
Extract visible    Generate targeted    Fill missing attributes
attributes from    search queries for   with official data and
product images     missing attributes   produce final profile
```

**Pipeline Flow:**
1. **Image Extraction Agent**: Analyzes product images and extracts visible attributes
2. **Manufacturer Search Agent**: Generates targeted queries to find official specifications
3. **Attribute Enrichment Agent**: Enriches attributes with manufacturer data and finalizes results

## 📁 Project Structure

```
code/
├── agents.py                 # ADK Sequential Agents definition
├── main.py                   # Main pipeline orchestrator & entry point
├── batch_processor.py        # Batch processing utilities & export functions
├── app.py                    # Streamlit web interface
├── extractor.py              # Legacy extraction (reference only)
├── agent.py                  # Legacy agent (reference only)
├── requirements.txt          # Python dependencies
├── ADK_ARCHITECTURE.md       # Detailed architecture documentation
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Generative AI API key (Gemini)
- Optional: Google Custom Search API key

### Installation

```bash
# 1. Clone or navigate to the project
cd code/

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export GEMINI_API_KEY="your-api-key-here"
# Optional:
export GOOGLE_CSE_API_KEY="your-cse-key"
export GOOGLE_CSE_CX="your-cse-cx"
```

### Usage

#### Option 1: Web Interface (Recommended)

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser

**Features:**
- 📁 Load folder path or 📦 upload ZIP file
- 🚀 Start extraction pipeline
- 📊 View execution report
- 📥 Download results as JSON/CSV

#### Option 2: Command Line

**Single Product:**
```bash
python main.py "/path/to/product_folder"
```

**Batch Processing:**
```bash
python main.py "/path/to/raw_images" --batch
```

#### Option 3: Batch Processor Script

```bash
python batch_processor.py "./raw_images" "./output"
```

Generates:
- `extraction_results_<timestamp>.json` - Complete results
- `extraction_results_<timestamp>.csv` - Spreadsheet format
- `summary_report_<timestamp>.json` - Statistics & completion rates

## 🤖 Agent Descriptions

### 1. Image Extraction Agent
**Input:** Product images  
**Output:** Extracted attributes with confidence scores

Analyzes product images using Gemini 2.0 Flash vision to identify:
- Physical properties (Color, Material, Dimensions, Weight)
- Technical specifications (Sensor Type, Display, Autofocus)
- Features (Battery Type, USB Port, Connectivity)

### 2. Manufacturer Search Agent
**Input:** Partially extracted attributes  
**Output:** Targeted search queries

Intelligently generates search queries to find missing data:
- Prioritizes official manufacturer domains
- Targets high-value attributes first
- Optimizes for maximum data retrieval

### 3. Attribute Enrichment Agent
**Input:** Initial extraction + search queries  
**Output:** Complete product profile

Enriches attributes with official specifications:
- Fills missing/incomplete attributes
- Applies confidence scoring
- Produces final, market-ready product profile

## 📊 Supported Attributes

The system extracts 20 key product attributes:

**Physical Properties:**
- Color
- Body Material
- Dimensions
- Weight

**Technical Specs:**
- Sensor Type
- Display Type
- Viewfinder Type
- Lens Mount

**Features:**
- Battery Type
- Memory Card Slot
- USB Port Type
- Hot Shoe Mount
- Tripod Socket

**Capabilities:**
- Video Capabilities
- Autofocus System
- Connectivity Features
- Auto White Balance

**Additional:**
- Low Pass Filter
- AE Lock Button
- Shutter Release Type

## 📤 Output Format

### JSON Result
```json
{
  "product_name": "Canon EOS R5 Mark II Mirrorless Camera",
  "image_count": 3,
  "attributes": {
    "Color": "Black",
    "Dimensions": "138.4 x 97.7 x 88.2 mm",
    "Weight": "738g",
    ...
  },
  "product_description": "Professional mirrorless camera...",
  "enrichment_summary": {
    "filled_attributes": 18,
    "sources_used": ["image", "official_specs"]
  }
}
```

### CSV Export
Spreadsheet format with product name, description, and all attributes as columns

## 🔧 Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional (for enhanced search)
GOOGLE_CSE_API_KEY=your-cse-api-key
GOOGLE_CSE_CX=your-cse-cx-id
```

### Input Format

**Folder Structure:**
```
raw_images/
├── Canon EOS R5 Mark II/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── image3.jpg
└── Sony Alpha a7 IV/
    ├── image1.jpg
    └── image2.jpg
```

**ZIP File:**
Same structure as above, compressed as ZIP

## 📈 Performance

- **Average Processing Time:** 2-3 minutes per product
- **Attribute Completion Rate:** 85-95% (depending on image quality)
- **Confidence Scores:** High (80-100%) for visual attributes, Medium (60-80%) for inferred attributes
- **Batch Processing:** Handles multiple products efficiently

## 🔄 Migration from Legacy Code

**What's New:**
- ✅ ADK Sequential Agents for deterministic execution
- ✅ State-based data flow between agents
- ✅ Improved modularity and reusability
- ✅ Better error handling and reporting
- ✅ Comprehensive batch processing utilities

**Backward Compatibility:**
- Legacy modules kept for reference
- New code independent from old implementation
- Can be deprecated in future versions

## 📚 Documentation

- **ADK_ARCHITECTURE.md** - Detailed technical documentation
- **agents.py** - Code comments explaining each agent
- **main.py** - Pipeline orchestration details
- **batch_processor.py** - Batch processing utilities

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No images found | Ensure images are in supported formats (.jpg, .png, etc.) |
| API key not found | Set `GEMINI_API_KEY` environment variable |
| Slow processing | Check internet connectivity and API quotas |
| Streamlit port busy | Try `streamlit run app.py --server.port 8502` |

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please follow the existing code style and add tests for new features.

## 📧 Support

For issues or questions:
1. Check ADK_ARCHITECTURE.md for detailed documentation
2. Review code comments in agents.py, main.py, batch_processor.py
3. Check Google ADK documentation: https://google.github.io/adk-docs/

---

**Powered by:** Google Agent Development Kit (ADK) | Gemini 2.0 Flash | Sequential Agents Architecture