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

import sys
import click
from datetime import datetime
from pathlib import Path
import argparse
import hashlib
import json
import zstandard as zstd # because we don't want too too much disk space taken up

@click.group()
@click.version_option(version="1.0.0", prog_name="gat")
def cli():
    """gat - A waste of disk space"""
    pass

@cli.command()
def init():
    """Initialise the repository. Only needed to be ran when you first initialise the repository"""
    Path("./.gat/snapshots").mkdir(parents=True, exist_ok=True)
    Path("./.gat/commits").mkdir(parents=True, exist_ok=True)
    if Path("./.gat/branches.json").is_file():
        return
    with open("./.gat/branches.json", "w") as f:
        json.dump([{"Name": "Main", "Commits": [], "Parent": None}], f, indent=4)

@cli.command()
@click.argument("branch")
@click.argument("files", nargs=-1, required=True)
@click.option("--name", "-n", required=True, help="Commit name")
@click.option("--message", "-m", required=True, help="Commit message")
def commit(branch, files, name, message):
    """Make a new commit on branch <branch>, with the files <[files]>"""
    result = make_commit(branch, files, name, message)
    if result is not None:
        print(f"Made a new commit: Commit {result}")

def make_commit(branch: str, files: list, name: str, message: str):
    missing_files = []
    for file in files:
        if not Path(file).exists():
            missing_files.append(file)
    if missing_files:
        print(f"{len(missing_files)} missing paths detected: {missing_files}")
        return
    existance = True
    target_commit = None
    branch_commits = None
    branch_exists = False
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")

    if Path("./.gat/branches.json").is_file():
        with open("./.gat/branches.json", "r") as f:
            data = json.load(f)
        
        updated = data.copy()  # Start with ALL branches
        branch_exists = False
        
        for limb in data:
            if limb["Name"] == branch:
                branch_exists = True
                # Modify the existing branch
                for item in updated:
                    if item["Name"] == branch:
                        item["Commits"].append(hashlib.md5(time_bytes).hexdigest())
                        break
                break
        
        if not branch_exists:
            # Add new branch
            if data[0]["Commits"] == []:
                parent = "Main (No commits)"
            else:
                parent = data[0]["Commits"][len(data[0]["Commits"]) - 1]
            updated.append({
                "Name": branch,
                "Commits": [hashlib.md5(time_bytes).hexdigest()],
                "Parent": parent
            })
        
        with open("./.gat/branches.json", "w") as f:
            json.dump(updated, f, indent=4)

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
                    with open(f"./{file}") as f:
                        text = f.read()
                    diff = find_minimum_edit_distance(snapshot.splitlines(), text.splitlines())

        if diff is None:
            diff = "No diff available for this file"
        

        file_dict = {
        "Path": f"./{file}",
        "Snapshot": make_snapshot(file),
        "Diff": diff
        }
        listed_files.append(file_dict.copy())
    commit["Files"] = listed_files

    with open(f"./.gat/commits/{commit['Hash']}", "w") as f:
        json.dump(commit, f, indent=4)
    
    with open("./.gat/branches.json", "w") as f:
            json.dump(updated, f, indent=4)
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

@cli.command()
@click.argument("commit")
def change(commit):
    """Load the commit with the hash <commit>"""
    with open(f"./.gat/commits/{commit}") as f:
        data = json.load(f)
    for file in data["Files"]:
        snapshot = file["Snapshot"]
        destination = file["Path"]

        file_data = load_snapshot(snapshot)
        with open(destination, "w") as f:
            f.write(file_data)

@cli.command()
@click.argument("branch")
@click.argument("name")
def goto(branch, name):
    """Load commit <name> from branch <branch>"""
    goto_via_name(branch, name)
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
                
            
@cli.command()
@click.argument("branch")
def list_commits(branch):
    """Lists every commit on a branch, but only it's name and hash"""
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
    print(commit_list)
    return commit_list

@cli.command()
def list_branches():
    """List every branch's name"""
    with open("./.gat/branches.json") as f:
        data = json.load(f)
    branches = []
    for branch in data:
        branches.append(branch["Name"])
    print(branches)
    return branches

@cli.command()
@click.argument("name")
def log(name):
    """Show every commit in branch <name>, aswell as some metadata"""
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

@cli.command()
@click.argument("branch")
@click.argument("file", type=click.Path(exists=True))
def status(branch, file):
    """Compare file <file> with the latest commit on branch <branch>"""
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
                operations_performed.append(({
                    "Type": "SUBSTITUTE",
                    "Original Text": source_string[j - 1],
                    "New Text": target_string[i - 1],
                    "Line": i
                    }) )
                i -= 1
                j -= 1
            # Check if the current element is derived from the upper element
            elif dp[i][j] == dp[i - 1][j] + 1 :
                operations_performed.append({
            "Type": "INSERT",
            "Text": target_string[i - 1],
            "Line": i
            })
                i -= 1
            # Check if the current element is derived from the left element
            else :
                operations_performed.append({
            "Type": "DELETE", 
            "Text": source_string[j - 1],
            "Line": j})
                j -= 1

    # If we reach top-most row of the matrix
    while (j != 0) :
        operations_performed.append({
            "Type": "DELETE", 
            "Text": source_string[j - 1],
            "Line": j})
        j -= 1

    # If we reach left-most column of the matrix
    while (i != 0) :
        operations_performed.append({
            "Type": "INSERT",
            "Text": target_string[i - 1],
            "Line": i
            }) 
        i -= 1

    # Reverse the list of operations performed as we have operations in reverse
    # order because of backtracking
    operations_performed.reverse()
    return operations_performed

@cli.command()
@click.argument("branch")
def merge(name):
    """Merge branch <branch> into Main"""
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

    with open("./.gat/branches.json") as f:
        branch_data = json.load(f)
    branch_data[0]["Commits"].append(time_hash)
    index = 0
    final_index = None

def fast_forward_merge(source_hash):
    with open(f"./.gat/commits/{source_hash}") as f:
        readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unix_time = datetime.now().timestamp()
        time_bytes = str(int(unix_time)).encode("utf-8")
        time_hash = hashlib.md5(time_bytes).hexdigest()

        commit_data = json.load(f)
        source_hash = commit_data["Hash"]
        source_files = commit_data["Files"]
        make_commit("Main", source_files, f"Merge {source_hash}", "Autogenerated by gat merge")

def three_way_merge(main_hash, source_hash):
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unix_time = datetime.now().timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")
    time_hash = hashlib.md5(time_bytes).hexdigest()
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
    print(main_data)

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

    files = []
    
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
        
        main_set = set()
        source_set = set()
        for diff in main_ancestor_diff:
            main_set.add(diff["Line"])
        for diff in source_ancestor_diff:
            source_set.add(diff["Line"])
        
        unique_lines = main_set ^ source_set

        unique_diffs = []
        conflicting_diffs_unpaired = []

        for diff in main_ancestor_diff:
            if diff["Line"] in unique_lines:
                unique_diffs.append(diff)
            else:
                conflicting_diffs_unpaired.append(diff)

        for diff in source_ancestor_diff:
            if diff["Line"] in unique_lines:
                unique_diffs.append(diff)
            else:
                conflicting_diffs_unpaired.append(diff)

        conflicting_diffs = pair_diffs(conflicting_diffs_unpaired)
        if len(conflicting_diffs):
            print(f"{len(conflicting_diffs)} conflicts found")
            for diffs in conflicting_diffs:
                try:
                    line = diffs[0][0]["Line"]
                except KeyError:
                    line = diffs[0]["Line"]
                print(f"Merge conflict at line {line}: Keep A ({diffs[0]}) or B ({diffs[1]})")
                e = True
                while e:
                    answer = input("A or B? ").lower()
                    if answer == "a":
                        unique_diffs.append(diffs[0])
                        e = False
                    elif answer == "b":
                        unique_diffs.append(diffs[1])
                        e = False
                    else:
                        print(f"{answer} isn't A or B")

        new_file = apply_diffs(ancestor_snapshot, unique_diffs)
        new_text = "\n".join(new_file)
        with open(path, "w") as f:
            f.write(new_text)
        
        files.append(str(Path(path)))
        
    make_commit("Main", files, f"Merge {source_hash}", "Autogenerated by gat merge")

def pair_diffs(diffs):
    paired = []
    unpaired = []
    for diff in diffs:
        done = False
        for unpaired_diff in unpaired:
            if not done:
                if unpaired_diff["Line"] == diff["Line"]:
                    paired.append((diff, unpaired_diff))
                    done = True
        if not done:
            unpaired.append(diff)

    return (paired)

def apply_diffs(text, diffs):
    text = text.splitlines()
    deletions = []
    additions = []

    for diff in diffs:
        if diff["Type"] == "SUBSTITUTE":
            deletions.append({
                "Type": "DELETE",
                "Text": diff["Original Text"],
                "Line": diff["Line"]
            })
            additions.append({
                "Type": "INSERT",
                "Text": diff["New Text"],
                "Line": diff["Line"]
            })
        elif diff["Type"] == "INSERT":
            additions.append(diff)
        else: # DELETE
            deletions.append(diff)

    deletions.sort(key=lambda x: x["Line"], reverse=True)
    additions.sort(key=lambda x: x["Line"])

    for deletion in deletions:
        del text[deletion["Line"] - 1]
    for addition in additions:
        text.insert(addition["Line"] - 1, addition["Text"])
    
    return text

if __name__ == "__main__":
    cli()