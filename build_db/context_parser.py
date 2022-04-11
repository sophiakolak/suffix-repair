#this time actually extract the context!
#start with the replace no gaps, it will be the easiest and there are the most 
#if you have time (which I doubt...do the add no gaps)

#read the file 
#checkout the version 
#get the context (before/after, 40 lines)
#generate patches 

#1. similarity
#compute the BLEU score 

#2. fun. correctness 
#you're going to have to use their scripts probably for now.

#how to get this done on time? 
#getting the context/generating patches is not hard.
#do a small subset, on that small subset, do the correctness 
# while the algorithm keeps generating patches. 

import os
import json

def get_files(path):
    files = []
    for file in os.listdir(path):
        if file.endswith(".json"):
            files.append(os.path.join(path, file))
    return files

def parse_file(files):
    f = open(files, 'r')
    data = json.load(f)
    f.close()
    return data

def checkout_version(commit, proj_path):
    os.chdir(proj_path)
    os.system("git checkout " + commit)
    os.chdir("../../../../")

def clone_project(proj, url):
    clone_folder = "BugsInPy/temp/projects"
    if not os.path.exists(clone_folder):
        os.makedirs(clone_folder)
    proj_path = clone_folder + "/" + proj
    if not os.path.exists(proj_path):
        command = "git clone " + url + " " + proj_path
        os.system(command)

def to_int_list(line_nums):
    return [int(line_num) for line_num in line_nums]

def get_bounds(lines_del):
    lines_del = to_int_list(lines_del.keys())
    start_line = min(lines_del)
    end_line = max(lines_del)
    return start_line, end_line

def get_context(file_changed_path, lines_del):
    context_len = 40
    assert(os.path.isfile(file_changed_path))
    f = open(file_changed_path, 'r')
    line_count = 0
    prefix, suffix, del_lines = "", "", ""
    start_line, end_line = get_bounds(lines_del)
    prefix_start = start_line - context_len
    prefix_end = start_line - 1
    suffix_start = end_line + 1
    suffix_end = end_line + context_len
    for line in f:
        if line_count >= prefix_start and line_count <= prefix_end:
            prefix += line
        elif line_count >= suffix_start and line_count <= suffix_end:
            suffix += line
        elif line_count >= start_line and line_count <= end_line:
            del_lines += line   
        line_count += 1
    f.close()
    return prefix, suffix

def get_prefix_only(file_changed_path, lines_del):
    context_len = 80
    assert(os.path.isfile(file_changed_path))
    f = open(file_changed_path, 'r')
    line_count = 0
    prefix, del_lines = "", ""
    start_line, end_line = get_bounds(lines_del)
    prefix_start = start_line - context_len
    prefix_end = start_line - 1
    for line in f:
        if line_count >= prefix_start and line_count <= prefix_end:
            prefix += line
        elif line_count >= start_line and line_count <= end_line:
            del_lines += line   
        line_count += 1
    f.close()
    return prefix, suffix

def write_data(data, prefix, suffix, long_prefix):
    context_data = {}
    context_data["prefix"] = prefix
    context_data["suffix"] = suffix
    context_data["long_prefix"] = long_prefix
    base_path = "data/add/no_gap_context" 
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    full_path = "/" + data["project"] + "_" + str(data["bug"]) + ".json" 
    f = open(base_path + full_path, 'w')
    json.dump(context_data, f)
    f.close()
        
path = "data/rep/no_gap"
files = get_files(path)
for file in files:
    data = parse_file(file)
    proj, bug, url, commit = data["project"], data["bug"], data["project_url"], data["buggy_commit_id"]
    clone_project(proj, url)
    proj_path = "BugsInPy/temp/projects/" + proj
    checkout_version(commit, proj_path)
    file_changed, lines_del = data["file_changed"], data["lines_deleted"]
    file_changed_path = proj_path + "/" + file_changed
    prefix, suffix = get_context(file_changed_path, lines_del)
    long_prefix = get_prefix_only(file_changed_path, lines_del)
    write_data(data, prefix, suffix, long_prefix)


