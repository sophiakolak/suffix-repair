import os 
import json
import re
import shutil
from test_patch import test_patch

data_path = "data/rep/no_gap"

def get_data_files(data_path):
    files = []
    for file in os.listdir(data_path):
        files.append(os.path.join(data_path,file))
    return files 

def get_project_data(file):
    with open(file) as f:
        data = json.load(f)
    return data

def old_lines(line_dic):
    old_lines = []
    for key in line_dic:
        old_lines.append(key)
    num_lines = len(old_lines)
    return old_lines, num_lines

def clone_project(proj, url):
    clone_folder = "BugsInPy/temp/projects"
    if not os.path.exists(clone_folder):
        os.makedirs(clone_folder)
    proj_path = clone_folder + "/" + proj
    if not os.path.exists(proj_path):
        command = "git clone " + url + " " + proj_path
        os.system(command)
    return proj_path

def checkout_version(commit, proj_path):
    os.chdir(proj_path)
    os.system("git checkout " + commit)
    os.chdir("../../../../")

def overwrite_f(f_path, new_code):
    f = open(f_path, 'w')
    f.write(new_code)
    f.close()

def save_old(file_to_change):
    f = file_to_change.split("/")[:-1]
    f = "/".join(f)
    dir = "bug_files/" + f
    print(dir)
    if not os.path.exists(dir):
        os.makedirs(dir)
    f_path = dir + "/" + file_to_change.split("/")[-1]
    shutil.copyfile(file_to_change, f_path)

def save_patch(file_to_change):
    f = file_to_change.split("/")[:-1]
    f = "/".join(f)
    dir = "patch_files/" + f 
    print(dir)
    if not os.path.exists(dir):
        os.makedirs(dir)
    f_path = dir + "/" + file_to_change.split("/")[-1]
    if os.path.exists(f_path):
        f_path = dir + "/" + file_to_change.split("/")[-1] + "p_only"
    shutil.copyfile(file_to_change, f_path)


def reset_file(file_to_change):
    f_path = "bug_files/" + file_to_change
    shutil.copyfile(f_path, file_to_change)

def write_patch(f_path, l_patch, lines_to_change):
    #print(f_path)
    assert(os.path.isfile(f_path))
    f = open(f_path, 'r')
    line_count = 0
    new_code = ""
    for line in f:
        if str(line_count) in lines_to_change:
            new_code += l_patch[str(line_count)]
        else:
            new_code += line
        line_count += 1
    f.close()
    overwrite_f(f_path, new_code)
    return new_code

def read_patches(file_path, lines_to_change):
    f = open(file_path, 'r')
    rank_cand = {}
    for line in f: 
        data = json.loads(line)
        rank_cand[data["rank"]] = data["candidate"]
    f.close()
    return rank_cand

def split_with_delim(patch):
    s = patch
    x = patch.splitlines(keepends=True)
    return x
    
def line_and_patch(patch, lines_to_change):
    line_patch = {}
    lines = split_with_delim(patch)
    idx = 0
    while len(lines) < len(lines_to_change):
        lines.append("\n")
    assert(len(lines) == len(lines_to_change))
    for line in lines:
        line_patch[lines_to_change[idx]] = line 
        idx += 1
    return line_patch

def trim_test(new_code, lines_to_change):
    trimmed = new_code.split("\n")[int(lines_to_change[0])-5:int(lines_to_change[-1])+5]
    return trimmed
    
def test_patches(patches, file_to_change, lines_to_change, project, bug, commit):
    f_path = "BugsInPy/temp/projects/" + project + "/" + file_to_change
    for rank,patch in patches.items():
        if rank != 1:
            continue
        l_patch = line_and_patch(patch, lines_to_change)
        save_old(f_path)
        new_code = write_patch(f_path, l_patch, lines_to_change)
        save_patch(f_path)
        #print(f'lines to change:{lines_to_change}', f'patch:{l_patch}')
        trimmed = trim_test(new_code, lines_to_change)

        tp = test_patch(project, bug, commit)
        info_lines = tp.compile_and_run_tests()
        print(info_lines)

        reset_file(f_path)


files = get_data_files(data_path)
for file in files:
    data = get_project_data(file)
    lines_to_change, num_lines = old_lines(data["lines_deleted"]) 
    project = data["project"]
    bug = data["bug"]
    buggy_commit = data["buggy_commit_id"]
    file_to_change = data["file_changed"]
    if project != 'youtube-dl':
        continue
    if bug != 1: 
        continue
    proj_path = clone_project(project, data["project_url"])
    checkout_version(buggy_commit, proj_path)
    file_name = file.split("/")[-1]
    ps_path = "data/rep/no_gap_bleu_score/ps/" + file_name
    p_path = "data/rep/no_gap_bleu_score/p/" + file_name  
    ps_patches = read_patches(ps_path, lines_to_change)
    p_patches = read_patches(p_path, lines_to_change)
    pre_suf_results = test_patches(ps_patches, file_to_change, lines_to_change, project, bug, buggy_commit)
    pre_only_results = test_patches(p_patches, file_to_change, lines_to_change, project, bug, buggy_commit)