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

@app.get('/rating/{handle}')
def get_cf(handle: str | None = "SEroshkin"):
    url = "https://codeforces.com/api/user.rating?handle=" + handle
    response = requests.get(url)
    return response.json()["result"][-1]['newRating']

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

#__________________________________



counter = {}

good = get_attempts("Tim07")
for g in good:
    task = g["problem"]
    if("points" in task):
        cost = task["points"]
    else:
        continue
    themes = task["tags"]
    for tag in themes:
        if(tag in counter):
            counter[tag][0] += cost
            counter[tag][1] += 1
        else:
            counter[tag] = [0, 0]
            counter[tag][0] += cost
            counter[tag][1] += 1

rate = get_cf("Tim07")
chance = {}



for tag in counter:
    chance[tag] = counter[tag][0] / counter[tag][1] / rate

print(chance)
