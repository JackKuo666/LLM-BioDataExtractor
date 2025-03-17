import os 
import argparse
import re
from csv_organize import * 
import json 
import pandas as pd
import math
import sys 
import logging
import copy


parser = argparse.ArgumentParser()
parser.add_argument('-Folder','-F', help='The path of folder of LLM outputs.',type=str
                   )
parser.add_argument('-Path','-P', help='The path of right answer file',type=str,default='../data/ground_truth/golden_ribozyme.csv'
                   )

parser.add_argument('-Seq','-S', help='version of log',type=str,default='|'
                   )
parser.add_argument('-Have_dir','-H', help='if have dir',type=int,default=0
                   )
parser.add_argument('-Version','-V', help='version of log',type=str,default='V7'
                   )
args = parser.parse_args()




def run_compare(Folder,Path,Seq,Have_dir,Version):
    
    if not os.path.exists(os.path.join(Folder.replace('extract_response','result_response'))):
        os.mkdir(os.path.join(Folder.replace('extract_response','result_response')))
    

    logging.basicConfig(level=logging.INFO,format='%(message)s',filemode='w',filename=os.path.join(Folder.replace('extract_response','result_response'),Version+'.log'))
    logger = logging.getLogger(__name__)
    
    
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
    
    def getfile_data(file):
        """
        Get the data from the answer.
        file: csv file of the output.
        
        """
        # df = csv_organize(file)
        # print(df)
    
        with open(file,encoding='utf-8') as f:
            # datas = f.readlines()[1:]
            datas = f.readlines()
        
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
        
        list_care=[]
        list_care_km=[]
        list_care_kcat=[]
        list_care_kobs=[]
        list_care_kcleav=[]
        # df = csv_organize(df)
        # print(df)
        df = csv_organize_ribozyme(df)
        
        for _,row in df.iterrows():
            try:
                if row['Kcat/Km']!='NA':
                    list_care.append(row['Kcat/Km'])
                else:
                    pass 
                
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(fname+':'+str(exc_tb.tb_lineno))
                #print(row['Km'],row['Kcat'],row['Kcat/Km'])
            try:
                if row['Kcat']!='NA':
                    list_care_kcat.append(row['Kcat'])
                else:
                    pass
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(fname+':'+str(exc_tb.tb_lineno))
                #print(row['Km'],row['Kcat'],row['Kcat/Km'])
            try:
                if row['Km']!='NA':
                    list_care_km.append(row['Km'])
                else:
                    pass
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(fname+':'+str(exc_tb.tb_lineno))
                #print(row['Km'],row['Kcat'],row['Kcat/Km'])
                # print(e)
            try:
                if row['Kobs']!='NA':
                    list_care_kobs.append(row['Kobs'])
                else:
                    pass
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(fname+':'+str(exc_tb.tb_lineno))
            
            try:
                if row['Kcleav']!='NA':
                    list_care_kcleav.append(row['Kcleav'])
                else:
                    pass
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(fname+':'+str(exc_tb.tb_lineno))
                  
        # list_care = df['Kcat/Km'].tolist()
        list_care = [str(i) for i in list_care]
        list_care_km = [str(i) for i in list_care_km]
        list_care_kcat = [str(i) for i in list_care_kcat]
        list_care_kobs = [str(i) for i in list_care_kobs]
        list_care_kcleav = [str(i) for i in list_care_kcleav]
        
        
        
        return {'km_kcat':list_care,'kcat':list_care_kcat,'km':list_care_km,'kobs':list_care_kobs,'kcleav':list_care_kcleav}
    
    
    def read_right_answer(answer_file,cont_dict=None,value='km'):
        """
        Get the right answer.
        answer_file: is the right answer file.
        """
        """
        Get the right answer.
        answer_file: is the right answer file.
        """
        if cont_dict==None:
            cont_dict = {}
        else:
            pass
        if answer_file.endswith('.csv'):
            data = pd.read_csv(answer_file,header=0,sep='\t',dtype=str,encoding='utf-8')
            
        elif answer_file.endswith('.xlsx'):
            data = pd.read_excel(answer_file,value,header=0)
        # print(data['km'])
        data = csv_organize_ribozyme(data)
        # print(data.head(5))
        for _,row in data.iterrows():
            if str(row['pubmed_id']) not in cont_dict:
                cont_dict[str(row['pubmed_id'])]={}
            else:
                pass 
            if 'km_kcat' not in cont_dict[str(row['pubmed_id'])]:
                cont_dict[str(row['pubmed_id'])]['km_kcat']=[]
            else:
                pass 
            if 'km' not in cont_dict[str(row['pubmed_id'])]:
                cont_dict[str(row['pubmed_id'])]['km']=[]
            else:
                pass 
            if 'kcat' not in cont_dict[str(row['pubmed_id'])]:
                cont_dict[str(row['pubmed_id'])]['kcat']=[]
            else:
                pass
            if 'kobs' not in cont_dict[str(row['pubmed_id'])]:
                cont_dict[str(row['pubmed_id'])]['kobs']=[]
            else:
                pass
            if 'kcleav' not in cont_dict[str(row['pubmed_id'])]:
                cont_dict[str(row['pubmed_id'])]['kcleav']=[]
            else:
                pass
            
            
            try:
                if row['km'].strip()=='NA' or math.isnan(float(row['km'])):
                    pass
                else:
                    cont_dict[str(row['pubmed_id'])]['km'].append(row['km'])
            except:
                cont_dict[str(row['pubmed_id'])]['km'].append(row['km'])
            try:
                if row['kcat'].strip()=='NA' or math.isnan(float(row['kcat'])):
                    pass
                else:
                    cont_dict[str(row['pubmed_id'])]['kcat'].append(row['kcat'])
            except:
                cont_dict[str(row['pubmed_id'])]['kcat'].append(row['kcat'])
            try:
                if row['Km_kcat'].strip()=='NA' or math.isnan(float(row['Km_kcat'])):
                    pass
                else:
                    cont_dict[str(row['pubmed_id'])]['km_kcat'].append(row['Km_kcat'])
            except:
                cont_dict[str(row['pubmed_id'])]['km_kcat'].append(row['Km_kcat'])
            try:
                if row['Kobs'].strip()=='NA' or math.isnan(float(row['Kobs'])):
                    pass
                else:
                    cont_dict[str(row['pubmed_id'])]['kobs'].append(row['Kobs'])
            except:
                cont_dict[str(row['pubmed_id'])]['kobs'].append(row['Kobs'])
            try:
                if row['Kcleav'].strip()=='NA' or math.isnan(float(row['Kcleav'])):
                    pass
                else:
                    cont_dict[str(row['pubmed_id'])]['kcleav'].append(row['Kcleav'])
            except:
                cont_dict[str(row['pubmed_id'])]['kcleav'].append(row['Kcleav'])
        
            # print(cont_dict)
        return cont_dict
    
    
    def get_num(right_answer,file,file_answer,total_brenda,total_right_number,total_big_model,value='km_kcat'):
        try:
            right_km =right_answer[file.split('_')[0]][value]
        except:
            right_km = right_answer[file[:-4].replace('response_','')][value]
        rights_km = []
        
        for i in right_km:
            # if not math.isnan(float(i)):
            #     rights_km.append(float(i))
            # else:
            #     rights_km.append(i)
            try:
                if not math.isnan(float(i)):
                    rights_km.append(float(i))
                else:
                    pass
            except:
                rights_km.append(i)
            
        logger.info(file+' '+value+ ' true_ans '+str(len(rights_km))+' %s',rights_km)
        logger.info(file+' '+value+ ' file_ans '+str(len(file_answer))+' %s',file_answer)
        
        right_num = 0
        total_brenda+=len(rights_km)
        total_nums=len(rights_km)
        total_num = 0
        # total_all = 0
        for fil_km in file_answer:
            try:
                try:
                    res = _to_float(fil_km)
                except:
                    res = fil_km
                # res = fil_km
                
                # if (res in right_km) or (res/1000 in right_km) or (res*1000 in right_km) or (res/10000 in right_km) or (res*10000 in right_km):
                if res in rights_km:
                    right_num+=1
                    # logger.info(str(res)+' '+str(right_num))
                    total_right_number+=1
                    rights_km.pop(rights_km.index(res))
                else:
                    pass 
                total_num+=1
            except Exception as e:
                total_num+=1
                logger.exception('Change float wrong!')
        logger.info(file+' '+value+' right_num '+ str(right_num))
        logger.info('*'*30)
        
        total_big_model+=total_num
        return  total_nums,total_num,right_num,total_brenda,total_right_number,total_big_model
    
    
    
    def compare(file_path,answer_file,have_dir=0):
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
        # print(right_answer)
        right_number = {}
        total_big_model = 0
        total_right_number = 0
        total_brenda = 0
    
        total_kcat_big_model=0
        total_km_big_model=0
        total_km_kcat_big_model=0
        total_kobs_big_model=0
        total_kcleav_big_model=0
    
        total_kcat_right_number = 0
        total_km_right_number = 0
        total_km_kcat_right_number = 0
        total_kobs_right_number = 0
        total_kcleav_right_number = 0
        
        total_kcat_brenda=0
        total_km_brenda=0
        total_km_kcat_brenda=0
        total_kobs_brenda=0
        total_kcleav_brenda=0
    
    
    
    
        work_file = 0
    
        out_list = []
        for file in file_list:
            try:
                if have_dir:
                    file_answer = getfile_data(file)
                    file = os.path.split(file)[-1]
                else:
                    file_answer = getfile_data(os.path.join(file_path,file))
                
                
                rights_km_kcat_num,total_km_kcat_num,right_km_kcat_num,total_brenda,total_right_number,total_big_model = get_num(right_answer,file,file_answer['km_kcat'],total_brenda,total_right_number,total_big_model,value='km_kcat')
                total_km_kcat_big_model+=total_km_kcat_num
                total_km_kcat_right_number+=right_km_kcat_num
                total_km_kcat_brenda+=rights_km_kcat_num
            
            
                rights_km_num,total_km_num,right_km_num,total_brenda,total_right_number,total_big_model = get_num(right_answer,file,file_answer['km'],total_brenda,total_right_number,total_big_model,value='km')
                total_km_big_model+=total_km_num
                total_km_right_number+=right_km_num
                total_km_brenda+=rights_km_num
                
    
                rights_kcat_num,total_kcat_num,right_kcat_num,total_brenda,total_right_number,total_big_model = get_num(right_answer,file,file_answer['kcat'],total_brenda,total_right_number,total_big_model,value='kcat')
                total_kcat_big_model+=total_kcat_num
                total_kcat_right_number+=right_kcat_num
                total_kcat_brenda+=rights_kcat_num
                
                rights_kobs_num,total_kobs_num,right_kobs_num,total_brenda,total_right_number,total_big_model = get_num(right_answer,file,file_answer['kobs'],total_brenda,total_right_number,total_big_model,value='kobs')
                total_kobs_big_model+=total_kobs_num
                total_kobs_right_number+=right_kobs_num
                total_kobs_brenda+=rights_kobs_num
                
                rights_kcleav_num,total_kcleav_num,right_kcleav_num,total_brenda,total_right_number,total_big_model = get_num(right_answer,file,file_answer['kcleav'],total_brenda,total_right_number,total_big_model,value='kcleav')
                total_kcleav_big_model+=total_kcleav_num
                total_kcleav_right_number+=right_kcleav_num
                total_kcleav_brenda+=rights_kcleav_num
                
                logging.info('\n\n')
                
                work_file+=1
                right_number[file]={'total_golden':rights_km_num+rights_kcat_num+rights_km_kcat_num+rights_kobs_num+rights_kcleav_num,'total_big_model':total_km_num+total_kcat_num+total_km_kcat_num+total_kobs_num+total_kcleav_num,'total_right_num':right_km_num+right_kcat_num+right_km_kcat_num+right_kobs_num+right_kcleav_num,
                                'km_total_golden': rights_km_num, 'km_total_big_model': total_km_num,'km_total_right_num':right_km_num,
                                'kcat_total_golden':rights_kcat_num , 'kcat_total_big_model': total_kcat_num,'kcat_total_right_num':right_kcat_num,
                                'kcat_km_total_golden': rights_km_kcat_num, 'kcat_km_total_big_model': total_km_kcat_num,'kcat_km_total_right_num':right_km_kcat_num,
                                'kobs_total_golden': rights_kobs_num, 'kobs_total_big_model': total_kobs_num,'kobs_total_right_num':right_kobs_num,
                                'kcleav_total_golden': rights_kcleav_num, 'kcleav_total_big_model': total_kcleav_num,'kcleav_total_right_num':right_kcleav_num,
                                }
                
                
                out_list.append(file[:-4].replace('response_',''))
                
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.exception(file+' : not work!   '+fname+':'+str(exc_tb.tb_lineno))
                # logger.errors(file+' : not work!')
                logger.info('*'*30+'\n')
                
                
                golden_total = []
                try: 
                    for value in ['km','kcat','km_kcat','kcleav','kobs']:
                        try:
                            right_golden =right_answer[file.split('_')[0]][value]
                        except:
                            right_golden = right_answer[file[:-4].split('_')[-1]][value]
                        golden_total.append[len(right_golden)]
                        
                    right_number[file]={'total_golden':sum(golden_total),'total_big_model': 0,'total_right_num': 0,
                                        'km_total_golden': golden_total[0], 'km_total_big_model': 0,'km_total_right_num':0,
                                        'kcat_total_golden': golden_total[1] , 'kcat_total_big_model': 0,'kcat_total_right_num':0,
                                        'kcat_km_total_golden': golden_total[2], 'kcat_km_total_big_model': 0,'kcat_km_total_right_num':0,
                                        'kobs_total_golden': golden_total[2], 'kobs_total_big_model': 0,'kobs_total_right_num':0,
                                        'kcleav_total_golden': golden_total[2], 'kcleav_total_big_model': 0,'kcleav_total_right_num':0,
                                        }
                except:
                    pass 
        # print(len(out_list),out_list)
        for pubmedid in right_answer.keys():
            if str(pubmedid) not in out_list:
                print(pubmedid)
                right_number[pubmedid]={'total_golden':len(right_answer[pubmedid]['km']) + len(right_answer[pubmedid]['kcat']) + len(right_answer[pubmedid]['km_kcat']) + len(right_answer[pubmedid]['kobs']) + len(right_answer[pubmedid]['kcleav']),'total_big_model': 0,'total_right_num': 0,
                                        'km_total_golden': len(right_answer[pubmedid]['km']), 'km_total_big_model': 0,'km_total_right_num':0,
                                        'kcat_total_golden': len(right_answer[pubmedid]['kcat']) , 'kcat_total_big_model': 0,'kcat_total_right_num':0,
                                        'kcat_km_total_golden': len(right_answer[pubmedid]['km_kcat']), 'kcat_km_total_big_model': 0,'kcat_km_total_right_num':0,
                                        'kobs_total_golden': len(right_answer[pubmedid]['kobs']), 'kobs_total_big_model': 0,'kobs_total_right_num':0,
                                        'kcleav_total_golden': len(right_answer[pubmedid]['kcleav']), 'kcleav_total_big_model': 0,'kcleav_total_right_num':0,
                                        }
                work_file+=1
                total_brenda+=len(right_answer[pubmedid]['km']) + len(right_answer[pubmedid]['kcat']) + len(right_answer[pubmedid]['km_kcat']) + len(right_answer[pubmedid]['kobs']) + len(right_answer[pubmedid]['kcleav'])
                total_km_brenda+=len(right_answer[pubmedid]['km'])
                total_kcat_brenda+=len(right_answer[pubmedid]['kcat'])
                total_km_kcat_brenda+=len(right_answer[pubmedid]['km_kcat'])
                total_kobs_brenda+=len(right_answer[pubmedid]['kobs'])
                total_kcleav_brenda+=len(right_answer[pubmedid]['kcleav'])
            else:
                pass
                        
        right_number['total'] = {'work_file(not cotain not work file)':work_file,'total_golden':total_brenda,'total_big_model':total_big_model,'total_right_num':total_right_number,
                                 'km_total_golden':total_km_brenda,'km_total_big_model':total_km_big_model,'km_total_right_num':total_km_right_number,
                                 'kcat_total_golden':total_kcat_brenda,'kcat_total_big_model':total_kcat_big_model,'kcat_total_right_num':total_kcat_right_number,
                                 'kcat_km_total_golden':total_km_kcat_brenda,'kcat_km_total_big_model':total_km_kcat_big_model,'kcat_km_total_right_num':total_km_kcat_right_number,
                                 'kobs_total_golden':total_kobs_brenda,'kobs_total_big_model':total_kobs_big_model,'kobs_total_right_num':total_kobs_right_number,
                                 'kcleav_total_golden':total_kcleav_brenda,'kcleav_total_big_model':total_kcleav_big_model,'kcleav_total_right_num':total_kcleav_right_number,
                                 'out':out_list
                                 }
        return right_number
   
    all_data = compare(Folder,Path,seq=Seq,have_dir=Have_dir)
    logger.info('\n\n')
    logger.info('*'*50+'Final score'+'*'*50)
    logger.info("""
    Criterion :\n
    1) (float(fil_km) in right_km) \n
    fil_km is the number that extract from the LLM. \n
    right_km is a list of the right answer. \n""")
    logger.info('total_brenda: the brenda database have the total number of the value\n')
    logger.info('total_big_model: the total number of value that extracted by LLM.\n')
    logger.info('total_right_num: the total number of value are right, more close to the total_brenda is better. Brenda dose not cover all the data.\n')
    logger.info('%s',all_data['total'])
    json_path = os.path.join(Folder.replace('extract_response','result_response'),Version+'.json')
    
    with open(json_path,'w') as f:
        json.dump(all_data,f)
    
    csv_path = os.path.join(Folder.replace('extract_response','result_response'),Version+'_result'+'.csv')
    with open(csv_path,'w') as f:
        f.write('pubmedid,total_golden,total_big_model,total_right_num,km_total_golden,km_total_big_model,km_total_right_num,kcat_total_golden,kcat_total_big_model,kcat_total_right_num,km_kcat_total_golden,km_kcat_total_big_model,km_kcat_total_right_num,kobs_total_golden,kobs_total_big_model,kobs_total_right_num,kcleav_total_golden,kcleav_total_big_model,kcleav_total_right_num\n')
        for key,value in all_data.items():
            if key != 'total':
                if '_' in key:
                    pubmedid = key.replace('response_','').replace('.csv','')
                    
                else:
                    pubmedid = key
                write_list = [pubmedid,
                              all_data[key]['total_golden'],all_data[key]['total_big_model'],all_data[key]['total_right_num'],
                              all_data[key]['km_total_golden'],all_data[key]['km_total_big_model'],all_data[key]['km_total_right_num'],
                              all_data[key]['kcat_total_golden'],all_data[key]['kcat_total_big_model'],all_data[key]['kcat_total_right_num'],
                              all_data[key]['kcat_km_total_golden'],all_data[key]['kcat_km_total_big_model'],all_data[key]['kcat_km_total_right_num'],
                              all_data[key]['kobs_total_golden'],all_data[key]['kobs_total_big_model'],all_data[key]['kobs_total_right_num'],
                              all_data[key]['kcleav_total_golden'],all_data[key]['kcleav_total_big_model'],all_data[key]['kcleav_total_right_num'],
                                    
                                 ]
                write_list = [str(i) for i in write_list]
                f.write(','.join(write_list)+'\n')
                
                
    
if __name__=='__main__':
    run_compare(args.Folder,args.Path,args.Seq,args.Have_dir,args.Version)