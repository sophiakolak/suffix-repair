import nltk 
import json 
import os

path = "data/rep/no_gap"
data_path_ps = "data/rep/no_gap_bleu_score/ps"
data_path_p = "data/rep/no_gap_bleu_score/p"

def calc_bleu_score(candidate, solution):
    candidate_tokenized = nltk.word_tokenize(candidate)
    solution_tokenized = nltk.word_tokenize(solution)
    BLEUscore = nltk.translate.bleu_score.sentence_bleu([solution_tokenized], candidate_tokenized, weights = (0.5, 0.5))
    return BLEUscore

def get_files(path):
    files = []
    for file in os.listdir(path):
        files.append(file)
    return files

def trim_lines(cand_code, num_lines):
    lines = cand_code.split("\n")
    idx, keep = 0, ""
    for line in lines:
        if line.strip() == "":
            continue
        if idx < num_lines:
            keep += line + "\n"
        idx += 1
    return keep 

def read_candidates(num_lines_changed, path):
    f = open(path, "r")
    rank, rank_cand = 1, {}
    for line in f:
        data = json.loads(line.strip())
        rank_cand[rank] = trim_lines(data["candidate"], num_lines_changed)
        rank += 1
    return rank_cand

def reform_add_lines(lines_add):
    solution = ""
    for idx,code in lines_add.items():
        solution += code 
    return solution

def write_data(file, data_path, data):
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    full_path = data_path + "/" + file
    f = open(full_path, "a+")
    f.write(json.dumps(data)+"\n")
    f.close()

files = get_files(path)
count = 0
for file in files:
    f = open(os.path.join(path, file))
    data = json.load(f)
    project = data["project"]
    bug = data["bug"]
    lines_dl = data["lines_deleted"]
    lines_add = data["lines_added"]
    print(project, ":", bug) 
    assert(len(lines_dl) == len(lines_add))
    num_lines_changed = len(lines_dl)
    suffix_prefix_path = "patch-data/prefix-suffix/rep/no_gap/" + file
    prefix_only_path = "patch-data/prefix-only/rep/no_gap/" + file
    pre_suf_cands = read_candidates(num_lines_changed, suffix_prefix_path)
    pre_only_cands = read_candidates(num_lines_changed, prefix_only_path)
    solution = reform_add_lines(lines_add)

    print("PRE+SUF:") 
    for rank, code in pre_suf_cands.items():
        bs = calc_bleu_score(code, solution)
        data = {"rank": rank, "bleu_score": bs, "candidate": code}
        write_data(file, data_path_ps, data)
        print(rank, ":", bs, ":")
        print("cand :", code.replace("\n", " "))
        print("sol  :", solution.replace("\n", " "))

    print("PRE ONLY:")
    for rank, code in pre_only_cands.items():
        bs = calc_bleu_score(code, solution)
        data = {"rank": rank, "bleu_score": bs, "candidate": code}
        write_data(file, data_path_p, data)
        print(rank, ":", bs, ":")  
        print("cand :", code.replace("\n", " "))
        print("sol  :", solution.replace("\n", " "))

    count += 1