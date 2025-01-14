```markdown
# StotenDownloader

StotenDownloader is a Node.js application designed for web scraping specific data from HTML files. The application extracts category links, product names, descriptions, prices, and photo links from product pages. It processes the extracted data and returns it in the required formats.

## Overview

StotenDownloader is a backend-focused project that utilizes Node.js for server-side logic. The primary functions include extracting category links, product names, descriptions, prices, and photo links from product pages. The architecture includes modules for each type of extraction, with helper functions as needed to ensure clean and maintainable code.

### Technologies Used

- **Node.js**: JavaScript runtime for building the application.
- **express**: Web server framework for Node.js.
- **mongodb**: MongoDB driver for Node.js.
- **cheerio**: Fast, flexible, and lean implementation of core jQuery for server-side HTML parsing.
- **fs-extra**: File system methods that aren't included in the native fs module and adds promise support.

### Project Structure

The project is organized into several modules, each handling a specific part of the scraping process:

- `stoten_downloader.py`: The main script that orchestrates the entire scraping and downloading process.
- `shared/`: Contains shared utilities and modules for downloading and processing web pages.
  - `category_firstpage_downloader.py`: Downloads the first pages of categories.
  - `category_pages_downloader.py`: Downloads all category pages.
  - `directory_manager.py`: Ensures the necessary directory structure is in place.
  - `html_loader.py`: Loads HTML content as a DOM tree.
  - `image_downloader.py`: Downloads images.
  - `logging_config.py`: Configures logging.
  - `main_page_downloader.py`: Downloads the main page.
  - `product_detail_page_downloader.py`: Downloads product detail pages.
  - `product_image_downloader.py`: Downloads product images.
  - `product_to_eshop_csv_saver.py`: Exports product data to CSV.
  - `utils.py`: Contains utility functions.
  - `webpage_downloader.py`: Handles downloading of web pages.
- `stotenlib/`: Contains library modules specific to StotenDownloader.
  - `category_link_extractor.py`: Extracts category links from the main page.
  - `category_pages_link_extractor.py`: Extracts links to all category pages.
  - `constants.py`: Defines constants used across the project.
  - `product_attribute_extractor.py`: Extracts various attributes of products.
  - `product_detail_link_extractor.py`: Extracts product detail links from category pages.

## Features

StotenDownloader can:

- Ensure the required directory structure exists.
- Download the main page.
- Extract and download category first pages.
- Extract and download all category pages.
- Extract product detail links from category pages.
- Download product detail pages.
- Extract various attributes of products (e.g., name, description, price, images).
- Download product images.
- Serialize product data into a CSV file.

## Getting Started

### Requirements

To run the project, you need the following technologies installed on your computer:

- Node.js
- npm (Node package manager)

### Quickstart

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install the required Node.js packages**:
    ```sh
    npm install
    ```

3. **Run the script**:
    ```sh
    node stoten_downloader.js --result_folder <path-to-result-folder> --overwrite --debug
    ```

    - `--result_folder`: Defines the root folder for the script's output. Default value is `H:/Desaka/Stoten`.
    - `--overwrite`: Optional flag to overwrite existing downloaded resources.
    - `--debug`: Optional flag to enable console logging of non-errors.

### License

The project is proprietary (not open source). Copyright (c) 2024.
```
