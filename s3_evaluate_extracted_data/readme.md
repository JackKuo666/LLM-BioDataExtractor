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
2. Run the `evaluate_extracted_data.py` script to compare the extracted data with the ground truth data.

```shell
python evaluate_extracted_data.py
```
## Parameters
The `evaluate_extracted_data.py` script takes the following parameters:
- `response_dir`: The directory containing the extracted data.
- `ground_truth_dir`: The directory containing the ground truth data.
- `output_dir`: The directory to save the evaluation results.
- `seq`: The delimiter used in the extracted data.
- `order`: The target column index in the extracted data.
- `have_dir`: Whether subdirectories exist in the extracted data.
- `prompt_dir`: The directory containing the prompt files.
- `prompt_name`: The name of the prompt file.
