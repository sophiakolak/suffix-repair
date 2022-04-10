import os 
import project_parser

proj_path = 'BugsInPy/projects'
project_data, project_tests, project_url = project_parser.get_project_data()

def map_proj_bug(project_tests):
    proj_bug = {}
    for proj_name in project_tests.keys():
        bugs = project_tests[proj_name]
        all_bugs = set()
        for bug in bugs:
            bug_num = int(list(bug.keys())[0])
            all_bugs.add(bug_num)
        proj_bug[proj_name] = sorted(all_bugs)
    return proj_bug

def parse_diff(patch_f, proj_name, bug):
    bug_diff_data = []
    #print("PROJ: " + proj_name, "BUG: " + str(bug))
    curr_file = ""
    for line in patch_f:
        bug_diff = {}
        if line[:2] == "@@":
            parts = line.strip().split(" ")
            old_indices = parts[1]
            new_indices = parts[2]
            if (len(parts) >= 5):
                code_type = parts[4]
            else:
                code_type = None
            #print(curr_file, old_indices, new_indices, code_type)
            bug_diff["file"] = curr_file
            bug_diff["old_indices"] = old_indices
            bug_diff["new_indices"] = new_indices
            bug_diff["code_type"] = code_type
            bug_diff_data.append(bug_diff)
        if line[:4] == "diff":
            line = line.strip().split(" ")
            old_file = line[2]
            new_file = line[3]
            assert(old_file.split("/")[-1] == new_file.split("/")[-1])
            curr_file = new_file
    patch_f.close()
    return bug_diff_data

#def reform_block(all_lines, in_both, changed_lines):
#    block = ""
#    for line in all_lines:
#        if line in in_both:
#            block += line[1:] #remove the added white space
#        if line in changed_lines:
#            block += line[1:] #remove the '-' or '+'
#    return block

def reform_block(in_both, changed_lines, total_lines):
    block = ""
    both_keys = list(in_both.keys())
    changed_keys = list(changed_lines.keys())
    all_keys = both_keys + changed_keys
    assert(len(all_keys) == total_lines)
    for i in sorted(all_keys):
        if i in both_keys:
            block += in_both[i]
        if i in changed_keys:
            block += changed_lines[i]
    return block


def extract_code(patch_f, proj_name, bug, bug_diff_data):
    if len(bug_diff_data) != 1:
        return None
    bug_diff = bug_diff_data[0]
    old_start_line, num_old_lines = bug_diff["old_indices"].split(",")
    new_start_line, num_new_lines = bug_diff["new_indices"].split(",")
    old_start_line = int(old_start_line[1:])
    num_old_lines = int(num_old_lines)
    new_start_line = int(new_start_line[1:])
    num_new_lines = int(num_new_lines)

    start_code = False
    all_lines, lines_added, lines_removed, in_both = {},{},{},{}
    idx = 0
    for line in patch_f:
        if line[:2] == "@@":
            start_code = True
            continue
        if start_code:
            all_lines[idx] = line
            if line[0] == "+":
                lines_added[idx] = line
            elif line[0] == "-":
                lines_removed[idx] = line
            else: 
                in_both[idx] = line
            idx += 1

    lines_in_old = len(in_both) + len(lines_removed)
    lines_in_new = len(in_both) + len(lines_added)

    #assert that you are counting the lines correctly
    assert(lines_in_old == num_old_lines) 
    assert(lines_in_new == num_new_lines)

    old_snippet = reform_block(in_both, lines_removed, lines_in_old)
    new_snippet = reform_block(in_both, lines_added, lines_in_new)

    reformed_old = old_snippet.split("\n")
    reformed_new = new_snippet.split("\n")

    #may be off by one due to whitespace
    assert(len(reformed_old) == lines_in_old or len(reformed_old) == lines_in_old+1) 
    assert(len(reformed_new) == lines_in_new or len(reformed_new) == lines_in_new+1)

    return old_snippet, new_snippet

   

def parse_info(info_f, proj_name, bug):
    bug_meta_data = {}
    for line in info_f:
        if "buggy_commit_id" in line:
            bug_meta_data["buggy_commit_id"] = line.strip().split("=")[1][1:-1]
        if "fixed_commit_id" in line:
            bug_meta_data["fixed_commit_id"] = line.strip().split("=")[1][1:-1]
        if "test_file" in line:
            bug_meta_data["test_file"] = line.strip().split("=")[1][1:-1]
    return bug_meta_data

def aggregate(proj_name, bug, bug_meta_data, bug_diff_data):
    bug_data = {}
    bug_data["bug"] = bug
    bug_data["bug_meta_data"] = bug_meta_data
    bug_data["bug_diff_data"] = bug_diff_data
    bug_data["proj_name"] = proj_name
    return bug_data

def get_proj_url(proj_name):
    for dic in project_url:
        if proj_name in dic:
            return dic[proj_name]

def verify_old(old_snippet, bug_data):
    proj_name = bug_data["proj_name"]
    bug = bug_data["bug"]
    proj_url = get_proj_url(proj_name)
    print("PROJ: " + proj_name, "BUG: " + str(bug), "URL: " + proj_url)
    print(bug_data)        

proj_bugs = map_proj_bug(project_tests)
single_change_count, total = 0,0
for proj, bugs in proj_bugs.items():
    for bug in bugs:
        patch_path = proj_path + "/" + proj + "/" +  "bugs/" + str(bug) 
        if (os.path.exists(patch_path)):
            patch_f = open(patch_path+"/bug_patch.txt", 'r')
            info_f = open(patch_path+"/bug.info", 'r')
            bug_meta_data = parse_info(info_f, proj, bug)
            bug_diff_data = parse_diff(patch_f, proj, bug) # this closes the file 
            patch_f = open(patch_path+"/bug_patch.txt", 'r') # reopen (change this later, it is unintuitive)
            reformed_blocks = extract_code(patch_f, proj, bug, bug_diff_data)
            bug_data = aggregate(proj, bug, bug_meta_data, bug_diff_data)
            if reformed_blocks is not None:
                old_snippet, new_snippet = reformed_blocks
                verify_old(old_snippet, bug_data)




