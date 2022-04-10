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

def extract_code(patch_f, proj_name, bug, bug_diff_data):
    if len(bug_diff_data) != 1:
        return None
    print("PROJ: " + proj_name, "BUG: " + str(bug))
    bug_diff = bug_diff_data[0]
    old_start_line, num_old_lines = bug_diff["old_indices"].split(",")
    new_start_line, num_new_lines = bug_diff["new_indices"].split(",")
    old_start_line = int(old_start_line[1:])
    num_old_lines = int(num_old_lines)
    new_start_line = int(new_start_line[1:])
    num_new_lines = int(num_new_lines)
    print("old start:", old_start_line, "# old lines:", num_old_lines)
    print("new start:", new_start_line, "# new lines:", num_new_lines)

    start_code = False
    all_lines, lines_added, lines_removed, in_both = [],[],[],[]
    for line in patch_f:
        if line[:2] == "@@":
            start_code = True
            continue
        if start_code:
            all_lines.append(line)
            if line[0] == "+":
                lines_added.append(line)
            elif line[0] == "-":
                lines_removed.append(line)
            else: 
                in_both.append(line)

    lines_in_old = len(in_both) + len(lines_removed)
    lines_in_new = len(in_both) + len(lines_added)

    #assert that you are counting the lines correctly
    assert(lines_in_old == num_old_lines) 
    assert(lines_in_new == num_new_lines)



        

            

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
    bug_data["proj_name"] = proj_name
    return bug_data
        

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
            extract_code(patch_f, proj, bug, bug_diff_data)
            bug_data = aggregate(proj, bug, bug_meta_data, bug_diff_data)




