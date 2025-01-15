import os
import fitz  # PyMuPDF
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
    path = os.path.join(pdf_folder_dir, pdf_dir)

    # Attempt to open the PDF file
    try:
        doc = fitz.open(path)
    except Exception as e:
        # If the file cannot be opened, print an error message and return None
        logging.error(f"Cannot read PDF: {e}")
        return None

    # Get and return the number of pages in the PDF file
    page_count = doc.page_count

    return page_count


def extract_text_from_pdf(pdf_file_path, output_dir, output_filename):
    """
    Extract text from a PDF file and save it as a text file using PyMuPDF.

    Parameters:
    pdf_file_path: str - The path to the PDF file.
    output_dir: str - The directory to save the output text file.
    output_filename: str - The name of the output text file.
    """
    try:
        # Open the PDF file
        doc = fitz.open(pdf_file_path)

        # Initialize an empty string to store the extracted text
        text = ""

        # Iterate through each page and extract text
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")

        # Save the extracted text to a text file
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write(text)
        logging.info(f"OCR result saved to: {output_path}")

        return text

    except Exception as e:
        logging.error(f"An error occurred during OCR: {e}")
        return None


def get_done_papers(txt_folder_dir):
    done_paper = []
    if os.path.exists(txt_folder_dir):
        try:
            done_paper = [i.replace(".txt", ".pdf") for i in os.listdir(txt_folder_dir)]
        except (FileNotFoundError, PermissionError) as e:
            logging.error(f"Error reading txt folder: {e}")
    return done_paper


def process_pdfs(pdf_folder_dir, done_paper, txt_folder_dir):
    no_response_paper = []
    pages_more_50 = []

    try:
        pdf_files = [i for i in os.listdir(pdf_folder_dir) if i.endswith("pdf")]
    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"Error reading pdf folder: {e}")
        return no_response_paper, pages_more_50, done_paper

    for pdf_file in pdf_files:
        if pdf_file not in done_paper + no_response_paper + pages_more_50:
            try:
                pages = get_pdf_pages(pdf_folder_dir, pdf_file)
                logging.info(f"start: {pdf_file} have pages: {pages}")

                if pages <= 50:
                    logging.info(f"start convert pdf 2 txt: {pdf_file}")
                    output_filename = os.path.splitext(pdf_file)[0] + ".txt"
                    content = extract_text_from_pdf(os.path.join(pdf_folder_dir, pdf_file), txt_folder_dir, output_filename)
                    if content:
                        done_paper.append(pdf_file)
                    else:
                        no_response_paper.append(pdf_file)
                else:
                    pages_more_50.append(pdf_file)
                    logging.info(f"pages_more_50: {pages_more_50}")
            except Exception as e:
                logging.error(f"Error processing {pdf_file}: {e}")

    return no_response_paper, pages_more_50, done_paper


if __name__ == '__main__':
    data_folder_dir = "../data/"
    pdf_folder_dir = os.path.join(data_folder_dir, "pdf")
    txt_folder_dir = os.path.join(data_folder_dir, "txt")

    done_paper = get_done_papers(txt_folder_dir)
    logging.info(f"done_paper: {done_paper}")

    no_response_paper, pages_more_50, done_paper = process_pdfs(pdf_folder_dir, done_paper, txt_folder_dir)
    logging.info(f"done_paper: {done_paper}")
    logging.info(f"no_response_paper: {no_response_paper}")
    logging.info(f"pages_more_50: {pages_more_50}")
