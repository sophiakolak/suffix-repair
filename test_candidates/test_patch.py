import os 
import json 
import shutil

class test_patch:
    def __init__(self, project, bug, commit):
        self.project = project
        self.bug = bug 
        self.commit = commit
        self.work_dir = "BugsInPy/temp/projects"

    def copy_data(self):
        command = "test_candidates/copy.sh -p " + self.project + " -i " + str(self.bug) + " -w " + self.work_dir
        os.system(command)

    def compile(self):
        command = "bugsinpy-compile -p " + self.project + " -w" + self.work_dir + "/" + self.project
        os.system(command)
    
    def run(self):
        command = "bugsinpy-test " + " -w " + self.work_dir + "/" + self.project
        info = os.popen(command).read()
        info_lines = info.splitlines()
        return info_lines 

    def compile_and_run_tests(self):
        self.copy_data()
        self.compile()
        info_lines = self.run()
        return info_lines
