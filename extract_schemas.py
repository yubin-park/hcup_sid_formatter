from os import listdir
from os.path import isfile, join
import re
from collections import defaultdict
import csv

schema_full = []
meta_collection = defaultdict(dict)

path = "original_schema"
filenames = [f for f in listdir(path) if isfile(join(path, f))]

def adjust_metadata(metadata):
    # We noticed some metadata sections have errors
    # We need to shift the value a bit
    for metakey in metadata.keys():
        pos_lst = metadata[metakey]
        if pos_lst[0] > 30:
            pos_lst[0] += 1
        if pos_lst[1] > 28:
            pos_lst[1] += 1
        metadata[metakey] = pos_lst
    return metadata

for filename in sorted(filenames):
    fn_tokens = re.split(r'_|\.', filename)
    if len(fn_tokens) < 4:
        print(f"[warning] skipping {filename}...")
        continue
    else:
        print(f"[info] processing {filename}...")
    state = fn_tokens[0]
    year = fn_tokens[2]
    category = fn_tokens[3]

    #if filename in {"MA_SID_1998_CHGS.loc"}:
    #    continue
    
    with open(f"{path}/{filename}", "r") as fp:
        
        is_metadata = False
        is_schema = False
        metadata_mapping = {"variable name": "varname",
                "starting column of variable in ascii file": "start_idx",
                "ending column of variable in ascii file": "end_idx",
                "variable type (num=numeric; char=character)": "vartype",
                "variable label": "label"}
        metadata = {}
        for line in fp:
            
            if "=======   ============" in line:
                is_metadata = True
                continue
            elif is_metadata and line.strip() == "":
                is_metadata = False
                is_schema = True
                meta_collection[f"{state}{year}{category}"] = metadata 
                continue
            elif line.strip() == "":
                continue

            if is_metadata:
                positions = line[:7]
                pos_lst = [int(x.strip()) 
                        for x in positions.split("-")]
                description = line[10:].strip().lower()
                if (description in metadata_mapping and 
                        len(pos_lst) == 2):
                    metadata[metadata_mapping[description]] = pos_lst

            if is_schema:
                if len(metadata) < 5:
                    # For some years, the metadata section is not provided
                    # We use the previous metadata section
                    key = f"{state}{int(year)-1}{category}"
                    metadata = meta_collection[key]
                
                d = {metakey: line[(pos_lst[0]-1):(pos_lst[1])].strip()
                        for metakey, pos_lst in metadata.items()}
                
                if "E3" in d["end_idx"]:
                    # the column index is "MA_SID_1998_CHGS.loc" noted as
                    # 1E3 or 2E3. For these, we ignore the varnames..
                    continue

                try: 
                    d["start_idx"] = int(d["start_idx"])
                except ValueError:
                    meatadata = adjust_metadata(metadata)
                    d = {metakey: line[(pos_lst[0]-1):(pos_lst[1])].strip()
                        for metakey, pos_lst in metadata.items()}
                    d["start_idx"] = int(d["start_idx"])
                
                d["end_idx"] = int(d["end_idx"])
                row = [state, year, category, 
                        d["varname"], 
                        d["start_idx"],
                        d["end_idx"],
                        d["vartype"],
                        d["label"]]
                schema_full.append(row)

with open("schema/schema_info.csv", "w") as fp:
    writer = csv.writer(fp)
    writer.writerow(["state", "year", "category", 
                    "varname", "start_idx", "end_idx",
                    "vartype", "label"])
    writer.writerows(schema_full)
