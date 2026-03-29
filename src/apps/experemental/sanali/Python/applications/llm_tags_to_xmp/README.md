# LLM Tags to XMP Tool

A command-line tool for automatically tagging images using the SmilingWolf WD-VIT-Tagger-v3 AI model and writing tags directly to XMP metadata.

## Features

✨ **AI-Powered Tagging** - Uses SmilingWolf/wd-vit-tagger-v3 for accurate image classification
📝 **Direct XMP Write** - Immediately writes tags to image files using exiftool
🔄 **Smart Deduplication** - Automatically merges with existing tags, no duplicates
⏸️ **Stop/Resume Support** - Can stop and restart processing (skips already tagged images)
📊 **Real-time Statistics** - Live progress tracking with processing speed
🚫 **Error Handling** - Continues processing even if individual files fail

## Tag Categories

Tags are organized with prefixes for easy categorization:

- `auto/wd_tag/*` - General image tags (e.g., `auto/wd_tag/1girl`, `auto/wd_tag/blue_eyes`)
- `auto/wd_characters/*` - Character names (e.g., `auto/wd_characters/hatsune_miku`)
- `auto/wd_rating/*` - Content ratings (e.g., `auto/wd_rating/safe`, `auto/wd_rating/questionable`)

## Installation

### 1. Install Dependencies

```bash
cd D:\Sanali209\Python\applications\llm_tags_to_xmp
pip install -r requirements.txt
```

### 2. Verify Exiftool

Ensure exiftool is available at: `D:\Sanali209\Python\SLM\exiftool.exe`

## Usage

### Running the Application

```bash
cd D:\Sanali209\Python\applications\llm_tags_to_xmp
pip install -r requirements.txt
```

#### Command Line Options

```bash
# Process specific folder with detailed output
python llm_xmp_tagger.py "D:\Images\dataset"

# Interactive mode (will prompt for folder path)
python llm_xmp_tagger.py

# Quiet mode (minimal output, only final statistics)
python llm_xmp_tagger.py --quiet "D:\Images\dataset"
```

#### Examples

```bash
# Direct path with verbose output
python llm_xmp_tagger.py "D:\Images\dataset"

# Interactive folder selection
python llm_xmp_tagger.py
# LLM XMP Tagger - AI-Powered Image Tagging Tool
# ============================================================
# 📂 Enter the folder path containing images to process:
#    (You can drag and drop the folder into the terminal)
# > D:\Images\dataset

# Quiet mode for batch processing
python llm_xmp_tagger.py --quiet "D:\Images\dataset"
```

### CLI Output Example

```
LLM XMP Tagger - AI-Powered Image Tagging Tool
📂 Scanning folder recursively: D:\Images\dataset
🖼️  Found 1234 image files (including subdirectories)

🤖 Loading AI model...
✅ Model loaded successfully

🚀 Processing 1234 files...
------------------------------------------------------------
[   1/1234] ✅ Processed: image_0001.jpg (+28 tags)
[   2/1234] ✅ Processed: image_0002.jpg (+32 tags)
[   3/1234] ⏭️  Skipped: image_0003.jpg (already tagged)
[   4/1234] ✅ Processed: image_0004.jpg (+15 tags)
...

PROCESSING COMPLETE - DETAILED REPORT
📁 Files Found:      1,234
✅ Processed:        1,200
⏭️  Skipped:          34 (already tagged)
🏷️  Tags Added:       35,890
❌ Errors:           0
⏱️  Time Elapsed:     245.67s
⚡ Speed:            4.9 files/sec
📊 Success Rate:     100.0%
```

### Workflow

1. **Enter Folder Path** - Provide as argument or interactively
2. **Scan** - Tool recursively scans for image files (.jpg, .png, .bmp, .gif, .webp)
3. **Check Duplicates** - Reads XMP metadata to detect existing WD tags
4. **Process** - Each new image is analyzed by AI model and tagged
5. **Write** - Tags are immediately written to XMP metadata with deduplication
6. **Report** - Detailed statistics and success metrics

## How It Works

1. **Scan**: Application scans the selected folder for image files
2. **Check**: Each image is checked for existing WD tagger tags (tags starting with `auto/wd_tag/`, `auto/wd_characters/`, or `auto/wd_rating/`)
3. **Skip**: Images that already have WD tags are skipped automatically
4. **Process**:
   - Load image and run through AI model
   - Extract general tags, character tags, and rating
   - Read existing XMP metadata
   - Merge new tags with existing (deduplicate)
   - Write immediately to XMP

## Reprocessing

If you want to reprocess images:

1. Use exiftool to remove the marker:
   ```bash
   exiftool -XMP:SLM-LLMProcessed= image.jpg
   ```

2. Or remove all auto tags:
   ```bash
   exiftool -XMP:Subject-=auto/wd_tag/* -XMP:Subject-=auto/wd_characters/* -XMP:Subject-=auto/wd_rating/* image.jpg
   ```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- WebP (.webp)

## Performance

- **CPU Mode**: ~0.5-1 files/sec
- **GPU Mode (CUDA)**: ~2-5 files/sec

First run will download the model (~500MB) from Hugging Face.

## Troubleshooting

### Model Download Fails
- Check internet connection
- Verify Hugging Face Hub is accessible
- Model will be cached in: `~/.cache/huggingface/hub/`

### XMP Write Fails
- Verify exiftool path in `D:\Sanali209\Python\SLM\exiftool.exe`
- Check file permissions
- Ensure images are not corrupted

### Application Crashes
- Check logs in activity log panel
- Verify all dependencies are installed
- Ensure sufficient disk space for model cache

## Technical Details

### Architecture

```
llm_xmp_tagger.py    - Main CLI application
tagger_engine.py     - SmilingWolf AI model integration
xmp_writer.py        - XMP metadata read/write operations
```

### XMP Fields Used

- `XMP:Subject` - Array of all tags (general, characters, rating)

### Dependencies

- **torch** - PyTorch for model inference
- **timm** - Image models library
- **Pillow** - Image processing
- **pandas** - Data processing for model labels
- **numpy** - Numerical operations
- **huggingface-hub** - Model downloading
- **loguru** - Logging

## Notes

- Processing is single-threaded to avoid XMP write conflicts
- Tags are written immediately after each image (no batch queue)
- Original files are preserved (exiftool creates temporary backups automatically)
- Model runs on GPU if available (CUDA), otherwise CPU

## License

Part of the Sanali209 project.
