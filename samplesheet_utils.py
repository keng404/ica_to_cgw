import csv
import re
import os
from datetime import datetime as dt
##########
def logging_statement(string_to_print):
    date_time_obj = dt.now()
    timestamp_str = date_time_obj.strftime("%Y/%b/%d %H:%M:%S:%f")
    #############
    final_str = f"[ {timestamp_str} ] {string_to_print}"
    return print(f"{final_str}")

def read_csv(file):
    csv_data = []
    logging_statement(f"Reading in CSV {file}")
    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if len(row) > 0:
                csv_data.append(row)
    return csv_data

def write_csv(data,output):
    logging_statement(f"Writing out to CSV {output}")
    with open(output, 'w') as f:
        for line_arr in data:
            f.write(line_arr + "\n")
    return(output)

def get_run_name(samplesheet_data):
    run_name = None
    for row in samplesheet_data:
        if row[0] == "RunName":
            run_name = row[1]
    ### replace spaces with '_'
    run_name = re.sub("\\s+","_",run_name)
    return run_name

def parse_tso_v2_samplesheet(samplesheet_data):
    found_tso_header = False
    tso_header_row = 0
    row_count = 0
    tso_header = []
    header_dict = {}
    sample_dict = {}
    parsed_object = {}
    ##### read in V2 samplesheet
    for row in samplesheet_data:
        row_count = row_count + 1
        if re.search("TSO",row[0]) is not None and re.search("Data",row[0]) is not None:
            found_tso_header = True
            tso_header_row = row_count + 1
        if found_tso_header and row_count == tso_header_row:
            tso_header = row
            for idx,field in enumerate(row):
                header_dict[field] = idx
        elif found_tso_header and row_count > tso_header_row:
            sample_of_interest = row[header_dict['Sample_ID']]
            sample_dict[sample_of_interest] = row
    #### craft parsed object 
    parsed_object['sample_info'] = sample_dict
    parsed_object['header_dict'] = header_dict
    parsed_object['header'] = tso_header
    return parsed_object
#######################################            
GGW_MANIFEST_HEADER = 'ACCESSION NUMBER,SPECIMEN LABEL,RUN ID,LANE,BARCODE,SEQUENCING TYPE,SAMPLE TYPE,SAMPLE ID,PAIR ID'
GGW_MANIFEST_HEADER_ARR =   GGW_MANIFEST_HEADER.split(',')
def get_header_dict(header_array):
    header_dict = {}
    for idx,field in enumerate(header_array):
        header_dict[field] = idx
    return header_dict      
##########################################
## CGW manifest notes
# assume LANE is always '1'
# assume SPECIMEN LABEL is always 'Primary Specimen'
# RUN ID is folder name
# BARCODE is f"{Index}-{Index2}
# assume SEQUENCING TYPE is PAIRED END
# ACCESSION NUMBER is Accession_Number
# SAMPLE TYPE is Sample_Type
# SAMPLE ID is Sample_ID
# PAIR ID is PAIR ID 
###############################
def get_hard_coded_values(row,header_dict):
    row[header_dict['LANE']] = '1'
    row[header_dict['SPECIMEN LABEL']] = 'Primary Specimen'
    row[header_dict['SEQUENCING TYPE']] = 'PAIRED END'
    return row

def update_barcode(row,header_dict,parsed_row,parsed_dict):
    index1 = parsed_row[parsed_dict['Index']]
    index2 = parsed_row[parsed_dict['Index2']]
    if index1 != "" and index2 != "":
        row[header_dict['BARCODE']] = f"{index1}-{index2}"
    elif index1 == "":
        row[header_dict['BARCODE']] = f"{index2}"
        row[header_dict['SEQUENCING TYPE']] = 'SINGLE END'
    elif index2 == "":
        row[header_dict['BARCODE']] = f"{index1}"
        row[header_dict['SEQUENCING TYPE']] = 'SINGLE END'
    return row

def update_parsed(row,header_dict,parsed_row,parsed_dict):
    row_parsed_mapping = {}
    row_parsed_mapping["ACCESSION NUMBER"] = "Accession_Number"
    row_parsed_mapping["SAMPLE TYPE"] = "Sample_Type"
    row_parsed_mapping["SAMPLE ID"] = "Sample_ID"
    row_parsed_mapping["PAIR ID"] = "Pair_ID"
    for k,v in enumerate(row_parsed_mapping):
        lookup_key = row_parsed_mapping[v]
        if lookup_key in list(parsed_dict.keys()):
            row[header_dict[v]] = parsed_row[parsed_dict[lookup_key]]
        else:
            debug_string = ",".join(parsed_row)
            raise ValueError(f"Could not find value for {lookup_key} in {debug_string}")
    return row

def get_updated_row(CGW_header_dict,parsed_row,parsed_dict):
    ### set row to dummy values and update
    row_to_craft = GGW_MANIFEST_HEADER_ARR
    ### update row - fields with hard-coded values:
    row_to_craft1 = get_hard_coded_values(row_to_craft,CGW_header_dict)
    ### update row - BARCODE field
    row_to_craft2 = update_barcode(row_to_craft1,CGW_header_dict,parsed_row,parsed_dict)
    ### update row based on other mappings
    row_to_craft3 = update_parsed(row_to_craft2,CGW_header_dict,parsed_row,parsed_dict)
    return row_to_craft3

def generate_CGW_sample_manifest(folder_basename,parsed_object):
    CGW_header_dict = get_header_dict(GGW_MANIFEST_HEADER_ARR)
    parsed_dict = parsed_object['header_dict']
    print(f"parsed dict {parsed_dict}")
    sample_info = parsed_object['sample_info']
    ### for each sample row info we parsed from the v2 samplesheet
    ### create row for manifest
    samples = list(sample_info.keys())        
    manifest_rows = []
    # add header to manifest
    manifest_rows.append(",".join(GGW_MANIFEST_HEADER_ARR))
    #print(f"manifest_rows {manifest_rows}")

    for idx,sample in enumerate(samples):
        parsed_row = sample_info[sample]
        row_to_write = get_updated_row(CGW_header_dict,parsed_row,parsed_dict)
        #print(f"row_to_write {row_to_write}")
        manifest_rows.append(",".join(row_to_write))
        #print(f"manifest_rows {manifest_rows}")
    return manifest_rows

def CGW_sample_manifest_runner(folder_basename,v2_samplesheet,output_manifest=None):
    ######################
    if output_manifest is None:
        timestamp = dt.now()
        random_string = timestamp.strftime("%f")
        output_manifest = f"{folder_basename}.sample_manifest.csv"
    ##############################    
    logging_statement(f"STEP1: Reading in V2 samplesheet {v2_samplesheet}")
    v2_samplesheet_data = read_csv(v2_samplesheet)

    logging_statement(f"STEP2: Parse V2 data from {v2_samplesheet}")
    v2_samplesheet_parsed = parse_tso_v2_samplesheet(v2_samplesheet_data)

    logging_statement(f"STEP3: Create CGW manifest for {folder_basename}")
    lines_to_write = generate_CGW_sample_manifest(folder_basename,v2_samplesheet_parsed)

    logging_statement(f"STEP4: Write out to CGW maniest {output_manifest}")
    output_file = write_csv(lines_to_write,output_manifest)
    return output_file