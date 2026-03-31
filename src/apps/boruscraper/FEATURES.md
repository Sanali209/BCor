# Features

## Core Scraping Capabilities
- **Playwright Integration**: Uses `playwright` (sync API) for robust browser automation, handling dynamic content and JavaScript execution.
- **Configurable-Driven**: Entirely driven by JSON configuration files, allowing it to scrape different image board sites (e.g., Danbooru, Gelbooru, Rule34) without code changes.
- **Resumable Scraping**: Tracks pagination progress in a JSON file, allowing scraping to resume from where it left off after interruption.
- **Throttling & Delays**: Configurable delays between pages, topics, and downloads to be polite to servers and avoid bans.
    - initial manual action delay (e.g., for login).
    - random ranges for download delays.
    - extensive pauses after N pages.
- **CAPTCHA Detection**: Detects CAPTCHAs and pauses execution to allow for manual user solving.

## Data Extraction & Processing
- **Field Parsing**: Flexible field extraction using CSS selectors.
    - Supports text, resource URL (images/videos) extraction.
    - Regex filtering for extracted text.
    - Multi-value support (tags).
- **Resource Downloading**:
    - Downloads images/videos associated with posts.
    - **Smart De-duplication**: Uses MD5 hashing to prevent downloading duplicate files (even if filenames differ).
    - **Dual Download Strategy**: Tries API-based fetch first, falls back to browser navigation download if needed.
    - **Custom File Naming**: Pattern-based file naming using extracted metadata (e.g., `images/{topic_id}_{field_name}.{ext}`).
- **Metadata Handling**:
    - Extracts structured metadata: Tags (General, Character, Artist, Copyright, Metadata), Rating, Source.
    - **XMP Tagging**: Writes extracted tags directly into file metadata (XMP:Subject) using `MDManager` (if available).

## Caching & Performance
- **Disk Caching**: Uses `diskcache` to cache scraped topic data, preventing redundant processing of already scraped posts.
- **MD5 Cache**: Persistent cache of file hashes to skip downloading previously seen content across different sessions.

## Configuration
Supports detailed configuration via JSON files:
- **Selectors**: Define CSS selectors for pagination, topic previews, and links.
- **Fields**: Define what to scrape (Name, Selector, Type, Required, etc.).
- **Paths**: Customizable save paths and directory structures.
