# VseNaStolniTenisDownloader

VseNaStolniTenisDownloader is a backend service for extracting and processing data from a table tennis-related website. The application focuses on downloading HTML files, parsing them to extract specific information, and converting the data into structured formats for further use.

## Overview

This project is designed as a backend service that processes HTML files to extract specific information related to table tennis products. The architecture is centered around a set of Python scripts organized in a library (`vsenastolnitenislib`). These scripts handle various tasks such as extracting URLs, parsing product details, and converting JavaScript data to Python data structures. The application does not require a frontend or a database, as it is solely focused on data extraction and processing.

### Technologies Used

- **Python**: The programming language used for the backend service.
- **beautifulsoup4**: Library for parsing HTML and XML documents.
- **requests**: Library for making HTTP requests in Python.
- **lxml**: Library for processing XML and HTML in Python.

### Project Structure

- **README.md**: Provides an overview and detailed documentation of the project.
- **shared**: Contains utility scripts for downloading webpages, managing directories, and logging.
- **vsenastolnitenislib**: Contains scripts for extracting category links, category pages, product details, and product attributes.
- **vse_na_stolni_tenis_downloader.py**: Main script that orchestrates the entire data extraction and processing workflow.

## Features

- **URL Extraction**: Extracts category, page, and product detail URLs from HTML files.
- **HTML Parsing**: Parses HTML files to extract specific product attributes such as name, description, price, and images.
- **JavaScript Data Conversion**: Converts JavaScript data structures embedded in HTML files to Python data structures.
- **Data Export**: Exports the extracted data to a CSV file for further use.
- **Image Downloading**: Downloads product images and stores them locally.

## Getting Started

### Requirements

To run this project, you need the following technologies and setups on your computer:

- Python 3.x
- pip (Python package installer)

### Quickstart

1. **Clone the repository**:
    ```sh
    git clone https://your-repository-url.git
    cd your-repository-name
    ```

2. **Install the dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Run the script**:
    ```sh
    python vse_na_stolni_tenis_downloader.py
    ```

### License

The project is proprietary (not open source). 

```
Copyright (c) 2024.
```