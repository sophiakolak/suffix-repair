import psycopg
import project_parser
import bug_parser
import json

#connect to the db "bugsinpy"
def create_connection():
    conn = psycopg.connect("dbname='bugsinpy' user='sophia' host='localhost' password='sophia'")
    return conn

#create cursor to execute queries 
def create_cursor(conn):
    cur = conn.cursor()
    return cur

#create base table for project data
def create_proj_table(cur, conn):
    cur.execute("DROP TABLE IF EXISTS projects CASCADE")
    sql = '''CREATE TABLE projects(
           project_id SERIAL PRIMARY KEY,
           name VARCHAR(100),
           url TEXT,
           path TEXT,
           test_path TEXT,
           num_bugs INTEGER
        )'''
    cur.execute(sql)
    conn.commit()

#create base table for bug data
def create_bug_table(cur, conn):
    cur.execute("DROP TABLE IF EXISTS bugs CASCADE")
    sql = '''CREATE TABLE bugs(
                bug_id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(project_id),
                project_name VARCHAR(100),
                orig_num INTEGER,
                buggy_commit_id TEXT,
                fixed_commit_id TEXT,
                test_file TEXT,
                file_changed TEXT
            )'''
    cur.execute(sql)
    conn.commit()

def create_diff_table(cur, conn):
    cur.execute("DROP TABLE IF EXISTS diff")
    sql = '''CREATE TABLE diff(
                bug_id INTEGER REFERENCES bugs(bug_id),
                project_id INTEGER REFERENCES projects(project_id),
                deleted BOOLEAN,
                added BOOLEAN,
                line_number INTEGER,
                line_content TEXT
            )'''
    cur.execute(sql)
    conn.commit()


#initialize db with empty project and bug tables
def init_db():
    conn = create_connection()
    cur = create_cursor(conn)
    create_proj_table(cur, conn)
    create_bug_table(cur, conn)
    create_diff_table(cur, conn)
    conn.close()

def insert_project(data):
    conn = create_connection()
    cur = create_cursor(conn)
    sql = '''INSERT INTO projects(name, url, path, test_path, num_bugs)
                VALUES(%s, %s, %s, %s, %s)'''
    cur.execute(sql, data)
    conn.commit()
    conn.close()

def insert_bug(data):
    conn = create_connection()
    cur = create_cursor(conn)
    sql = '''INSERT INTO bugs(project_id, project_name, orig_num, buggy_commit_id, 
    fixed_commit_id, test_file, file_changed)
    VALUES(%s, %s, %s, %s, %s, %s, %s)'''
    cur.execute(sql, data)
    conn.commit()
    conn.close()

def get_proj_id(proj):
    conn = create_connection()
    cur = create_cursor(conn)
    sql = '''SELECT project_id FROM projects WHERE name = %s'''
    cur.execute(sql, (proj,))
    proj_id = cur.fetchone()[0]
    conn.close()
    return proj_id

def get_bug_id(proj_id, bug_num):
    conn = create_connection()
    cur = create_cursor(conn)
    sql = '''SELECT bug_id FROM bugs WHERE project_id = %s AND orig_num = %s'''
    cur.execute(sql, (proj_id, bug_num))
    bug_id = cur.fetchone()[0]
    conn.close()
    return bug_id

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

def map_proj_path(project_data):
    proj_path = {}
    for dic in project_data:
        proj = dic["name"]
        path = dic["path"]
        proj_path[proj] = path
    return proj_path

def map_proj_test_path(project_data):
    proj_test_path = {}
    for dic in project_data:
        proj = dic["name"]
        test_path = dic["test_data_path"] 
        proj_test_path[proj] = test_path
    return proj_test_path

def map_proj_url(project_url):
    proj_url = {}
    for dic in project_url:
        proj = list(dic.keys())[0]
        url = dic[proj]
        proj_url[proj] = url
    return proj_url

def map_proj_num_bugs(proj_bugs):
    proj_num_bugs = {}
    for proj in proj_bugs.keys():
        proj_num_bugs[proj] = count_bugs(proj, proj_bugs)
    return proj_num_bugs

def count_bugs(proj, proj_bugs):
   return len(proj_bugs[proj])

def reform_data():
    project_data, project_tests, project_url = project_parser.get_project_data()
    proj_bugs = map_proj_bug(project_tests)
    proj_path = map_proj_path(project_data)
    proj_test_path = map_proj_test_path(project_data)
    proj_url = map_proj_url(project_url)
    proj_num_bugs = map_proj_num_bugs(proj_bugs)
    return proj_bugs, proj_path, proj_test_path, proj_url, proj_num_bugs

def insert_projects():
    proj_bugs, proj_path, proj_test_path, proj_url, proj_num_bugs = reform_data()
    projects = list(proj_bugs.keys())
    for proj in projects:
        num_bugs = proj_num_bugs[proj]
        url = proj_url[proj]
        path = proj_path[proj]
        test_path = proj_test_path[proj]
        data = (proj, url, path, test_path, num_bugs)
        insert_project(data)
    return projects, proj_bugs

def insert_diff(data):
    conn = create_connection()
    cur = create_cursor(conn)
    sql = '''INSERT INTO diff(bug_id, project_id, deleted, added, line_number, line_content)
                VALUES(%s, %s, %s, %s, %s, %s)'''
    cur.execute(sql, data)
    conn.commit()
    conn.close()

def insert_delete_diffs(project_id, bug_id, lines_deleted):
    for line_number, line_content in lines_deleted.items():
        data = (bug_id, project_id, True, False, line_number, line_content)
        insert_diff(data)

def insert_add_diffs(project_id, bug_id, lines_added):
    for line_number, line_content in lines_added.items():
        data = (bug_id, project_id, False, True, line_number, line_content)
        insert_diff(data)

def insert_diffs(project_id, bug_id, lines_deleted, lines_added):
    insert_delete_diffs(project_id, bug_id, lines_deleted)
    insert_add_diffs(project_id, bug_id, lines_added)
    
def get_bug_fields(proj, bug, bug_data):
    project_id = get_proj_id(proj)
    buggy_commit_id = bug_data["buggy_commit_id"]
    fixed_commit_id = bug_data["fixed_commit_id"]
    test_file = bug_data["test_file"]
    file_changed = bug_data["file_changed"]
    return project_id, proj, bug, buggy_commit_id, fixed_commit_id, test_file, file_changed

def get_diff_fields(proj, bug, bug_data):
    project_id = get_proj_id(proj)
    bug_id = get_bug_id(project_id, bug)
    lines_deleted = bug_data["lines_deleted"]
    lines_added = bug_data["lines_added"]
    return project_id, bug_id, lines_deleted, lines_added

def insert_bugs(projects, proj_bugs):
    proj_bug_data = bug_parser.get_bug_data()
    for proj in projects:
        bugs = proj_bugs[proj]
        for bug in bugs:
            if bug in proj_bug_data[proj]:
                bug_data = proj_bug_data[proj][bug]
                data = get_bug_fields(proj, bug, bug_data)
                insert_bug(data)
                project_id, bug_id, lines_deleted, lines_added = get_diff_fields(proj, bug, bug_data)
                insert_diffs(project_id, bug_id, lines_deleted, lines_added)
            else:
                continue
            

def main():
    init_db()
    projects, proj_bugs = insert_projects()
    insert_bugs(projects, proj_bugs)
    

    
if __name__ == "__main__":
    main()

