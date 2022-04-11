import os 
import json

from matplotlib import lines 

data_path = "data/all_data"
total_bug_count = []
replacement_no_gap = []
replacement_gap = []
delete_no_gap = []
delete_gap = []
add_no_gap = []
add_gap = []
other = []

def get_data_files(data_path):
    proj_data_path = []
    for proj in os.listdir(data_path):
        proj_data_path.append(os.path.join(data_path, proj))
    return proj_data_path

def line_nums(lines_changed):
    return list(lines_changed.keys())

def to_int_list(line_nums):
    return [int(line_num) for line_num in line_nums]

def check_sequential(changed_line_nums):
    if len(changed_line_nums) == 0:
        return False
    changed_line_nums = to_int_list(changed_line_nums)
    assert(changed_line_nums == sorted(changed_line_nums))
    max_line = max(changed_line_nums)
    min_line = min(changed_line_nums)
    if max_line - min_line == len(changed_line_nums) - 1:
        return True

def compare_changes(del_line_nums, add_line_nums, proj_bug):
    del_is_seq = check_sequential(del_line_nums)
    add_is_seq = check_sequential(add_line_nums)
    if del_line_nums == add_line_nums:
        if del_is_seq and add_is_seq:
            replacement_no_gap.append(proj_bug)
            return "rep", "no_gap"
        else:
            replacement_gap.append(proj_bug)
            return "rep", "gap"
    elif len(del_line_nums) == 0:
        if add_is_seq:
            add_no_gap.append(proj_bug)
            return "add", "no_gap"
        else:
            add_gap.append(proj_bug)
            return "add", "gap"
    elif len(add_line_nums) == 0:
        if del_is_seq:
            delete_no_gap.append(proj_bug)
            return "del", "no_gap"
        else:
            delete_gap.append(proj_bug)
            return "del", "gap"
    else:
        #print("del:", del_line_nums, "add:", add_line_nums)
        other.append(proj_bug)
        return "other", "other"

def write_data(change_type, data):
    project = data["project"]
    bug = data["bug"]
    base_path = "data"
    dir_path = base_path + "/" + change_type[0] + "/" + change_type[1]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = dir_path + "/" + project + "_" + str(bug) + ".json"
    with open(file_path, 'w') as data_f:
        json.dump(data, data_f)
    
    

def read_data(proj_data_path):
    with open(proj_data_path, 'r') as data_f:
        for line in data_f:
            data = json.loads(line)
            proj = data["project"]
            bug = data["bug"]
            proj_bug = (proj, bug)
            if proj_bug not in total_bug_count:
                total_bug_count.append((proj, bug))
            lines_deleted = data["lines_deleted"]
            lines_added = data["lines_added"]
            del_line_nums = line_nums(lines_deleted)
            add_line_nums = line_nums(lines_added)
            change_type = compare_changes(del_line_nums, add_line_nums, proj_bug)
            write_data(change_type, data)
                
            
            

proj_data_paths = get_data_files(data_path)
simp_count_all, total_all = 0,0
for proj_data_path in proj_data_paths:
    read_data(proj_data_path)

print("total num bugs:", len(total_bug_count))
print("replacement no gap:", len(replacement_no_gap))
print("replacement gap:", len(replacement_gap))
print("delete no gap:", len(delete_no_gap))
print("delete gap:", len(delete_gap))
print("add no gap:", len(add_no_gap))
print("add gap:", len(add_gap))
print("other:", len(other))

print("perc no gap:", (len(replacement_no_gap) + len(delete_no_gap) + len(add_no_gap)) / len(total_bug_count))
print("perc gap:", (len(replacement_gap) + len(delete_gap) + len(add_gap)) / len(total_bug_count))

print("perc other:", len(other) / len(total_bug_count))




