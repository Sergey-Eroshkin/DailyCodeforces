import json
def dict_list_to_json(dict_list, filename):
    try:
        json_str = json.dumps(dict_list, ensure_ascii = False)
        with open(filename, 'w', encoding = 'utf-8') as file:
            file.write(json_str)
        return json_str
    except (TypeError, ValueError, IOError) as e:
        print(f'({e})')
        return None

def json_to_dict_list(filename):
    try:
        with open(filename, 'r', encoding = 'utf-8') as file:
            json_str = file.read()
            dict_list = json.loads(json_str)
            return dict_list
    except (TypeError, ValueError, IOError) as e:
        print(f'Не, Ярик, всё хуйня({e}), давай заново!')
        return None


def add_to_json(dict_list, filename):
    data = []
    try:
        with open(filename, 'r', encoding = 'utf-8') as file:
            json_str = file.read()
            if(json_str):
                data.append(json.loads(json_str))
            print("data: ", data, "list: ", dict_list)
            for i in dict_list:
                data.append(i)
        dict_list_to_json(data, filename)
        return None
    except (TypeError, ValueError, IOError) as e:
        print(f'({e})')
        return None