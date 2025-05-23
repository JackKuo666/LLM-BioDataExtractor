# 1.LLM Data Extraction Pipeline

## Overview
`LLM_data_extraction.py` is a Python script designed for extracting information from scientific literature. The script leverages OpenAI's GPT models to process and extract key information from text, while also removing the references section from the literature.

## Dependencies
Before running the script, ensure the following dependencies are installed:
- `openai`
- `tiktoken`
- `re`
- `time`
- `os`
- `logging`

Install the required libraries using:
```bash
pip install openai tiktoken
```

## Environment Variables
The script relies on the following environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key.
- `OPENAI_BASE_URL`: Base URL for the OpenAI API (optional, default: `https://api.openai.com`).

Set these environment variables before running the script:
```bash
export OPENAI_API_KEY=your_openai_api_key
export OPENAI_BASE_URL=https://api.openai.com
```

## Usage
### Basic Usage
Place Markdown files of scientific literature in the `data/md/` directory, then run the script:
```bash
python LLM_data_extraction.py
```

### Parameters
- `md_dir`: Directory containing the Markdown files (default: `data/md/`).
- `response_folder`: Directory to save responses (default: `data/response/`).
- `model`: The GPT model to use (default: `claude-3-5-sonnet-20240620`).
- `temperature`: Controls randomness in text generation (default: `0.1`).
- `prompt_dir`: Directory for the prompt file (default: `prompt/p_3_2_0806.txt`).
- `max_tokens`: Maximum number of tokens to generate (default: `8192`).

### Example
Suppose you have a file named `example.md` in the `data/md/` directory. Run the script as follows:
```bash
python LLM_data_extraction.py
```
The script processes `example.md`, removes its references section, and extracts key information using the GPT model. The extracted results are saved in the `data/response/` directory.

## Logging
The script uses the `logging` module to record information, warnings, and errors. The log format is:
```sh
%(asctime)s - %(levelname)s - %(message)s
```

## Function Descriptions
### `num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")`
Calculates the number of tokens used by a list of messages.

### `del_references(file_name, md_folder)`
Removes the references section from a Markdown file.

### `chat_1_step(model, messages, temperature, max_tokens, new_dir, md_dir, response_folder)`
Performs a single-step chat completion operation.

### `chat_2_step(md_dir, file_content, response_folder, model, temperature, new_dir, prompt_extract, max_tokens, prompt_merge_dir="prompt/p_2_0826.txt")`
Executes a two-step chat completion operation for lengthy content.

### `LLM_extract(md_dir, file_content, response_folder, model="claude-3-5-sonnet-20240620", temperature=0.1, prompt_dir="prompt/p_3_2_0806.txt", max_tokens=8192)`
Extracts information from file content using a language model.

## Notes
- Ensure the security of your API key; do not hardcode it in public repositories.
- Adjust `temperature` and `max_tokens` as needed to achieve the best results.

# 2.LLM Response Aggregation Pipeline
## Overview
`LLM_response_aggregate.py` is a Python script designed for aggregating responses from 4 language model responses.

## Usage
Place Markdown files of scientific literature in the `data/md/` directory, and place 4 model responses in the `data/response/` directory. The script will process these responses and aggregate them into a single response.

```bash 
python LLM_response_aggregation.py
```


