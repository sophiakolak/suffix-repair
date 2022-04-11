from audioop import add
import os
import openai
import requests
import time
import difflib
import nltk
import json
from io import StringIO

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Engine.list()

path = "data/rep/no_gap_context"

def query_openai(prefix, suffix):
    response = openai.Completion.create(
        engine="code-davinci-002", 
        temperature=0.8,
        prompt=prefix,
        suffix=suffix,
        max_tokens=100,
        best_of=21,
        n=20,
        logprobs=1,
    )
    return response

def get_candidates(response):
    count = 0
    candidates = []
    entropies = []
    for result in response["choices"]:
        count += 1
        candidate = result["text"]
        candidates.append(result["text"])
        token_logprobs = result.logprobs.token_logprobs
        entropy = sum(token_logprobs)*(-1)
        entropies.append(entropy) 

    return candidates, entropies

def save_data(candidates, entropies, file):
    base_path = "patch-data/prefix-suffix/rep/no_gap"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    full_path = base_path + "/" + file
    f = open(full_path, "w+")
    for cand,ent in zip(candidates, entropies):
        f.write(json.dumps({"candidate": cand, "entropy": ent})+"\n")
    f.close()

def get_files(path):
    files = []
    for file in os.listdir(path):
        files.append(file)
    return files

def read_context(path, file):
    f = open(os.path.join(path, file))
    data = json.load(f)
    prefix = data["prefix"]
    suffix = data["suffix"]
    return prefix, suffix 

files = get_files(path)
for file in files:
    prefix, suffix = read_context(path, file)
    response = query_openai(prefix, suffix)
    candidates, entropies = get_candidates(response)
    save_data(candidates, entropies, file) 


