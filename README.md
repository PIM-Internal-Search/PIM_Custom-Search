# Product Attribute Extraction App

**Simplified architecture using Google ADK Sequential Agents**

## Overview

This application automatically extracts product attributes from images using a two-agent sequential pipeline:

1. **Image Analysis Agent** - Analyzes product images and extracts 20+ attributes
2. **Search Enhancement Agent** - Enhances attributes using Google Custom Search API

## Features

- 🖼️ **Automatic Attribute Extraction** - Extracts 20+ camera attributes from images
- 🔍 **Search Enhancement** - Uses Google Custom Search to fill missing attributes
- 📝 **E-commerce Descriptions** - Generates compelling product descriptions
- 📊 **Batch Processing** - Process multiple products at once
- 💾 **Export Results** - Download as JSON or CSV
- 🎨 **Clean UI** - Streamlit interface with folder selection

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config.py` with your API keys:

```python
GEMINI_API_KEY = "your-gemini-api-key"
GOOGLE_CSE_API_KEY = "your-google-cse-api-key"
GOOGLE_CSE_CX = "your-custom-search-engine-id"
```

### 3. Prepare Product Images

Organize your product images in this structure:

```
raw_images/
├── Product 1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── Product 2/
│   ├── image1.jpg
│   └── ...
└── ...
```

## Usage

### Streamlit UI (Recommended)

```bash
streamlit run streamlit_app.py
```

Then:
1. Enter the path to your `raw_images` folder
2. Click "Load Folder"
3. Click "Start Attribute Extraction"
4. View results and download as JSON/CSV

### Command Line

**Single Product:**
```bash
python pipeline.py "c:\path\to\product_folder"
```

**Batch Processing:**
```bash
python pipeline.py "c:\path\to\raw_images" --batch
```

## Extracted Attributes

The system extracts 22 camera attributes:

**Physical:**
- Color, Body Material, Dimensions, Weight

**Specifications:**
- Sensor Type, Sensor Size, Megapixels, ISO Range
- Lens Mount, Viewfinder Type, Display Type, Display Size

**Features:**
- Autofocus System, Video Capabilities, Connectivity Features
- Battery Type, Memory Card Slot, USB Port Type, Hot Shoe Mount
- Image Stabilization, Shutter Speed Range, Continuous Shooting Speed

## Architecture

```
┌─────────────────────┐
│  Product Images     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Image Analysis      │
│ Agent               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Search Enhancement  │
│ Agent               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Final Attributes    │
│ + Description       │
└─────────────────────┘
```

## Files

- `config.py` - API key configuration
- `agents.py` - Google ADK sequential agent definitions
- `pipeline.py` - Pipeline orchestrator and batch processor
- `streamlit_app.py` - Streamlit UI application
- `requirements.txt` - Python dependencies

## Backup

The previous complex implementation has been backed up to `code_backup/` folder.

## License

MIT
