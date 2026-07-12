def diff(file1, file2):
    with open(file1) as f:
        data_original = f.read()
        print(data_original)
    
    with open(file2) as f:
        data_new = f.read()
        print(data_new)
    
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
    while index < max_len:
        
        
        index += 1
    

diff("main.py", "no.txt")