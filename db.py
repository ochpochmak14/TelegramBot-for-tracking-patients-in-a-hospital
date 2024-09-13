import json

def write_data(data, file_name):
    data = json.dumps(data)
    data = json.loads(str(data))
    
    with open(file_name, "a", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        
        
def read_inf(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)