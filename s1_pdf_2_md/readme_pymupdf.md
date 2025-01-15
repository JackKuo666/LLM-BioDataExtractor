# OCR using PyMuPDF

## Overview
`ocr_pymupdf.py` is a Python script that uses the PyMuPDF (also known as `fitz`) library to extract text from PDF files and save it as plain text files.

## Dependencies
Before running this script, ensure you have the following dependencies installed:
- `PyMuPDF` (`fitz`)

You can install the required library using the following command:

```bash
pip install pymupdf
```
## Usage
### Basic Usage
Place your scientific literature PDF files in the `data/pdf/` directory, then run the script:


```bash
python ocr_pymupdf.py
```

### Directory Structure
- `data/pdf/`: Directory for input PDF files.
- `data/txt/`: Directory for output plain text files.

### Logging
The script uses the `logging` module to log information, warnings, and errors. The log format is:


```sh
%(asctime)s - %(levelname)s - %(message)s
```
## Function Descriptions
### `get_pdf_pages(pdf_folder_dir, pdf_dir)`
Get the number of pages in a PDF file.

### `extract_text_from_pdf(pdf_file_path, output_dir, output_filename)`
Extract text from a PDF file and save it as a plain text file.

### `get_done_papers(txt_folder_dir)`
Get a list of PDF files that have already been processed.

### `process_pdfs(pdf_folder_dir, done_paper, txt_folder_dir)`
Process PDF files, extract text, and save it as plain text files.

## Notes
- Ensure that PDF files are located in the `data/pdf/` directory.
- Output plain text files will be saved in the `data/txt/` directory.
- The script will skip PDF files that have already been processed.
- PDF files with more than 50 pages will be skipped and logged in the `pages_more_50` list.
