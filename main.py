from datetime import datetime
from pathlib import Path
import hashlib
import json
import zstandard as zstd # because we don't want too too much disk space taken up

def init():
    Path("./.gat/snapshots").mkdir(parents=True, exist_ok=True)
    Path("./.gat/commits").mkdir(parents=True, exist_ok=True)
    Path("./.gat/branches").mkdir(parents=True, exist_ok=True)

def make_commit(files: list, name: str, message: str):
    readable_time = datetime.now()
    unix_time = readable_time.timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")

    commit = {
    "Name": name,
    "Message": message,
    "Time": readable_time,
    "Hash": hashlib.md5(time_bytes).hexdigest(),
    "Files": []
    }
    listed_files = []
    for file in files:
        file_dict = {
        "Path": f"./{file}",
        "Snapshot": make_snapshot(file),
        "Diff": "" # TODO <- Fix this thing
        }
        listed_files.append(file_dict.copy())
    commit["Files"] = listed_files

    with open(f"./.gat/commits/{commit["Hash"]}", "w") as f:
        json.dump(commit, final, indent=4)

def make_diff(file1: str, file2: str, name):
    readable_time = datetime.now()
    unix_time = readable_time.timestamp()
    time_bytes = str(int(unix_time)).encode("utf-8")
    full_diff = [{
        "Name": name,
        "Hash": hashlib.md5(time_bytes).hexdigest(),
        "Time": readable_time
    }]
    diff = {
        "Line": 1,
        "Type": None,
        "Text": ""
    }
    with open(file1) as f:
        data_original = f.read()
    
    with open(file2) as f:
        data_new = f.read()
    
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
    return full_diff

def make_snapshot(path): # Makes new snapshots or returns existing ones
    readable_time = datetime.now()
    unix_time = readable_time.timestamp()
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
make_commit(["main.py"], "Gay", "The first test of the new commiting system")