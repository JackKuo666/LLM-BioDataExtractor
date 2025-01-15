import os
import argparse
import re
from .csv_organize import *
import json
import pandas as pd
import math

parser = argparse.ArgumentParser()
parser.add_argument('-Folder','-F', help='The path of folder of LLM outputs.',type=str,default='data/response/prompt_p_3_2_0806_claude-3-5-sonnet-20240620_128k_stream_max_tokens_8192_temperature_0.1'
                   )
parser.add_argument('-Path','-P', help='The path of right answer file',type=str,default='./data/ground_truth/km_kcat_all.csv'
                   )
parser.add_argument('-Seq','-S', help='version of log',type=str,default='|'
                   )
parser.add_argument('-Have_dir','-H', help='if have dir',type=int,default=0
                   )
parser.add_argument('-Version','-V', help='version of log',type=str,default='latest'
                   )
args = parser.parse_args()


def _to_float(sci_notation_str):
    for sep in "±(":
        if sep in sci_notation_str:
            sci_notation_str = sci_notation_str.split(sep)[0]
    sci_notation_str = sci_notation_str.replace(",", "")
    sci_notation_str = sci_notation_str.strip()
    try:
        res = float(sci_notation_str)
        return res
    except ValueError:
        # Regular expression to match the scientific notation pattern
        match = re.match(r'([+-]?\d+\.?\d*)\s*[x×X]*\s*10\^([+-]?\d+)', sci_notation_str)
        if match:
            # Extract the coefficient and the exponent
            coefficient_str, exponent_str = match.groups()
            coefficient = float(coefficient_str)
            exponent = int(exponent_str)

            # Calculate the float number
            float_number = coefficient * (10 ** exponent)
            return float_number
        elif sci_notation_str=='NA':
            return 'NA'
        else:
            raise ValueError(f"Invalid scientific notation format {sci_notation_str}")


def getfile_data(file,order,seq=','):
    """
    Get the data from the answer.
    file: csv file of the output.
    order: the number col of the target value. For now we only compare km/kcat.
    seq: seprator.
    """
    # df = csv_organize(file)
    # print(df)

    with open(file,encoding='utf-8') as f:
        # datas = f.readlines()[1:]
        datas = f.readlines()

    #list_care = []
    # for data in datas:
    #     cont = data.split(seq)
    #     try:
    #         list_care.append(cont[order])
    #     except:
    #         pass

    # df = csv_organize(''.join(datas))
    new_datas = []
    for data in datas:
        if data[0]!='|' and '|' in data:
            if data[-2]!='|':
                new_datas.append('|'+data[:-1]+'|'+data[-1])
            else:
                new_datas.append('|'+data)
        else:
            new_datas.append(data)
    df = extract_data_table(''.join(new_datas))
    # print(df['Kcat/Km'])
    list_care=[]
    df = csv_organize(df)
    for _,row in df.iterrows():
        try:
            if row['Kcat/Km']!='NA':
                list_care.append(row['Kcat/Km'])
            elif row['Km']=='NA' and row['Kcat']=='NA':
                pass
            else:
                list_care.append(row['Kcat/Km'])
        except Exception as e:
            print(row['Km'],row['Kcat'],row['Kcat/Km'])
            # print(e)
    # list_care = df['Kcat/Km'].tolist()
    list_care = [str(i) for i in list_care]
    return list_care


def read_right_answer(answer_file):
    """
    Get the right answer.
    answer_file: is the right answer file.
    """
    if answer_file.endswith('.csv'):
        with open(answer_file) as f:
            datas=f.readlines()[1:]
        cont_dict = {}
        for line in datas:
            cont = line[:-1].split('|')
            if cont[-1] not in cont_dict:
                cont_dict[cont[-1]] = {}
            else:
                pass
            if 'km_kcat' not in  cont_dict[cont[-1]]:
                cont_dict[cont[-1]]['km_kcat']=[]
            else:
                pass
            cont_dict[cont[-1]]['km_kcat'].append(cont[2])
        # print(cont_dict)
        return cont_dict
    elif answer_file.endswith('.xlsx'):
        data = pd.read_excel(answer_file,'gold',header=0)
        cont_dict = {}

        for _,row in data.iterrows():

            if str(int(row['pubmed_id'])) not in cont_dict:
                cont_dict[str(int(row['pubmed_id']))]={}
            else:
                pass
            if 'km_kcat' not in cont_dict[str(int(row['pubmed_id']))]:
                cont_dict[str(int(row['pubmed_id']))]['km_kcat']=[]
            else:
                pass
            try:
                if math.isnan(float(row['km'])) and math.isnan(float(row['kcat'])) and math.isnan(float(row['km_kcat'])):
                    pass
                else:
                    cont_dict[str(int(row['pubmed_id']))]['km_kcat'].append(row['km_kcat'])
            except Exception as e:
                print(e)
        print(cont_dict)
        return cont_dict


def compare(file_path,answer_file,seq=',',order=-6,have_dir=0):
    """
    compare the answer between LLM extractions and Brenda.
    Criterion :
    1) (float(fil_km) in right_km) or
    2) (float(fil_km)/1000 in right_km) or
    3) (float(fil_km)*1000 in right_km) or
    4) (float(fil_km)/10000 in right_km) or
    5  (float(fil_km)*10000 in right_km).
    fil_km is the number that extract from the LLM.
    right_km is a list of the right answer.

    For this Criterion: now we only care about
    (1) the value got from the LLM is in the right answer list no matter whether unit conversion.
    (2) right relation between substrate and the target value.
    (3) in the fix colum. Sometimes, the value we care extracted from the LLM in the -6 or -7 colum.  For this reason, try order=-6 and order=-7 separately.

    file_path: the path of the LLM extractions folder.
    answer_file: the path of right answer file.
    seq: seqrator.
    order: the number colum of the target value.  For now we only compare km/kcat.
    """
    if have_dir:
        file_list = []
        have_file=set()
        for root,dirs,files in os.walk(file_path):
            for file in files:
                # print(root,file)
                if file.startswith('response_all') and file.endswith('.csv'):
                    file_list.append(os.path.join(root,file))
                    have_file.add(file[:-4].split('_')[-1])
                elif file.startswith('response_'+str(have_dir)+'_all') and file.endswith('.csv') and file[:-4].split('_')[-1] not in have_file:
                    file_list.append(os.path.join(root,file))

    else:
        file_list = os.listdir(file_path)
    # print(file_list)
    right_answer = read_right_answer(answer_file)
    right_number = {}
    total_big_model = 0
    total_right_number = 0
    total_brenda = 0
    work_file = 0
    out_list = []
    for file in file_list:
        try:
            if have_dir:
                file_answer = getfile_data(file,order,seq=seq)
                file = os.path.split(file)[-1]
            else:
                file_answer = getfile_data(os.path.join(file_path,file),order,seq=seq)
            # file_answer = sorted(file_answer)
            # print(file.split('_')[0])
            try:
                right_km =right_answer[file.split('_')[0]]['km_kcat']
            except:
                right_km = right_answer[file[:-4].split('_')[-1]]['km_kcat']

            rights_km = []
            for i in right_km:
                if not math.isnan(float(i)):
                    rights_km.append(float(i))
                else:
                    rights_km.append('NA')


            print(file,'true_ans',len(rights_km),rights_km,)
            print(file,'file_ans',len(file_answer),file_answer,)
            right_num = 0
            total_brenda+=len(rights_km)
            total_num = 0
            # total_all = 0
            for fil_km in file_answer:
                try:
                    res = _to_float(fil_km)

                    # if (res in right_km) or (res/1000 in right_km) or (res*1000 in right_km) or (res/10000 in right_km) or (res*10000 in right_km):
                    if res in rights_km:
                        right_num+=1
                        total_right_number+=1
                    else:
                        pass
                    total_num+=1
                except Exception as e:
                    total_num+=1
                    print(e)
            print(file,'right_num',right_num)
            print('*'*30)
            out_list.append([file,str(len(rights_km)),str(len(file_answer)),str(right_num)])

            work_file+=1
            total_big_model+=total_num
            right_number[file]={'total_brenda':len(rights_km),'total_big_model':total_num,'total_right_num':right_num}
        except Exception as e:
            print(file ,'not work!')
            print('*'*30)
            print(e)
            work_file+=1
    right_number['total'] = {'work_file':work_file,'total_brenda':total_brenda,'total_big_model':total_big_model,'total_right_num':total_right_number}
    # with open('write_result_list.txt','w') as f:
    #     for d in out_list:
    #         f.write(','.join(d)+'\n')
    return right_number


if __name__=='__main__':
    all_data = compare(args.Folder,args.Path,seq=args.Seq,order=-7,have_dir=args.Have_dir)

    print('\n\n')
    print('*'*50,'Final score','*'*50)
    print("""
    Criterion :\n
    1) (float(fil_km) in right_km) \n
    file_ans is the number that extract from the LLM. \n
    true_ans is a fist of the right answer. \n""")
    print('total_brenda: the brenda database have the total number of the value\n')
    print('total_big_model: the total number of value that extracted by LLM.\n')
    print('total_right_num: the total number of value are right, more close to the total_brenda is better. Brenda dose not cover all the data.\n')
    print(all_data['total'])
    # json_path = os.path.join(args.Folder.replace('extract_response','result_response'),args.Version+'.json')
    # with open(json_path,'w') as f:
    #     json.dump(all_data['total'],f)
    print('*'*50,'Final score','*'*50)
    # getfile_data(r'D:\wenxian\BrendaExtraction-3\extract_response\14篇_md_三步走_p_3_0620_kimi-128k_继续说\20656778\response_3\response_3_all_20656778.csv',3)



