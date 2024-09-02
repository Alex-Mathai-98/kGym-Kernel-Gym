# syz_dump.py
import os, json

def open_bug(bug_dir: str, bug_id: str):
    # bug file IO;
    bug_path = os.path.join(bug_dir, bug_id + '.json')
    if not os.path.exists(bug_path):
        raise FileNotFoundError(bug_path)
    with open(bug_path, 'r', encoding='utf-8') as fp:
        bug = json.load(fp)
    return bug
