def make_diff(file1, file2):
    with open(file1) as f:
        data_original = f.read()
    
    with open(file2) as f:
        data_new = f.read()
    
    original_chars = []
    new_chars = []
    for char in data_original:
        original_chars.append(char)
    for char in data_new:
        new_chars.append(char)
    
    len_original = len(original_chars)
    len_new = len(new_chars)
    if len_original >= len_new:
        max_len = len_original
    else:
        max_len = len_new
    
    index = 0

    diff = []
    original_line = True
    original_file = True
    new_line = True
    new_file = True
    while index < max_len:
        if index < len(original_chars):
            original_char = original_chars[index]
        else:
            original_char = "<EOF>"
            original_file = False
        if index < len(new_chars):
            new_char = new_chars[index]
        else:
            new_char = "<EOF>"
            new_file = False
        
        if original_char:
            if original_char == "\n":
                original_line = False
        else:
            if original_char not in ("\n", " "):
                original_line = True

        if new_line:
            if new_char == "\n":
                new_line = False
        else:
            if new_char not in ("\n", " "):
                new_line = True
        
        pair = (original_char, new_char)
        missing_part = False
        for part in pair:
            if not missing_part:
                if part in ("<EOF>", "<ADD>"):
                    missing_part = True
                else:
                    missing_part = False
        if missing_part:
            diff.append(("EOF", pair))
        else:
            diff.append(pair)
        index += 1
    print(diff)
make_diff("yes.txt", "no.txt")