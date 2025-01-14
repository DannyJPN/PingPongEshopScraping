# GewoDownloader

GewoDownloader is a backend-focused application designed for extracting and processing product information from a website, likely for an e-commerce platform. The application performs web scraping tasks such as extracting category links, downloading category pages, extracting product detail links, and generating a CSV output with the collected product information.

## Overview

GewoDownloader is built using Python and leverages several libraries to accomplish its web scraping and data extraction tasks. The key technologies used in the project are:

- **Python**: The primary programming language used for the project.
- **beautifulsoup4**: A library for parsing HTML and XML documents.
- **requests**: A library for making HTTP requests.
- **tqdm**: A library for showing progress bars.

The project is organized into several scripts and modules, each responsible for specific tasks such as downloading pages, extracting links, and managing directories. The main script orchestrates the overall workflow, while the `gewolib` and `shared` directories contain various helper modules.

### Project Structure

- **README.md**: Provides an overview of the GewoDownloader project and instructions on how to set it up and run it.
- **gewo_downloader.py**: The main script that coordinates the downloading and processing of product information.
- **gewolib/**: Contains modules for extracting category links, category pages links, product detail links, and product attributes.
- **shared/**: Contains utility modules for downloading web pages, managing directories, loading HTML, and saving data to CSV.

## Features

GewoDownloader provides the following functionalities:

1. **Extract Category Links**: Extracts category links from the main page HTML.
2. **Download Category Pages**: Downloads the first pages of specified category URLs.
3. **Extract Category Pages Links**: Extracts links to all category pages from the downloaded first pages.
4. **Extract Product Detail Links**: Extracts product detail links from downloaded category pages.
5. **Download Product Detail Pages**: Downloads product detail pages from the extracted links.
6. **Extract Product Attributes**: Extracts various product attributes such as name, description, variants, and images.
7. **Generate CSV Output**: Saves the collected product information into a CSV file.

## Getting Started

### Requirements

To run GewoDownloader, you'll need the following:

- **Python 3.x**: Ensure you have Python 3.x installed on your machine.
- **beautifulsoup4**: Install using `pip install beautifulsoup4`.
- **requests**: Install using `pip install requests`.
- **tqdm**: Install using `pip install tqdm`.

### Quickstart

Follow these steps to set up and run GewoDownloader:

1. **Clone the Repository**:
   ```sh
   git clone <repository_url>
   cd GewoDownloader
   ```

2. **Install Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Main Script**:
   ```sh
   python gewo_downloader.py --output_folder <output_folder> --overwrite --debug
   ```

   - `--output_folder`: Specify the folder where the output files will be saved.
   - `--overwrite`: Optional flag to overwrite existing files.
   - `--debug`: Optional flag to enable debug logging.

### License

The project is proprietary (not open source). 

```
Copyright (c) 2024.
```