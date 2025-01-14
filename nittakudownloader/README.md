```markdown
# NittakuDownloader

NittakuDownloader is a web scraping tool designed to extract product information from the Nittaku sports-related website. It downloads web pages, extracts relevant links and product details, and saves the extracted data into a CSV file.

## Overview

NittakuDownloader is built using Node.js and MongoDB, leveraging various libraries to handle web scraping, data extraction, and progress tracking. The project is organized into several modules, each responsible for a specific part of the scraping process:

- **Node.js**: JavaScript runtime for building the app.
- **MongoDB**: NoSQL database for storing data.
- **Express**: Web server framework for Node.js.
- **Cheerio**: Fast, flexible, and lean implementation of core jQuery designed specifically for the server.
- **TQDM**: Fast, extensible progress bar for loops and other operations.

The project structure is as follows:

- `nittaku_downloader.py`: Main script for downloading and processing data.
- `nittakulib/`: Contains modules for extracting links, product details, and handling various tasks.
  - `category_link_extractor.py`: Extracts category links from the main page.
  - `category_pages_link_extractor.py`: Extracts links to all category pages.
  - `constants.py`: Defines constants used throughout the project.
  - `product_attribute_extractor.py`: Extracts product attributes from HTML files.
  - `product_detail_link_extractor.py`: Extracts product detail links from category pages.
- `shared/`: Contains shared utilities and functions for downloading pages, managing directories, logging, and more.

## Features

- **Category Link Extraction**: Extracts category links from the main page.
- **Category Page Link Extraction**: Extracts links to all pages within a category.
- **Product Detail Link Extraction**: Extracts product detail links from category pages.
- **Product Attribute Extraction**: Extracts various product attributes such as name, description, variants, and images.
- **Image Downloading**: Downloads product images.
- **Data Export**: Exports extracted data to a CSV file.

## Getting Started

### Requirements

To run NittakuDownloader, ensure you have the following technologies set up on your computer:

- Node.js
- MongoDB (local installation or cloud version like MongoDB Atlas)
- Python 3.x
- Pip (Python package installer)

### Quickstart

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd nittakudownloader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**:
   - If using MongoDB Atlas, follow the instructions to create a cluster and get the connection string.
   - If using a local MongoDB instance, ensure it is running.

4. **Run the main script**:
   ```bash
   python nittaku_downloader.py
   ```

5. **Output**:
   - The script will download web pages, extract data, and save the results into a CSV file in the specified output folder.

### License

The project is proprietary.

```
Copyright (c) 2024.
```
```