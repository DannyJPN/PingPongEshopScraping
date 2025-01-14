# SportSpinDownloader

SportSpinDownloader is a Python script designed to scrape the Sportspin.cz website for various product details. The script downloads web pages, extracts product information, and saves the data into a structured CSV file. It also handles image downloads for each product, organizing them into a specified directory structure.

## Overview

SportSpinDownloader is built using Python and leverages several libraries to perform its tasks:
- **requests**: For making HTTP requests.
- **beautifulsoup4**: For parsing HTML and XML documents.
- **lxml**: Used by BeautifulSoup for processing XML and HTML.
- **tqdm**: For displaying progress bars.

The project structure is organized into several modules, each responsible for a specific part of the scraping process:

- `sport_spin_downloader.py`: The main script orchestrating the entire scraping process.
- `shared/`: Contains utility scripts for downloading pages, managing directories, and handling images.
- `sportspinlib/`: Contains scripts for extracting links and product attributes from the HTML content.

## Features

SportSpinDownloader includes the following features:
1. **Directory Structure Management**: Ensures the necessary directories exist for storing downloaded content.
2. **Web Page Downloading**: Downloads the main page, category pages, and product detail pages.
3. **HTML Parsing**: Loads HTML content as DOM trees for further processing.
4. **Link Extraction**: Extracts category and product detail links from the HTML content.
5. **Product Extraction**: Extracts detailed product information such as name, descriptions, prices, and images.
6. **Image Downloading**: Downloads main and gallery images for each product.
7. **CSV Export**: Exports the collected product data into a structured CSV file.

## Getting Started

### Requirements

To run SportSpinDownloader, you need the following technologies installed on your computer:
- Python 3.x
- pip (Python package installer)

Additionally, the following Python libraries are required:
- requests
- beautifulsoup4
- lxml
- tqdm

### Quickstart

1. **Clone the repository**:
   ```sh
   git clone <repository-url>
   cd SportSpinDownloader
   ```

2. **Install the required libraries**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Run the script**:
   ```sh
   python sport_spin_downloader.py --result_folder <path_to_result_folder> --overwrite <True_or_False> --debug <True_or_False>
   ```

   - `result_folder`: The root folder for the script's output. Default is `H:/Desaka/SportSpin`.
   - `overwrite`: Boolean value indicating if the downloaded resources should be replaced. Default is `False`.
   - `debug`: Boolean value indicating if console logging for non-errors should be enabled. Default is `False`.

### License

The project is proprietary (not open source).

```
Copyright (c) 2024.
```