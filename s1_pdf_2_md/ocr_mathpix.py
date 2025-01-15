import os
import fitz
import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_pdf_pages(pdf_folder_dir, pdf_dir):
    """
    Get the number of pages in a PDF file.

    Parameters:
    pdf_folder_dir: str - The directory of the PDF folder.
    pdf_dir: str - The name of the PDF file.

    Returns:
    int - The total number of pages in the PDF file, or None if the PDF cannot be read.
    """
    # Construct the full path to the PDF file
    path = pdf_folder_dir + "/" + pdf_dir

    # Attempt to open the PDF file
    try:
        doc = fitz.open(path)
    except:
        # If the file cannot be opened, print an error message and return None
        print("can not read pdf")
        return None

    # Get and return the number of pages in the PDF file
    page_count = doc.page_count

    return page_count


def get_api_credentials():
    """Retrieve Mathpix API credentials from environment variables"""
    APP_ID = os.getenv('MATHPIX_APP_ID')
    print(APP_ID)
    APP_KEY = os.getenv('MATHPIX_APP_KEY')
    if not APP_ID or not APP_KEY:
        raise ValueError("Please set MATHPIX_APP_ID and MATHPIX_APP_KEY environment variables")
    return APP_ID, APP_KEY

def upload_pdf_to_mathpix(pdf_file_path, headers, options):
    """Upload the PDF file to Mathpix API"""
    url = 'https://api.mathpix.com/v3/pdf'
    with open(pdf_file_path, 'rb') as pdf_file:
        files = {
            'file': pdf_file,
            'options_json': (None, json.dumps(options))
        }
        response = requests.post(url, headers=headers, files=files)
    return response


def check_conversion_status(pdf_id, headers, max_retries=30, retry_interval=5):
    """Check the conversion status with a maximum number of retries and interval"""
    status_url = f'https://api.mathpix.com/v3/pdf/{pdf_id}'
    retries = 0

    while retries < max_retries:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        conversion_status = status_data.get('status', 'unknown')
        logging.info(f"conversion_status: {conversion_status}")

        # Log the full response data for debugging purposes
        logging.debug(f"Full conversion status response: {status_data}")

        if conversion_status == 'completed':
            break
        elif conversion_status in ['loaded', 'split', 'processing']:
            logging.info(f"Conversion is {conversion_status}, waiting for processing to complete.")
            time.sleep(retry_interval)
            retries += 1
            continue
        else:
            raise ValueError(f"Conversion failed, status: {conversion_status}")

        logging.info('Processing... Please wait.')
        time.sleep(retry_interval)
        retries += 1

    if retries >= max_retries:
        raise TimeoutError("Conversion did not complete within the allowed time.")


def download_md_file(pdf_id, headers, output_dir, output_filename):
    """Download and save the Markdown file"""
    md_url = f'https://api.mathpix.com/v3/pdf/{pdf_id}.md'
    md_response = requests.get(md_url, headers=headers)
    if md_response.status_code == 200:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write(md_response.text)
        logging.info(f"OCR result saved to: {output_path}")
        return md_response.text
    else:
        logging.error('Failed to download Markdown file.')
        return None


def extract_pdf_mathpix(pdf_folder_dir, pdf_dir, md_folder_dir):
    """
    Extract content from a PDF file and convert it to Markdown format
    """
    try:
        # Retrieve API credentials
        APP_ID, APP_KEY = get_api_credentials()

        # Build the PDF file path
        pdf_file_path = os.path.join(pdf_folder_dir, pdf_dir)
        logging.info(f"pdf_file_path: {pdf_file_path}")

        # Check if the file exists
        if not os.path.exists(pdf_file_path):
            raise FileNotFoundError(f"File {pdf_file_path} does not exist")

        # Set request headers and options
        headers = {
            'app_id': APP_ID,
            'app_key': APP_KEY,
        }
        options = {
            "conversion_formats": {
                "md": True
            },
            "math_inline_delimiters": ["$", "$"],
            "rm_spaces": True
        }

        # Upload the PDF file
        response = upload_pdf_to_mathpix(pdf_file_path, headers, options)
        if response.status_code != 200:
            logging.error(f'Failed to upload PDF. Status code: {response.status_code}')
            return None

        # Get the PDF ID
        pdf_id = response.json().get('pdf_id')
        logging.info(f"pdf_id: {pdf_id}")

        # Check the conversion status
        check_conversion_status(pdf_id, headers)

        # Download and save the Markdown file
        output_filename = os.path.splitext(pdf_dir)[0] + ".md"
        return download_md_file(pdf_id, headers, md_folder_dir, output_filename)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None


def get_done_papers(md_folder_dir):
    done_paper = []
    if os.path.exists(md_folder_dir):
        try:
            done_paper = [i.replace(".md", ".pdf") for i in os.listdir(md_folder_dir)]
        except (FileNotFoundError, PermissionError) as e:
            print(f"Error reading md folder: {e}")
    return done_paper


def process_pdfs(pdf_folder_dir, done_paper, md_folder_dir):
    no_response_paper = []
    pages_more_50 = []

    try:
        pdf_files = [i for i in os.listdir(pdf_folder_dir) if i.endswith("pdf")]
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error reading pdf folder: {e}")
        return no_response_paper, pages_more_50, done_paper

    for pdf_file in pdf_files:
        if pdf_file not in done_paper + no_response_paper + pages_more_50:
            try:
                pages = get_pdf_pages(pdf_folder_dir, pdf_file)
                print(f"\nstart: {pdf_file} have pages: {pages}")

                if pages <= 50:
                    print(f"start convert pdf 2 md: {pdf_file}")
                    content = extract_pdf_mathpix(pdf_folder_dir, pdf_file, md_folder_dir)
                    if content:
                        done_paper.append(pdf_file)
                    else:
                        no_response_paper.append(pdf_file)
                else:
                    pages_more_50.append(pdf_file)
                    print(f"pages_more_50: {pages_more_50}")
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")

    return no_response_paper, pages_more_50, done_paper


if __name__ == '__main__':
    data_folder_dir = "../data/"
    pdf_folder_dir = os.path.join(data_folder_dir, "pdf")
    md_folder_dir = os.path.join(data_folder_dir, "md")

    done_paper = get_done_papers(md_folder_dir)
    print("done_paper:", done_paper)

    no_response_paper, pages_more_50, done_paper = process_pdfs(pdf_folder_dir, done_paper, md_folder_dir)
    print("done_paper:", done_paper)
    print("no_response_paper:", no_response_paper)
    print("pages_more_50:", pages_more_50)
