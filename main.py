from datetime import datetime
from pathlib import Path
import hashlib
import json
import zstandard as zstd # because we don't want too too much disk space taken up

def init():
    Path("./.gat/snapshots").mkdir(parents=True, exist_ok=True)
    Path("./.gat/commits").mkdir(parents=True, exist_ok=True)

def make_commit(branch: str, files: list, name: str, message: str):
    existance = True
    branch_commits = None
    branch_exists = False
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")

    if Path("./.gat/branches.json").is_file():
        with open("./.gat/branches.json", "r") as f:
            data = json.load(f)
            for limb in data:
                if limb["Name"] == branch:
                    branch_commits = limb["Commits"]
                    branch_exists = True
                    break 
    else:
        existance = False

   
    
                

    commit = {
    "Name": name,
    "Message": message,
    "Time": readable_time,
    "Hash": hashlib.md5(time_bytes).hexdigest(),
    "Files": []
    }
    listed_files = []
    diff = None
    for file in files:
        print(file)
        if branch_commits:
            target_commit = branch_commits[len(branch_commits) - 1]
            with open(f"./.gat/commits/{target_commit}") as old_commit:
                data = json.load(old_commit)
                for old_file in data["Files"]:
                    if old_file["Path"] == file:
                        snapshots = old_file["Snapshot"]
                        snapshot = load_snapshot(snapshots)
                        diff = make_diff(snapshot, file)

        if diff is None:
            diff = "No diff available for this file"
        

        file_dict = {
        "Path": f"./{file}",
        "Snapshot": make_snapshot(file),
        "Diff": diff
        }
        listed_files.append(file_dict.copy())
    commit["Files"] = listed_files

    with open(f"./.gat/commits/{commit["Hash"]}", "w") as f:
        json.dump(commit, f, indent=4)

    
    if not existance:
        with open("./.gat/branches.json", "w") as f:
            json.dump([{"Name": branch, "Commits": [commit["Hash"]]}], f)
    return commit["Hash"]

def make_diff(file1: str, file2: str):
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")
    empty = True
    full_diff = [{
        "Hash": hashlib.md5(time_bytes).hexdigest(),
        "Time": readable_time
    }]
    diff = {
        "Line": 1,
        "Type": None,
        "Text": ""
    }
    data_original = file1
    
    try:
        with open(file2) as f:
            data_new = f.read()
    except UnicodeDecodeError:
        diff = "Unable to generate diff for this file type"
    original_lines = data_original.split("\n")
    new_lines = data_new.split("\n")

    if len(original_lines) < len(new_lines):
        new_longer = True
    else:
        new_longer = False
    
    index = 0
    
    if new_longer:
        length = len(new_lines)
        difference = length - len(original_lines)
        while difference > 0:
            original_lines.append(None)
            difference -= 1
    else:
        length = len(original_lines)
        difference = length - len(new_lines)
        while difference > 0:
            new_lines.append(None)
            difference -= 1
    
    index = 0
    while index < length:
        original = original_lines[index]
        new = new_lines[index]
        both = (original, new)
        if original == new: # No need to waste space w/ the same line
            pass # (Stolen from Gut)
        else: # There's a change
            empty = False
            diff["Line"] = index + 1
            if None in both: # Add/Remove
                if original is None:
                    diff["Type"] = "Add"
                    diff["Text"] = new
                else:
                    diff["Type"] = "Remove"
                    diff["Text"] = original
            else: # Modify
                diff["Type"] = "Modify"
                diff["Text"] = new
        
            full_diff.append(diff.copy())
        index += 1
    
    if empty:
        return "No changesv in this file"
    return full_diff

def make_snapshot(path): # Makes new snapshots or returns existing ones
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    with open(f"./{path}", "rb") as f:
        data = f.read()
    
    compressor = zstd.ZstdCompressor(22)
    processed = compressor.compress(data)

    with open(f"./.gat/snapshots/{Path(path).stem}_{unix_time}.zst", "wb") as f:
        f.write(processed)
    return f"{Path(path).stem}_{unix_time}"

def load_snapshot(name):
    with open(f"./.gat/snapshots/{name}.zst", "rb") as f:
        data = f.read()

    decompressor = zstd.ZstdDecompressor()

    processed = decompressor.decompress(data)
    return processed

init()
make_commit("Main", ["main.py", "no.txt"], "uwu", "Yet another test")