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


def make_commit(branch: str, files: list, name: str, message: str):
    existance = True
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
                    branch_commits = limb["Commits"]
                    target_commit = limb["Commits"][len(limb["Commits"]) - 1]
                    updated = limb.copy()
                    updated["Commits"].append(hashlib.md5(time_bytes).hexdigest())
                    updated = [updated]
                    branch_exists = True
                    break 
                else:
                    updated = data.copy()
                    updated.append({
                        "Name": branch,
                        "Commits": [hashlib.md5(time_bytes).hexdigest()]
                     })
        
        with open("./.gat/branches.json", "w") as f:
            json.dump(updated, f)
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
        if branch_commits:
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
            target_commit = branches["Commits"][len(branches["Commits"]) - 1]
    if target_commit is None:
        print(f"Branch '{branch}' not found")
        return
    with open(f"./.gat/commits/{target_commit}") as f:
        data = json.load(f)
    for files in data["Files"]:
        if files["Path"] == file:
            target_snapshot = files["Snapshot"]
    print(make_diff(load_snapshot(target_snapshot), file))

# Costs for the operations
INS_COST = 1
DEL_COST = 1
SUB_COST = 2

def find_minimum_edit_distance(source_string, target_string) :

    # Create a dp matrix of dimension (source_string + 1) x (destination_matrix + 1)
    dp = [[0] * (len(source_string) + 1) for i in range(len(target_string) + 1)]

    # Initialize the required values of the matrix
    for i in range(1, len(target_string) + 1) :
        dp[i][0] = dp[i - 1][0] + INS_COST
    for i in range(1, len(source_string) + 1) :
        dp[0][i] = dp[0][i - 1] + DEL_COST

    # Maintain the record of opertions done
    # Record is one tuple. Eg : (INSERT, 'a') or (SUBSTITUTE, 'e', 'r') or (DELETE, 'j')
    operations_performed = []

    # Build the matrix following the algorithm
    for i in range(1, len(target_string) + 1) :
        for j in range(1, len(source_string) + 1) :
            if source_string[j - 1] == target_string[i - 1] :
                dp[i][j] = dp[i - 1][j - 1]
            else :
                dp[i][j] =  min(dp[i - 1][j] + INS_COST, \
                                dp[i - 1][j - 1] + SUB_COST, \
                                dp[i][j - 1] + DEL_COST)

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
            if dp[i][j] == dp[i - 1][j - 1] + SUB_COST :
                operations_performed.append(('SUBSTITUTE', source_string[j - 1], target_string[i - 1]))
                i -= 1
                j -= 1
            # Check if the current element is derived from the upper element
            elif dp[i][j] == dp[i - 1][j] + INS_COST :
                operations_performed.append(('INSERT', target_string[i - 1]))
                i -= 1
            # Check if the current element is derived from the left element
            else :
                operations_performed.append(('DELETE', source_string[j - 1]))
                j -= 1

    # If we reach top-most row of the matrix
    while (j != 0) :
        operations_performed.append(('DELETE', source_string[j - 1]))
        j -= 1

    # If we reach left-most column of the matrix
    while (i != 0) :
        operations_performed.append(('INSERT', target_string[i - 1]))
        i -= 1

    # Reverse the list of operations performed as we have operations in reverse
    # order because of backtracking
    operations_performed.reverse()
    return [dp[len(target_string)][len(source_string)], operations_performed]


if __name__ == "__main__":

    # Get the source and target string
    print("Enter the source string :")
    source_string = input().strip()
    print("Enter the target string :")
    target_string = input().strip()

    # Find the minimum edit distance and the operation performed
    distance, operations_performed = find_minimum_edit_distance(source_string, target_string)

    # Count the number of individual operations
    insertions, deletions, substitutions = 0, 0, 0
    for i in operations_performed :
        if i[0] == 'INSERT' :
            insertions += 1
        elif i[0] == 'DELETE' :
            deletions += 1
        else :
            substitutions += 1

    # Print the results
    print("Minimum edit distance : {}".format(distance))
    print("Number of insertions : {}".format(insertions))
    print("Number of deletions : {}".format(deletions))
    print("Number of substitutions : {}".format(substitutions))
    print("Total number of operations : {}".format(insertions + deletions + substitutions))

    print("Actual Operations :")
    for i in range(len(operations_performed)) :

        if operations_performed[i][0] == 'INSERT' :
            print("{}) {} : {}".format(i + 1, operations_performed[i][0], operations_performed[i][1]))
        elif operations_performed[i][0] == 'DELETE' :
            print("{}) {} : {}".format(i + 1, operations_performed[i][0], operations_performed[i][1]))
        else :
            print("{}) {} : {} by {}".format(i + 1, operations_performed[i][0], operations_performed[i][1], operations_performed[i][2]))

init()
status("Main", "./no.txt")