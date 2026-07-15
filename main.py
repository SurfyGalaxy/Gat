# This project uses code from here:
# https://github.com/athlohangade/minimum-edit-distance/

# MIT License

# Copyright (c) 2021 Atharva Lohangade

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime
from pathlib import Path
import argparse
import hashlib
import json
import zstandard as zstd # because we don't want too too much disk space taken up

def init():
    Path("./.gat/snapshots").mkdir(parents=True, exist_ok=True)
    Path("./.gat/commits").mkdir(parents=True, exist_ok=True)
    if Path("./.gat/branches.json").is_file():
        return
    with open("./.gat/branches.json", "w") as f:
        json.dump([{"Name": "Main", "Commits": [], "Parent": None}], f, indent=4)

def make_commit(branch: str, files: list, name: str, message: str):
    existance = True
    target_commit = None
    branch_commits = None
    branch_exists = False
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")

    updated = []
    if Path("./.gat/branches.json").is_file():
        with open("./.gat/branches.json", "r") as f:
            data = json.load(f)
        for limb in data:
            if limb["Name"] == branch:
                updated = limb.copy()
                branch_commits = limb["Commits"]
                if branch_commits != []:
                    target_commit = limb["Commits"][len(limb["Commits"]) - 1] 
                updated["Commits"].append(hashlib.md5(time_bytes).hexdigest())
                updated = [updated]
                branch_exists = True
                break 
            else:
                with open("./.gat/branches.json") as f:
                    main_data = json.load(f)
                if main_data[0]["Commits"] == []:
                    parent = "Main (No commits)"
                else:
                    parent = main_data[0]["Commits"][len(main_data[0]["Commits"]) - 1]
                updated = data.copy()
                updated.append({
                    "Name": branch,
                    "Commits": [hashlib.md5(time_bytes).hexdigest()],
                    "Parent": parent
                    })
        
        with open("./.gat/branches.json", "w") as f:
            json.dump(updated, f, indent=4)
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
        if target_commit:
            with open(f"./.gat/commits/{target_commit}") as old_commit:
                data = json.load(old_commit)
                for old_file in data["Files"]:
                    path = Path(old_file["Path"])
                    if str(path) == str(file):
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
    full_diff = []
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
    
    original_list = data_original.split("\n")
    new_list = data_new.split("\n")
        
    full_diff_list = find_minimum_edit_distance(original_list, new_list)

    for change in full_diff_list:
        if change[0] == "INSERT":
            full_diff.append({"Line": change[2], "Type": "Add", "Text": change[1]})
        elif change[0] == "SUBSTITUTE":
            full_diff.append({"Line": change[2], "Type": "Modify", "Text": change[1]})
        else:
            full_diff.append({"Line": change[2], "Type": "Delete", "Text": change[1]})
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

    processed = decompressor.decompress(data).decode("utf-8")
    return processed

def change(commit):
    with open(f"./.gat/commits/{commit}") as f:
        data = json.load(f)
    for file in data["Files"]:
        snapshot = file["Snapshot"]
        destination = file["Path"]

        file_data = load_snapshot(snapshot)
        with open(destination, "w") as f:
            f.write(file_data)

def goto_via_name(branch, name):
    branch_found = False
    commit_list = []

    with open("./.gat/branches.json") as f:
        data = json.load(f)
    for file in data:
        if file["Name"] == branch:
            branch_found = True
            for commit in file["Commits"]:
                with open(f"./.gat/commits/{commit}") as f:
                    commit_data = json.load(f)
                if commit_data["Name"] == name:
                    commit_list.append(commit_data)
    if branch_found:
        if len(commit_list) == 0:
            print(f"Commit '{name}' not found")
        elif len(commit_list) > 1:
            print(
f"""Multiple commits named '{name}' found.
Commits found:
{commit_list}""")
        else:
            change(commit_list[0]["Hash"])
            print(f"Loaded commit '{name}' from '{branch}'")
    else:
        print(f"Branch '{branch}' not found")
                
            

def list_commits(branch):
    commit_list = []
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    for branches in data:
        if branches["Name"] == branch:
            commit_hash = branches["Commits"]
            for hashes in commit_hash:
                with open(f"./.gat/commits/{hashes}") as f:
                    commit_data = json.load(f)
                name = commit_data["Name"]
                commit_list.append(f"{name} ({hashes})")
    return commit_list

def list_branches():
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    branches = []
    for branch in data:
        branches.append(branch["Name"])
    return branches

def log(name):
    commits = []
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    for branches in data:
        if branches["Name"] == name:
            commits = branches["Commits"]
    if len(commits) == 0:
        print(f"Branch '{name}' not found")
    for commit in commits:
        with open(f"./.gat/commits/{commit}") as f:
            data = json.load(f)
            print(
f"""Commit {data["Hash"]}:
  Name: {data["Name"]}
  Created on: {data["Time"]}
  Message: {data["Message"]}
  Files: {', '.join([f['Path'] for f in data['Files']])}
  """)

def status(branch, file):
    target_commit = None
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    for branches in data:
        if branches["Name"] == branch:
            try:
                target_commit = branches["Commits"][len(branches["Commits"]) - 1]
            except IndexError:
                print(f"No commits found in branch '{branch}'")
                return
    if target_commit is None:
        print(f"Branch '{branch}' not found")
        return
    with open(f"./.gat/commits/{target_commit}") as f:
        data = json.load(f)
    for files in data["Files"]:
        if files["Path"] == file:
            target_snapshot = files["Snapshot"]
    print(make_diff(load_snapshot(target_snapshot), file))

def find_minimum_edit_distance(source_string, target_string) :

    # Create a dp matrix of dimension (source_string + 1) x (destination_matrix + 1)
    dp = [[0] * (len(source_string) + 1) for i in range(len(target_string) + 1)]

    # Initialize the required values of the matrix
    for i in range(1, len(target_string) + 1) :
        dp[i][0] = dp[i - 1][0] + 1
    for i in range(1, len(source_string) + 1) :
        dp[0][i] = dp[0][i - 1] + 1

    # Maintain the record of opertions done
    # Record is one tuple. Eg : (INSERT, 'a') or (SUBSTITUTE, 'e', 'r') or (DELETE, 'j')
    operations_performed = []

    # Build the matrix following the algorithm
    print("Building matrix")
    for i in range(1, len(target_string) + 1) :
        for j in range(1, len(source_string) + 1) :
            if source_string[j - 1] == target_string[i - 1] :
                dp[i][j] = dp[i - 1][j - 1]
            else :
                dp[i][j] =  min(dp[i - 1][j] + 1, \
                                dp[i - 1][j - 1] + 1, \
                                dp[i][j - 1] + 1)

    # Initialization for backtracking
    i = len(target_string)
    j = len(source_string)

    # Backtrack to record the operation performed
    while (i != 0 and j != 0) :
        # If the character of the source string is equal to the character of the destination string,
        # no operation is performed
        if target_string[i - 1] == source_string[j - 1] :
            i -= 1
            j -= 1
        else :
            # Check if the current element is derived from the upper-left diagonal element
            if dp[i][j] == dp[i - 1][j - 1] + 1 :
                operations_performed.append(('SUBSTITUTE', source_string[j - 1], target_string[i - 1], i))
                i -= 1
                j -= 1
            # Check if the current element is derived from the upper element
            elif dp[i][j] == dp[i - 1][j] + 1 :
                operations_performed.append(('INSERT', target_string[i - 1], i))
                i -= 1
            # Check if the current element is derived from the left element
            else :
                operations_performed.append(('DELETE', source_string[j - 1], j))
                j -= 1

    # If we reach top-most row of the matrix
    while (j != 0) :
        operations_performed.append(('DELETE', source_string[j - 1], j))
        j -= 1

    # If we reach left-most column of the matrix
    while (i != 0) :
        operations_performed.append(('INSERT', target_string[i - 1], i))
        i -= 1

    # Reverse the list of operations performed as we have operations in reverse
    # order because of backtracking
    operations_performed.reverse()
    return operations_performed

def merge(name):
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")
    time_hash = hashlib.md5(time_bytes).hexdigest()
    source_data = None
    if name == "Main":
        print("Can't merge Main to Main")
        return
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    main_data = data[0]
    if len(main_data["Commits"]):
        main_target_commit = main_data["Commits"][len(main_data["Commits"]) - 1]
    else:
        main_target_commit = None
    for branch in data:
        if branch["Name"] == name:
            source_data = branch
    if source_data is None:
        print(f"Branch '{name}' not found")
        return
    source_target_commit = source_data["Commits"][len(source_data["Commits"]) - 1]
    if main_target_commit is None:
        commit_message = fast_forward_merge(source_target_commit)
    else:
        commit_message = three_way_merge(main_target_commit, source_target_commit)
    
    with open(f"./.gat/commits/{hashlib.md5(time_bytes).hexdigest()}", "w") as f:
        json.dump(commit_message, f, indent=4)
    with open("./.gat/branches.json") as f:
        branch_data = json.load(f)
    branch_data[0]["Commits"].append(time_hash)
    index = 0
    final_index = None
    for branch in branch_data:
        if branch["Name"] == name:
            final_index = index
        index += 1
    branch_data[final_index]["Commits"].append(time_hash)
    with open("./.gat/branches.json", "w") as f:
        json.dump(branch_data, f, indent=4)

def fast_forward_merge(source_hash):
    with open(f"./.gat/commits/{source_hash}") as f:
        readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unix_time = datetime.now().timestamp()
        time_bytes = str(int(unix_time)).encode("utf-8")
        time_hash = hashlib.md5(time_bytes).hexdigest()

        commit_data = json.load(f)
        source_hash = commit_data["Hash"]
        source_files = commit_data["Files"]
        commit_message = {"Name": f"Merge {source_hash}", "Message": "Autogenerated by gat merge", "Time": readable_time, "Hash": time_hash, "Files": source_files}

def three_way_merge(main_hash, source_hash):
    with open(f"./.gat/commits/{main_hash}") as f:
        main_data = json.load(f)
    with open(f"./.gat/commits/{source_hash}") as f:
        source_data = json.load(f)
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    for branch in data:
        if source_hash in branch["Commits"]:
            ancestor_hash = branch["Parent"]
    
    with open(f"./.gat/commits/{ancestor_hash}") as f:
        ancestor_data = json.load(f)

    main_files = main_data["Files"]
    source_files = source_data["Files"]
    ancestor_files = ancestor_data["Files"]

    main_file_set = set()
    source_file_set = set()
    for file in main_files:
        main_file_set.add(file["Path"])
    for file in source_files:
        source_file_set.add(file["Path"])
    
    shared_set = main_file_set & source_file_set
    new_set = source_file_set - main_file_set
    deleted_set = main_file_set - source_file_set
    
    for path in shared_set:
        for file in  main_files: # generate a list of diffs (it's midnight i need comments to think)
            if file["Path"] == path:
                main_snapshot = load_snapshot(file["Snapshot"])
        for file in ancestor_files:
            if file["Path"] == path:
                ancestor_snapshot = load_snapshot(file["Snapshot"])
        for file in source_files:
            if file["Path"] == path:
                source_snapshot = load_snapshot(file["Snapshot"])
        
        main_ancestor_diff = find_minimum_edit_distance(ancestor_snapshot.splitlines(), main_snapshot.splitlines())
        source_ancestor_diff = find_minimum_edit_distance(ancestor_snapshot.splitlines(), source_snapshot.splitlines())
        
        main_diff_lines = set()
        source_diff_lines = set()

        for change in main_ancestor_diff:
            if change[0] == "SUBSTITUTE":
                main_diff_lines.add(change[3])
            else:
                main_diff_lines.add(change[2])
        for change in source_ancestor_diff:
            if change[0] == "SUBSTITUTE":
                source_diff_lines.add(change[3])
            else:
                source_diff_lines.add(change[2])
        
        conflicting_diff_lines = main_diff_lines & source_diff_lines
        if len(conflicting_diff_lines):
            print(f"Merge conflicts on lines {conflicting_diff_lines}")

init()
three_way_merge("cfe9f10443432a720f6134351301d62d", "ce2eead72a214b543c9e362af19fd630")