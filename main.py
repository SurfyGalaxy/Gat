import zstandard as zstd # because we don't want too too much disk space taken up

def make_diff(file1, file2):
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
    
    full_diff = []
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

def snapshot(path, compressing, output): # Makes new snapshots or returns existing ones
    with open(path, "rb") as f:
        data = f.read()
    
    compressor = zstd.ZstdCompressor(22)
    decompressor = zstd.ZstdDecompressor()

    if compressing:
        processed = compressor.compress(data)
    else:
        processed = decompressor.decompress(data)
        return processed

    with open(f"{output}.zst", "wb") as f:
        f.write(processed)
