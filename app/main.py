from fastapi import FastAPI
from urllib3.util import url

from utils import json_to_dict_list
from utils import dict_list_to_json
from utils import add_to_json
import os
from typing import Optional
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
path_to_json = os.path.join(parent_dir, 'codeforces.json')

CONST = 100

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
    return good

#__________________________________


def get_counter(handle: str | None = "SEroshkin"):
    counter = {}
    good = get_attempts(handle)
    for g in good:
        task = g["problem"]
        if("rating" in task):
            cost = task["rating"]
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
    return counter

def get_chance(handle: str | None = "SEroshkin"):
    rate = get_cf(handle)
    counter = get_counter(handle)
    chance = {}
    for tag in counter:
        chance[tag] = counter[tag][0] / counter[tag][1] / rate
    return chance

#__________________________________

def get_contest(Id):
    url = "https://codeforces.com/api/contest.standings?contestId=" + str(Id)
    response = requests.get(url)
    ct = response.json()['result']["contest"]['name']
    return ct

def get_tasks():
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    t = response.json()['result']["problems"]
    return t


def get_recommendations(handle: str | None = "SEroshkin", limit: int = 3):
    """Возвращает список рекомендованных задач с расширенной информацией."""
    daily = []
    solved = get_attempts(handle)
    chance = get_chance(handle)
    rate = get_cf(handle)

    for task in get_tasks():
        flag = 0
        for sub in solved:
            if task == sub["problem"]:
                flag = 1
                break
        if flag == 1:
            continue
        tags = task["tags"]
        if ("rating" in task):
            cost = task["rating"]
        else:
            continue
        diff = []
        for tag in tags:
            if (tag in chance):
                new_cost = chance[tag] * cost
                diff.append(abs(new_cost - rate))
        if (len(diff) != 0 and sum(diff) / len(diff) <= CONST):
            daily.append([task, sum(diff) / len(diff)])

    daily = sorted(daily, key=lambda t: t[1], reverse=True)
    answer = []
    limit = max(1, limit)
    limit = min(limit, len(daily))
    for i in range(limit):
        contest_name = get_contest(daily[i][0]['contestId'])
        task = daily[i][0]
        answer.append({
            "name": task['name'],
            "contest": str(contest_name),
            "rating": task.get("rating", "-"),
            "tags": task.get("tags", []),
            "link": f"https://codeforces.com/problemset/problem/{task['contestId']}/{task['index']}"
        })
    return answer

@app.get('/tasks/{handle}')
def DAY(handle: str | None = "SEroshkin"):
    # Оставляем строковый формат для обратной совместимости API
    recs = get_recommendations(handle)
    return [f"{r['name']} - {r['contest']}" for r in recs]

if __name__ == "__main__":
    print(DAY("--S"))
