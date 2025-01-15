
# PDF to Markdown Conversion Pipeline

## Overview

This project implements an automated workflow to extract content from PDF files and convert it into Markdown format. The main functionalities include:
- Retrieving Mathpix API credentials from environment variables.
- Uploading PDF files to the Mathpix API for processing.
- Polling to check the conversion status of PDF files until completion or timeout.
- Downloading and saving the converted Markdown files to a specified directory.
- Retrieving a list of already processed papers.
- Iterating through the PDF folder, checking if files have been processed, and invoking the above steps for unprocessed files.

## Directory Structure

```
.
├── data
│   ├── pdf  # Folder containing PDF files to be processed
│   └── md   # Folder containing converted Markdown files
└── s1_pdf_2_md
        └── ocr_mathpix.py  # Main processing logic，PDF to Markdown conversion pipeline,for expensive ,and good performance 
        └── ocr_pymupdf.py  # PDF to text processing logic,for free, but not good performance
        └── readme.md       # Usage instructions
        └── readme_pymupdf.md  # PDF processing logic instructions
```


## Environment Configuration

Ensure the following environment variables are set:

```bash
export MATHPIX_APP_ID=your_app_id
export MATHPIX_APP_KEY=your_app_key
```


## Dependency Installation

Make sure you have the required Python libraries installed:

```bash
pip install pymupdf requests
```


## Usage Instructions

### Running the Script

To start the conversion process, run the following command in your terminal:

```bash
python ocr_mathpix.py
```


### Output Results

After running the script, converted Markdown files will be saved in the `data/md` directory, and the following information will be printed:

- `done_paper`: List of successfully converted PDF files.
- `no_response_paper`: List of PDF files that failed to process.
- `pages_more_50`: List of PDF files with more than 50 pages.

## Key Function Descriptions

### get_pdf_pages

Get the total number of pages in a PDF file.

```python
def get_pdf_pages(pdf_folder_dir, pdf_dir):
    """
    Get the total number of pages in a PDF file.

    Parameters:
    pdf_folder_dir: str - Directory of the PDF folder.
    pdf_dir: str - Name of the PDF file.

    Returns:
    int - Total number of pages in the PDF file, or None if the PDF cannot be read.
    """
```


### get_api_credentials

Retrieve Mathpix API credentials from environment variables.

```python
def get_api_credentials():
    """Retrieve Mathpix API credentials from environment variables"""
```


### upload_pdf_to_mathpix

Upload a PDF file to the Mathpix API.

```python
def upload_pdf_to_mathpix(pdf_file_path, headers, options):
    """Upload a PDF file to the Mathpix API"""
```


### check_conversion_status

Poll to check the conversion status of a PDF file.

```python
def check_conversion_status(pdf_id, headers, max_retries=30, retry_interval=5):
    """Poll to check the conversion status of a PDF file"""
```


### download_md_file

Download and save the converted Markdown file.

```python
def download_md_file(pdf_id, headers, output_dir, output_filename):
    """Download and save the converted Markdown file"""
```


### extract_pdf_mathpix

Integrate the above steps to complete the conversion from PDF to Markdown.

```python
def extract_pdf_mathpix(pdf_folder_dir, pdf_dir, md_folder_dir):
    """Extract content from a PDF file and convert it to Markdown format"""
```


### get_done_papers

Retrieve a list of already processed papers.

```python
def get_done_papers(md_folder_dir):
    """Retrieve a list of already processed papers"""
```


### process_pdfs

Iterate through the PDF folder, check if files have been processed, and invoke the above steps for unprocessed files.

```python
def process_pdfs(pdf_folder_dir, done_paper, md_folder_dir):
    """Iterate through the PDF folder, check if files have been processed, and invoke the above steps for unprocessed files"""
```


## Logging

Logging is configured using Python's `logging` module with the log level set to `INFO`. The log format is as follows:

```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```


Logs will record key information at each step, facilitating debugging and tracking issues.

---

By following these steps, you can easily convert PDF files to Markdown format and manage various scenarios during the conversion process. If you encounter any problems, refer to the code comments or contact the developer for assistance.