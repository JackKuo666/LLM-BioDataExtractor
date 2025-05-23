import re
import time
import os
import tiktoken
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')

client = OpenAI(api_key=api_key, base_url=base_url)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """
    Returns the number of tokens used by a list of messages.

    Args:
    messages (list): A list of messages.
    model (str): The name of the model to use for tokenization.

    Returns:
    int: The number of tokens used by the messages.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def del_references(file_name, md_folder):
    """
    Removes references from a markdown file.

    Args:
    file_name (str): The name of the markdown file.
    md_folder (str): The path to the markdown file folder.

    Returns:
    str: The content of the file with references removed.
    """
    file_path = os.path.join(md_folder, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read()

    patterns = [
        (
        r'\*\{.{0,5}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*?)\\section\*\{Tables',
        "\section*{Tables\n"),
        (r'\*\{.{0,5}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*)',
         ""),
        (
        r'#.{0,15}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*?)(Table|Tables)',
        "Tables"),
        (
        r'#.{0,15}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*?)# SUPPLEMENTARY',
        "# SUPPLEMENTARY"),
        (
        r'#.{0,15}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*)\[\^0\]',
        "[^0]"),
        (r'#.{0,15}(References|Reference|REFERENCES|LITERATURE CITED|Referencesand notes|Notes and references)(.*)', "")
    ]

    for pattern, replacement in patterns:
        matches = re.search(pattern, lines, re.DOTALL)
        if matches:
            lines = lines.replace(matches[0], replacement)
            logging.info(f"Matched and replaced pattern: {pattern}")
            break
    else:
        logging.info("No References pattern matched.")

    output_dir = os.path.join(md_folder, "full_text_no_references")
    os.makedirs(output_dir, exist_ok=True)

    md_path = os.path.join(output_dir, f"{file_name.split('.')[0]}_full_text_no_references_mathpix_ocr.md")
    with open(md_path, "w", encoding="utf-8") as fout:
        fout.write(lines)
    logging.info(f"MD result written to: {md_path}")

    return lines

def chat_1_step(model, messages, temperature, max_tokens, new_dir, md_dir, response_folder):
    """
    Performs one step of chat completion.

    Args:
    model (str): The model to use for completion.
    messages (list): A list of messages.
    temperature (float): The temperature to use for completion.
    max_tokens (int): The maximum number of tokens to generate.
    new_dir (str): The directory for new responses.
    md_dir (str): The directory of the markdown file.
    response_folder (str): The folder for saving responses.

    Returns:
    str or None: The generated response content or None if an error occurs.
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        response_list = [chunk.choices[0].delta.content if chunk.choices[0].delta.content else "" for chunk in
                         completion]
        logging.info(f"Response tokens: {len(response_list)}")
        if len(response_list) > max_tokens:
            logging.warning("Output exceeds Max output tokens, please check.")

        response_content = ''.join(response_list)
        response_dir = os.path.join(response_folder, new_dir)
        os.makedirs(response_dir, exist_ok=True)

        response_content_dir = os.path.join(response_dir, f"response_{md_dir.split('.')[0]}.csv")
        with open(response_content_dir, "w", encoding="utf-8") as fout:
            fout.write(response_content)
        logging.info(f"Aggregate result written to: {response_content_dir}")

        return response_content
    except Exception as ex:
        logging.error(f"API request failed: {ex}")
        return None


def chat_2_step(md_dir, file_content, response_folder, model, temperature, new_dir, prompt_extract, gpt_4o_response, claude_response, llama_response, qwen_response, max_tokens, prompt_merge_dir="prompt/p_2_0826.txt"):
    """
    Performs a two-step chat completion for long content.

    Args:
    md_dir (str): The directory of the markdown file.
    file_content (str): The content of the file.
    response_folder (str): The folder for saving responses.
    model (str): The model to use for completion.
    temperature (float): The temperature to use for completion.
    new_dir (str): The directory for new responses.
    p_3_2_0617 (str): The prompt for the second step.
    max_tokens (int): The maximum number of tokens to generate.
    prompt_merge_dir (str): The directory of the merge prompt file.

    Returns:
    str or None: The generated response content or None if an error occurs.
    """
    all_response = ""
    for i in range(len(file_content) // 110000 + 1):
        text = file_content[i * 110000:(i + 1) * 110000]
        messages = [
            {
                "role": "system",
                "content": "You are an expert in information extraction from scientific literature.",
            },
            {"role": "user",
             "content": "The following is a [scientific article], please read it carefully: \n{" + text + "}.\n\n And the corresponding [LLM extraction prompt]: {" + prompt_extract + "}.\n\n" +
                        "Next are the responses of the four LLMs: \n[extracted table by gpt-4o]: \n{" + gpt_4o_response + "}.\n[extracted table by claude-3-5-sonnet-20240620]: \n{" + claude_response + "}.\n[extracted table by Meta-Llama-3.1-405B-Instruct]: \n{" + llama_response + "}.\n[extracted table by qwen-plus-0806]: \n{" + qwen_response + "}.\n\n" +
                        "Please check these [responses of the four LLMs] according to the provided [scientific article], [LLM extraction prompt] and organize them into a final table."},
        ]
        tokens = num_tokens_from_messages(messages)
        logging.info(f"Step one: Aggregate part {i}")
        logging.info(f"Prompt tokens: {tokens}")
        logging.info(f"Max output tokens: {max_tokens}")
        time.sleep(20)  # Required by some models
        response_content = chat_1_step(model, messages, temperature, max_tokens, new_dir, md_dir, response_folder)
        if response_content:
            all_response += response_content + "\n"
        else:
            return None

    with open(prompt_merge_dir, "r", encoding="utf-8") as fout:
        prompt_merge = fout.read()

    messages = [
        {"role": "system", "content": "You are an expert in information extraction from scientific literature."},
        {"role": "user", "content": f"Provided Text:\n'''\n{{\n{all_response}\n}}\n'''\n{prompt_merge}"}
    ]
    tokens = num_tokens_from_messages(messages)
    logging.info("Step two: Merging parts")
    logging.info(f"Prompt tokens: {tokens}")
    logging.info(f"Max output tokens: {max_tokens}")

    response = chat_1_step(model, messages, temperature, max_tokens, new_dir, md_dir, response_folder)
    return response


def LLM_aggregate(md_dir, file_content, response_folder, prompt_extract_dir="prompt/p_3_2_0806.txt", prompt_merge_dir="prompt/p_2_0826.txt", model="claude-3-5-sonnet-20240620", temperature=0.1,
                 max_tokens=8192):
    """
    Extracts information from file content using a language model.

    Args:
    md_dir (str): The directory of the markdown file.
    file_content (str): The content of the file.
    response_folder (str): The folder for saving responses.
    model (str): The model to use for extraction.
    temperature (float): The temperature to use for completion.
    prompt_dir (str): The directory of the prompt file.
    max_tokens (int): The maximum number of tokens to generate.

    Returns:
    str or None: The generated response content or None if an error occurs.
    """
    new_dir = "prompt_" + prompt_extract_dir.split("/")[-1].split(".")[0] + "_" + model + "_128k_stream_max_tokens_" + str(
        max_tokens) + "_temperature_" + str(temperature) + "_aggregate/"

    with open(prompt_extract_dir, "r", encoding="utf-8") as fout:
        prompt_extract = fout.read()

    with open(response_folder+"/claude-3-5-sonnet-20240620_example/response_"+md_dir.replace("md","csv"), "r", encoding="utf-8") as fout:
        claude_response = fout.read()

    with open(response_folder+"/gpt-4o_example/response_"+md_dir.replace("md","csv"), "r", encoding="utf-8") as fout:
        gpt_4o_response = fout.read()

    with open(response_folder+"/qwen-plus-0806_example/response_"+md_dir.replace("md","csv"), "r", encoding="utf-8") as fout:
        qwen_response = fout.read()

    with open(response_folder+"/Meta-Llama-3.1-405B-Instruct_example/response_"+md_dir.replace("md","csv"), "r", encoding="utf-8") as fout:
        llama_response = fout.read()

    # 把它放进请求中
    messages = [
        {
            "role": "system",
            "content": "You are an expert in information extraction from scientific literature.",
        },
        {"role": "user", "content": "The following is a [scientific article], please read it carefully: \n{"+file_content + "}.\n\n And the corresponding [LLM extraction prompt]: {" +prompt_extract+"}.\n\n"+
         "Next are the responses of the four LLMs: \n[extracted table by gpt-4o]: \n{"+gpt_4o_response+ "}.\n[extracted table by claude-3-5-sonnet-20240620]: \n{"+claude_response+ "}.\n[extracted table by Meta-Llama-3.1-405B-Instruct]: \n{"+llama_response+ "}.\n[extracted table by qwen-plus-0806]: \n{"+qwen_response+ "}.\n\n"+
        "Please check these [responses of the four LLMs] according to the provided [scientific article], [LLM extraction prompt] and organize them into a final table."},
    ]

    tokens = num_tokens_from_messages(messages)
    logging.info("Starting first round: Aggregate")
    logging.info(f"Prompt tokens: {tokens}")
    time.sleep(20)  # Required by some models,for example, claude-3-5-sonnet-20240620
    if tokens > 128000:
        try:
            response = chat_2_step(md_dir, file_content, response_folder, model, temperature, new_dir, prompt_extract, max_tokens, prompt_merge_dir)
            return response
        except Exception as ex:
            logging.error(f"Second round failed: {ex}")
            return None
    else:
        logging.info(f"Max output tokens: {max_tokens}")
        response = chat_1_step(model, messages, temperature, max_tokens, new_dir, md_dir, response_folder)
        return response


if __name__ == '__main__':
    md_folder = "../data/md/"
    response_folder = "../data/response/"
    prompt_extract_dir = "../prompt/p_3_2_0806.txt"
    prompt_merge_dir = "../prompt/p_2_0826.txt"
    done_paper = []
    no_response_paper = []

    for md_file in os.listdir(md_folder):
        if md_file.endswith("md") and (md_file not in done_paper + no_response_paper):
            logging.info(f"Deleting references from: {md_file}")
            content = del_references(md_file, md_folder)
            response = LLM_aggregate(md_file, content, response_folder, prompt_extract_dir, prompt_merge_dir)
            if response:
                done_paper.append(md_file)
            else:
                no_response_paper.append(md_file)
            logging.info(f"Done papers: {done_paper}")
            logging.info(f"No response papers: {no_response_paper}")


