# evaluate_extracted_data

This directory contains code for evaluating the extracted data.
The `evaluate_extracted_data.py` script is used to evaluate the extracted data from the LLM. It compares the extracted data with the ground truth data to assess the accuracy of the extraction process.

## Installation

Ensure the required dependencies are installed:

```bash
pip install -r requirements.txt
```
## Usage
To use this script, follow these steps:
1. Ensure that the extracted data is in the correct format and stored in the `response_dir` directory.
2. Run the `compare_value.py` script to compare the extracted data with the ground truth data of protein enzyme.
3. Run the `compare_value_bibozyme.py` script to compare the extracted data with the ground truth data of Ribozyme.

```shell
python compare_value.py
```
