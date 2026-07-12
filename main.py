def make_diff(file1, file2):
    with open(file1) as f:
        data_original = f.read()
    
    with open(file2) as f:
        data_new = f.read()
    
    original_lines = data_original.split("\n")
    new_lines = data_new.split("\n")

    if len(original_lines) < len(new_lines):
        shared_length = len(original_lines)
        new_longer = True
    else:
        shared_length = len(new_lines)
        new_longer = False
    
    index = 0
    while index < shared_length:
        original = original_lines[index]
        new = new_lines[index]
        index += 1
    
    if new_longer:
        length = len(new_lines)
        difference = length - len(original_lines)
        while difference > 0:
            original_lines.append(True)
            difference -= 1
    else:
        length = len(original_lines)
        difference = length - len(new_lines)
        while difference > 0:
            new_lines.append(True)
            difference -= 1
    
    index = 0
    while index < length:
        new_lines[index]
        original_lines[index]
    
        index += 1

make_diff("no.txt", "yes.txt")