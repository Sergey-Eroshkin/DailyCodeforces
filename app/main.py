from fastapi import FastAPI
from utils import json_to_dict_list
from utils import dict_list_to_json
from utils import add_to_json
import os
from typing import Optional
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
path_to_json = os.path.join(parent_dir, 'codeforces.json')

app = FastAPI()

@app.get('/me')
def get_me():
    return json_to_dict_list(path_to_json)

@app.get('/')
def home():
    return 'Hello World'

def get_cf():
    url = "https://codeforces.com/api/user.rating?handle=SEroshkin"
    response = requests.get(url)
    return response.json()

changes = get_cf()["result"]
#print(changes)
#add_to_json(changes, path_to_json)

@app.get('/attempts/{handle}')
def get_attempts(handle: str | None = "SEroshkin"):
    url = "https://codeforces.com/api/user.status?handle=" + handle + "&count=50"
    response = requests.get(url)
    at = response.json()["result"]
    good = []
    for attempt in at:
        if attempt["verdict"] == "OK":
            good.append(attempt)
    add_to_json(good, path_to_json)
    return good

get_attempts("Tim07")
