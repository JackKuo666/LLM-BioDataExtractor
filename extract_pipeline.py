import os
import logging
from s1_pdf_2_md.ocr_mathpix import get_done_papers, process_pdfs
from s2_LLM_data_extract.LLM_data_extraction import LLM_extract, del_references
from s3_evaluate_extracted_data.compare_value import compare

def pdf_2_md():
    data_folder_dir = "data/"
    pdf_folder_dir = os.path.join(data_folder_dir, "pdf")
    md_folder_dir = os.path.join(data_folder_dir, "md")

    done_paper = get_done_papers(md_folder_dir)
    print("done_paper:", done_paper)

    no_response_paper, pages_more_50, done_paper = process_pdfs(pdf_folder_dir, done_paper, md_folder_dir)
    print("done_paper:", done_paper)
    print("no_response_paper:", no_response_paper)
    print("pages_more_50:", pages_more_50)


def LLM_extract_data():
    md_folder = "data/md/"
    response_folder = "data/response/"
    prompt_extract_dir = "prompt/p_3_2_0806.txt"
    prompt_merge_dir = "prompt/p_2_0826.txt"
    done_paper = []
    no_response_paper = []

    for md_file in os.listdir(md_folder):
        if md_file.endswith("md") and (md_file not in done_paper + no_response_paper):
            logging.info(f"Deleting references from: {md_file}")
            content = del_references(md_file, md_folder)
            response = LLM_extract(md_file, content, response_folder, prompt_extract_dir, prompt_merge_dir)
            if response:
                done_paper.append(md_file)
            else:
                no_response_paper.append(md_file)
            logging.info(f"Done papers: {done_paper}")
            logging.info(f"No response papers: {no_response_paper}")


def evaluate_extracted_data():
    response_dir = 'data/response/prompt_p_3_2_0806_claude-3-5-sonnet-20240620_128k_stream_max_tokens_8192_temperature_0.1'
    ground_truth_dir = 'data/ground_truth/km_kcat_all.csv'
    all_data = compare(response_dir, ground_truth_dir, "|", order=-7, have_dir=0)

    print('\n\n')
    print('*' * 50, 'Final score', '*' * 50)
    print("""
    Criterion :\n
    1) (float(fil_km) in right_km) \n
    file_ans is the number that extract from the LLM. \n
    true_ans is a fist of the right answer. \n""")
    print('total_brenda: the brenda database have the total number of the value\n')
    print('total_big_model: the total number of value that extracted by LLM.\n')
    print(
        'total_right_num: the total number of value are right, more close to the total_brenda is better. Brenda dose not cover all the data.\n')
    print(all_data['total'])
    # json_path = os.path.join(args.Folder.replace('extract_response','result_response'),args.Version+'.json')
    # with open(json_path,'w') as f:
    #     json.dump(all_data['total'],f)
    print('*' * 50, 'Final score', '*' * 50)
    # getfile_data(r'D:\wenxian\BrendaExtraction-3\extract_response\14篇_md_三步走_p_3_0620_kimi-128k_继续说\20656778\response_3\response_3_all_20656778.csv',3)


if __name__ == '__main__':
    pdf_2_md()
    LLM_extract_data()
    evaluate_extracted_data()