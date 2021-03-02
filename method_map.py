method_map = []

code_list = []
def fill_method_map():
    for line in code_list:
        if line.startswith("method"):
            method_map.append(line.split(' ')[2])

    print(method_map)

def clear_method_map():
    method_map = []

code_list = []