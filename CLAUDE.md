# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desaka is a comprehensive Python-based e-commerce product data unification system that downloads, processes, and standardizes product information from multiple Czech and Slovak e-commerce websites. The system consists of two main components:

1. **E-shop Downloaders**: Individual web scrapers for specific e-commerce sites
2. **Desaka Unifier**: The main processing pipeline that consolidates and standardizes the data

**Note**: The `unifier/` directory is legacy code and should be deleted - it's no longer used.

## Architecture

### Main Unifier (desaka_unifier/)

The core processing system that orchestrates everything:

**Entry Point**: `unifier.py` - Main script that coordinates the entire pipeline
**Core Modules** (`unifierlib/`):
- `script_runner.py` - Manages parallel execution of downloader scripts
- `parser.py` - Product parsing with AI-powered data extraction
- `openai_client.py` & `openai_unifier.py` - OpenAI GPT integration
- `memory_manager.py` - Manages cached mappings and learned data
- `product_*.py` - Data models (DownloadedProduct → RepairedProduct → ExportProduct)
- `export_manager.py` - Exports to various e-commerce platforms

**Key Features**:
- Parallel execution of downloader scripts (configurable via `--MaxParallel`)
- AI-powered product data standardization using GPT-4o/GPT-4o-mini
- Memory system that caches user confirmations for AI suggestions
- Support for Czech (CS) and Slovak (SK) languages
- Export to 96-column format for major e-commerce platforms

### E-shop Downloaders

Each downloader follows a standardized pattern and architecture:

**Downloaders Available**:
- `gewodownloader/gewo_downloader.py` - Gewo.de (table tennis equipment)
- `nittakudownloader/nittaku_downloader.py` - Nittaku.com (table tennis)
- `pincesobchoddownloader/pincesobchod_downloader.py` - Pincesobchod.cz (general)
- `sportspindownloader/sport_spin_downloader.py` - SportSpin (table tennis)
- `stotendownloader/stoten_downloader.py` - Stoten.cz (table tennis)
- `vsenastolnitenisdownloader/vse_na_stolni_tenis_downloader.py` - VseNaStolniTenis.cz

**Shared Architecture Pattern**:
All downloaders follow the same 10-step process:

1. **Main Page Download**: Download the e-shop's main page
2. **Category Link Extraction**: Extract category URLs from main page
3. **Category First Pages**: Download first page of each category
4. **Category Pagination**: Extract and download all category pages (with pagination)
5. **Product Link Extraction**: Extract all product detail page URLs
6. **Product Detail Download**: Download individual product pages
7. **Variant Handling**: Download product variant pages (if applicable)
8. **Data Extraction**: Extract product attributes from HTML
9. **Image Download**: Download main and gallery images
10. **CSV Export**: Export to standardized CSV format

**Shared Modules** (in each `*/shared/` directory):
- `main_page_downloader.py` - Downloads main website page
- `category_*_downloader.py` - Category page downloading logic
- `product_detail_page_downloader.py` - Product page downloading
- `product_image_downloader.py` - Image downloading functionality
- `html_loader.py` - HTML parsing utilities
- `logging_config.py` - Logging setup
- `utils.py` - Common utilities (date folders, filename generation)
- `product_to_eshop_csv_saver.py` - CSV export functionality

**Site-Specific Modules** (in each `*/[site]lib/` directory):
- `constants.py` - Site-specific URLs, filenames, selectors
- `category_link_extractor.py` - CSS selectors for category extraction
- `product_detail_link_extractor.py` - Product URL extraction logic
- `product_attribute_extractor.py` - Product data extraction from HTML
- `category_pages_link_extractor.py` - Pagination handling

## Data Flow

### 1. Download Phase
Each downloader runs independently and produces:
- **Raw HTML files**: Organized in dated folders (e.g., `H:/Desaka/Nittaku/2024-08-21/`)
- **CSV export**: Standardized product data in `*Output.csv`
- **Images**: Product photos in structured directories
- **Logs**: Debug information in `H:/Logs/`

### 2. Unification Phase  
The main unifier processes all downloader outputs:

**Data Pipeline**:
1. `DownloadedProduct` objects (from CSV files)
2. → `RepairedProduct` objects (AI-cleaned and standardized)
3. → Product merging (handle duplicates and variants)
4. → Product filtering (business rules, quality checks)
5. → `ExportProduct` objects (96-column format for platforms)
6. → Final export (Zbozi.cz, Heureka.cz, Google Shopping, Glami)

### 3. Memory System
Caches AI decisions and user confirmations:
- `NameMemory_*.csv` - Product name standardizations
- `ProductBrandMemory_*.csv` - Brand classifications  
- `ProductTypeMemory_*.csv` - Product type mappings
- `CategoryMemory_*.csv` - Category classifications
- `KeywordsGoogle_*.csv` / `KeywordsZbozi_*.csv` - SEO keywords

## Common Development Tasks

### Running Individual Downloaders

```bash
# All downloaders use the same parameter pattern
cd [downloader_directory]
python [downloader_script].py --result_folder H:/Desaka --debug --overwrite

# Examples:
cd gewodownloader
python gewo_downloader.py --result_folder H:/Desaka --debug

cd nittakudownloader  
python nittaku_downloader.py --result_folder H:/Desaka --debug

# Pincesobchod is special - requires country code instead of language
cd pincesobchoddownloader
python pincesobchod_downloader.py --result_folder H:/Desaka/Pincesobchod_CS --country_code CZ --debug
```

**Common Downloader Parameters**:
- `--result_folder` - Output directory (creates dated subdirectories)
- `--debug` - Enable debug logging to console and file
- `--overwrite` - Overwrite existing downloaded files
- `--country_code` - Only for Pincesobchod (CZ/SK)

### Running the Main Unifier

```bash
cd desaka_unifier
python unifier.py --Language CS --Debug
```

**Key Unifier Parameters**:
- `--Language CS/SK` - Target language (Czech/Slovak)
- `--Debug` - Enable debug logging
- `--SkipScripts` - Skip downloader execution, process existing data only
- `--SkipAI` - Skip AI processing (use cached memory only)
- `--ConfirmAIResults` - Auto-confirm AI suggestions without user prompts
- `--MaxParallel 3` - Number of parallel downloader processes
- `--ResultDir H:/Desaka` - Input directory with downloader results
- `--ExportDir H:/Desaka/Results` - Output directory for final exports
- `--EnableFineTuning` - Enable OpenAI model fine-tuning
- `--UseFineTunedModels` - Use custom fine-tuned models

### Memory System Management

```bash
cd desaka_unifier
python memory_checker.py --language CS
```

This validates and repairs memory files, ensuring data consistency across:
- Brand mappings against BrandCodeList.csv
- Product types don't contain brand names
- Keyword format validation (Google: 5 keywords, Zbozi: 2 keywords)
- Name memory updates based on corrected Type/Brand/Model values

## Directory Structure and File Organization

### Downloaders
Each downloader creates this structure:
```
H:/Desaka/[EshopName]/[YYYY-MM-DD]/
├── MainPage/               # Main website pages
├── CategoryPages/          # Category listing pages  
├── ProductDetailPages/     # Individual product pages
├── Images/                 # Product photos
│   ├── MainImages/        # Primary product images
│   └── GalleryImages/     # Additional product photos
└── [EshopName]Output.csv  # Standardized product data
```

### Unifier Memory System
```
desaka_unifier/Memory/
├── *Memory_CS.csv         # Language-specific cached data
├── *Memory_SK.csv         # Slovak language data
├── BrandCodeList.csv      # Master brand mappings
├── CategoryCodeList.csv   # Category definitions
├── EshopList.csv          # Downloader configuration
├── ItemFilter.csv         # Product filtering rules
└── Wrongs.txt            # Rejected products log
```

### Configuration Files
- `desaka_unifier/Config/SupportedLanguages.csv` - Language settings
- `desaka_unifier/requirements.txt` - Python dependencies  
- Each downloader has site-specific constants in `[site]lib/constants.py`

## AI Integration Details

The system uses OpenAI GPT models for intelligent data processing:

**Model Selection**:
- `gpt-4o` - Complex tasks (category classification, name standardization)
- `gpt-4o-mini` - Simple tasks (keyword generation, basic parsing)

**AI Tasks**:
- Product name standardization and translation
- Brand and product type detection
- Category classification (maps to Czech/Slovak category trees)
- SEO keyword generation (Google: 5 keywords, Zbozi: 2 keywords)
- HTML description cleaning and enhancement
- Variant handling and normalization

**Memory Behavior**:
- All AI suggestions require user confirmation (unless `--ConfirmAIResults`)
- Confirmed mappings are cached for future use
- System can run offline using cached data (`--SkipAI`)
- Fine-tuning capability improves AI accuracy over time

## Parallel Processing and Performance

### Downloader Execution
- Managed by `script_runner.py` in the unifier
- Configurable parallelism (`--MaxParallel`, default: 3)
- Each downloader runs in separate process with own logging
- Progress tracking with `tqdm` progress bars
- Graceful shutdown on Ctrl+C

### Script Runner Specifics
The `ScriptRunner` class handles:
- Path resolution for relative script paths (handles `../` correctly)
- Parameter mapping (most use `--result_folder`, Pincesobchod uses `--country_code`)
- Process monitoring and error handling
- Result directory naming conventions
- Cross-platform subprocess management

## Development Notes

### Downloader Development Pattern
When working on downloaders, note the shared pattern:
1. All use same argument parsing (`--result_folder`, `--debug`, `--overwrite`)
2. All follow the 10-step process outlined above
3. Site-specific logic is isolated in `[site]lib/` modules
4. Shared functionality is in `shared/` modules
5. HTML extraction uses CSS selectors defined in constants
6. Error handling and logging are standardized

### Memory File Format
- CSV format with consistent structure across languages
- Timestamps for tracking changes
- Backup files (`.csv_old`) for rollback capability
- Language suffixes (`_CS`, `_SK`) for localization

### Testing and Debugging
- Individual downloaders can be tested independently
- Unifier can process existing data without re-downloading (`--SkipScripts`)
- Debug logging provides detailed execution traces
- Memory checker validates data integrity
- Rejected products are logged with reasons

### Configuration
- Default paths use H:/ drive (configurable via constants)
- OpenAI API key required for AI features
- Locale-aware text processing for Czech/Slovak languages
- Platform-specific export formats (96 columns)

## File Naming Conventions

- Downloaders: `[site]_downloader.py`
- Constants: Site-specific in `[site]lib/constants.py`
- Shared modules: Descriptive names in `shared/`
- Memory files: `[Type]Memory_[Language].csv`
- Export files: `[EshopName]Output.csv`
- Logs: Timestamped in `H:/Logs/`