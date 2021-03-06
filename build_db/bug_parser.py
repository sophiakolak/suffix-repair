import os 
import project_parser
import json


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

def reform_block(in_both, changed_lines, total_lines):
    block = ""
    both_keys = list(in_both.keys())
    changed_keys = list(changed_lines.keys())
    all_keys = both_keys + changed_keys
    assert(len(all_keys) == total_lines)
    for i in sorted(all_keys):
        if i in both_keys:
            block += in_both[i][1:]
        if i in changed_keys:
            block += changed_lines[i][1:]
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

    return old_snippet, new_snippet, lines_removed, lines_added

   

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

def get_proj_url(proj_name, project_url):
    for dic in project_url:
        if proj_name in dic:
            return dic[proj_name]

def checkout_version(buggy_commit, proj_path):
    os.chdir(proj_path)
    os.system("git checkout " + buggy_commit + " > /dev/null 2>&1")
    os.chdir("../../../../")

def combine_new(file_lines, snippet_lines):
    file_str, snippet_str = "", ""
    for line in file_lines:
        file_str += line + '\n'
    for line in snippet_lines:
        snippet_str += line + '\n'
    return file_str, snippet_str

def compare(file, snippet, num_lines):
    snippet_lines = snippet.split("\n")
    file_lines = file.split("\n")
    #checking that you have the # of lines stated by diff file
    assert(len(file_lines) == num_lines)
    if len(snippet_lines) == len(file_lines)+1:
        snippet_lines = snippet_lines[1:]
    file_str, snippet_str = combine_new(file_lines, snippet_lines)
    for i in range(len(snippet_lines)):
        if snippet_lines[i] != file_lines[i]:
            return False
    return True, file_str, snippet_str

def check_match_old(change_f, old_snippet, start_line, end_line):
    num_lines = end_line - start_line + 1
    curr_line = 0
    lines = ""
    for line in change_f:
        if curr_line >= start_line and curr_line <= end_line-1:
            lines += line
        curr_line += 1
    return compare(lines, old_snippet, num_lines)

def check_match_new(change_f, new_snippet, start_line, end_line):
    num_lines = end_line - start_line + 1
    #print("start", start_line, "end", end_line)
    curr_line = 0
    lines = ""
    for line in change_f:
        if curr_line >= start_line and curr_line <= end_line-1:
            lines += line
        curr_line += 1
    return compare(lines, new_snippet, num_lines)

def get_code(snippet, bug_data, version):
    data = {}
    proj_name = bug_data["proj_name"]
    bug = bug_data["bug"]
    #print("PROJ: " + proj_name, "BUG: " + str(bug))

    proj_path = "BugsInPy/temp/projects/" + proj_name
    bug_meta_data = bug_data["bug_meta_data"]
    diff_data = bug_data["bug_diff_data"]
    if version == "old":
        commit_id = bug_meta_data["buggy_commit_id"]
        start_line = int(diff_data[0]["old_indices"].split(",")[0][1:])
        num_lines = diff_data[0]["old_indices"].split(",")[1]
        end_line = int(start_line) + int(num_lines) - 1
    elif version == "new":
        commit_id = bug_meta_data["fixed_commit_id"]
        start_line = int(diff_data[0]["new_indices"].split(",")[0][1:])
        num_lines = diff_data[0]["new_indices"].split(",")[1]
        end_line = int(start_line) + int(num_lines) - 1
    file_changed = diff_data[0]["file"][2:]  

    data["file_changed"] = file_changed
    data["start_line"] = start_line
    data["num_lines"] = num_lines

    checkout_version(commit_id, proj_path)
    path_to_change = proj_path + "/" + file_changed
    assert(os.path.isfile(path_to_change))

    change_f = open(path_to_change, "r")

    if version == "new":
        is_match, data["file_str"], data["snippet_str"] = check_match_new(change_f, snippet, start_line, end_line)
        change_f.close()
        assert(is_match)
        return data
    
    elif version == "old":
        is_match, data["file_str"], data["snippet_str"] = check_match_old(change_f, snippet, start_line, end_line)
        change_f.close()
        assert(is_match) #ensure that your parsing the change correctly 
        return data

def clean_diffs(lines_changed):
    bugs = {}
    for idx, line in lines_changed.items():
        bug = line[1:].replace("\n", "")
        bugs[idx] = bug
    return bugs

def find_del_line_numbers(diff_block, bug_start_line, lines_removed):
    diff_block = diff_block.split("\n")
    bugs = clean_diffs(lines_removed)
    adjusted_idx = {}
    start_line, lines_seen = bug_start_line, 0
    for idx, bug in bugs.items():
        offset = 0
        for line in diff_block:
            if offset < lines_seen:
                offset += 1
                continue
            if line == bug:
                adjusted_idx[start_line+offset] = line + "\n"
                lines_seen += 1
                break
            lines_seen += 1
            offset += 1
    return adjusted_idx


def find_add_line_numbers(diff_block, bug_start_line, lines_added):
    diff_block = diff_block.split("\n")
    patches = clean_diffs(lines_added)
    adjusted_idx = {}
    start_line, lines_seen = bug_start_line, 0
    for idx, patch in patches.items():
        offset = 0
        for line in diff_block:
            if offset < lines_seen:
                offset += 1
                continue
            if line == patch:
                adjusted_idx[start_line+offset] = line + "\n"
                lines_seen += 1
                break
            lines_seen += 1
            offset += 1
    return adjusted_idx
    

def check_line_match(adjusted_idx, bug_f):
    line_count = 0
    for line in bug_f:
        if line_count in adjusted_idx:
            if line != adjusted_idx[line_count]:
                return False
        line_count += 1
    return True

def clone_projects(proj_bugs, project_url):
    projects = list(proj_bugs.keys())
    for proj in projects:
        proj_url = get_proj_url(proj, project_url)
        clone_folder = "BugsInPy/temp/projects"
        if not os.path.exists(clone_folder):
            os.makedirs(clone_folder)
        proj_path = clone_folder + "/" + proj
        if not os.path.exists(proj_path):
            command = "git clone " + proj_url + " " + proj_path
            #print("Cloning " + proj + " to " + proj_path)
            os.system(command)

def write_data(proj, bug, bug_meta_data, file_changed, adjusted_del_idx, adjusted_add_idx):
    data = {}
    data["project"] = proj
    data["bug"] = bug
    data["project_url"] = get_proj_url(proj)
    data["file_changed"] = file_changed
    data["buggy_commit_id"] = bug_meta_data["buggy_commit_id"]
    data["fixed_commit_id"] = bug_meta_data["fixed_commit_id"]
    data["lines_deleted"] = adjusted_del_idx
    data["lines_added"] = adjusted_add_idx
    as_json = json.dumps(data)
    data_folder = "data/all_data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    data_path = data_folder + "/" + proj + ".json"
    with open(data_path, "a") as f:
        f.write(as_json)
        f.write("\n")
    
    

def get_bug_data():
    proj_path = 'BugsInPy/projects'
    project_data, project_tests, project_url = project_parser.get_project_data()
    proj_bugs = map_proj_bug(project_tests)
    clone_projects(proj_bugs, project_url)
    single_change_count, total = 0,0
    proj_bug_data = {}
    for proj, bugs in proj_bugs.items():
        proj_bug_data[proj] = {}
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
                    old_snippet, new_snippet, lines_removed, lines_added = reformed_blocks
                    if proj == "pandas" and bug == 93:
                        continue
                    if True:
                        old_data = get_code(old_snippet, bug_data, version="old")
                        del_start_line = int(old_data["start_line"])
                        del_diff_block = old_data["snippet_str"]
                        if len(lines_removed) > 0:
                            adjusted_del_idx = find_del_line_numbers(del_diff_block, del_start_line, lines_removed)
                            assert(len(adjusted_del_idx) == len(lines_removed))
                            path = "BugsInPy/temp/projects/" + proj
                            bug_f = open(path + "/" + old_data["file_changed"], "r")
                            correct_lines = check_line_match(adjusted_del_idx, bug_f)
                            bug_f.close()
                            assert(correct_lines)
                        else:
                            adjusted_del_idx = {}
                        new_data = get_code(new_snippet, bug_data, version="new")
                        add_start_line = int(new_data["start_line"])
                        add_diff_block = new_data["snippet_str"]
                        if len(lines_added) > 0:
                            adjusted_add_idx = find_add_line_numbers(add_diff_block, add_start_line, lines_added)
                            #print(adjusted_add_idx)
                            #if len(lines_removed) > 0:
                                #print(adjusted_del_idx)
                            assert(len(adjusted_add_idx) == len(lines_added))
                            path = "BugsInPy/temp/projects/" + proj
                            change_f = open(path + "/" + new_data["file_changed"], "r")
                            correct_lines = check_line_match(adjusted_add_idx, change_f)
                            change_f.close()
                            assert(correct_lines)
                        else: 
                            adjusted_add_idx = {}
                    
                    #write_data(proj, bug, bug_meta_data, new_data["file_changed"], adjusted_del_idx, adjusted_add_idx)

                    file_changed = new_data["file_changed"]
                    proj_bug_data[proj][bug] = {"buggy_commit_id": bug_meta_data["buggy_commit_id"],
                    "fixed_commit_id": bug_meta_data["fixed_commit_id"], "test_file": bug_meta_data["test_file"],
                    "file_changed": file_changed, "lines_deleted": adjusted_del_idx, "lines_added": adjusted_add_idx}
                   
    return proj_bug_data


def get_bug_data_for_project(proj):
    proj_bug_data = get_bug_data()
    return proj_bug_data[proj]
