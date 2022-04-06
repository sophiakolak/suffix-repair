import os 

proj_path = 'BugsInPy/projects'

def get_all_project_data():
    projects = []
    all_proj = os.listdir(proj_path)
    for proj in all_proj:
        project_data = {}
        project_data["name"] = proj
        project_data["path"] = os.path.join(proj_path, proj)
        projects.append(project_data)
    return projects

def get_project_test_path(project_data):
    project_tests = []
    for proj in project_data:
        base_path = proj["path"]
        test_path = os.path.join(base_path, proj["name"]+"-pass.txt")
        proj["test_data_path"] = test_path
        project_tests.append(proj)
    return project_tests

def get_project_url(project_data):
    project_url = []
    for proj in project_data:
        url_data = {}
        proj_name = proj["name"]
        base_path = proj["path"]
        test_path = os.path.join(base_path, "project.info")
        info_f = open(test_path, 'r')
        url_line = info_f.readline()
        url = url_line.strip().split("=")[1][1:-1]
        url_data[proj_name] = url
        project_url.append(url_data)
    return project_url

def extract_data(test_file, proj_name):
    bug_data = []
    for line in test_file:
        test_data = {}
        if "test" in line:
            path,command = line.strip().split(" ", 1)
            full_path = path.split("/")
            bug_number = full_path[-1]
            try: 
                int(bug_number)
            except: 
                x = command.split(" ")[0]
                bug_number = x.split("/")[-1]
                command = " " + command
            test_data[bug_number] = command[1:-1]
            bug_data.append(test_data)
    return bug_data


def get_project_tests(project_data):
    project_tests = {}
    for proj in project_data:
        proj_name = proj["name"]
        test_path = proj["test_data_path"]
        with open(test_path, 'r') as test_file:
            test_data = extract_data(test_file, proj_name)
            project_tests[proj_name] = test_data
    return project_tests


def get_project_data():
    project_data = get_all_project_data()
    project_test_paths = get_project_test_path(project_data)
    project_tests = get_project_tests(project_test_paths)
    project_url = get_project_url(project_data)

    return project_data, project_tests, project_url

#get_project_data()