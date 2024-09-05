import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from json import loads, dump
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
import redis
import json
import redis.asyncio as redis
from operator import itemgetter, attrgetter
import warnings
warnings.filterwarnings("ignore")
load_dotenv()
ENV_URL = os.getenv("ENV_URL", "https://vk.lab-sp.com")
REDIS_URL = os.getenv("REDIS_URL", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "59920")
print(REDIS_URL)
print(ENV_URL)
print(REDIS_PORT)

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def ping():
    return {"ping": "pong"}


@app.get("/set")
async def setK():
    client = redis.Redis(host=REDIS_URL, port=int(REDIS_PORT), db=0)
    await client.set(f"test", "foo", ex=86400)
    await client.aclose()
    return {"ping": "pong"}


@app.get("/get")
async def getK():
    client = redis.Redis(host=REDIS_URL, port=int(REDIS_PORT), db=0)
    user = await client.get(f"test")
    await client.aclose()
    return {"ping": user}


@app.get("/getUser")
async def getUser(id: str):
    client = redis.Redis(host=REDIS_URL, port=int(REDIS_PORT), db=0)
    payload = {}
    headers = {"Accept": "application/json"}
    url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
    response = requests.request(
        "GET", url_emp_byid, headers=headers, data=payload, verify=False
    )
    data_emp = loads(response.text)
    await client.aclose()
    return data_emp


@app.get("/clear")
async def clear():
    """Чистим редис"""
    result = "success"
    try:
        r = redis.Redis(host=REDIS_URL, port=int(REDIS_PORT), db=0)
        url = f"{ENV_URL}/api/groups/public/v_alpha/employees/?page_size=10000000"
        payload = {}
        headers = {"Accept": "application/json"}
        response = requests.request(
            "GET", url, headers=headers, data=payload, verify=False
        )
        data = loads(response.text)
        for i in range(len(data["items"])):
            id = data["items"][i]["id"]
            url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
            response = requests.request(
                "GET", url_emp_byid, headers=headers, data=payload, verify=False
            )
            data_emp = loads(response.text)
            await r.set(f"{id}_user", json.dumps(data_emp), ex=1)
    except Exception as e:
        result = str(e)
    return {"result": result}


app.mount("/bdaywidget/", StaticFiles(directory="bdaywidget", html=True))
app.mount("/hdaywidget/", StaticFiles(directory="hdaywidget", html=True))


def parse_date(date_str):
    try:
        employee_date = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        employee_date = datetime.strptime(date_str, "%m-%d")
    return employee_date


@app.get("/employee/birthdate")
async def get_employees_with_bdate():
    # * Используем переменную окружения, и обьявленный в ней URL нашего API
    r = redis.Redis(host=REDIS_URL, port=int(REDIS_PORT), db=0)
    page_num = 1
    end = -1
    arr = []
    date_today = datetime.now()
    month_today = date_today.month
    payload = {}
    headers = {"Accept": "application/json"}
    while page_num != end + 1:
        url = f"{ENV_URL}/api/groups/public/v_alpha/employees/?page_number={page_num}"
        page_num += 1
        response = requests.request(
            "GET", url, headers=headers, data=payload, verify=False
        )
        data = loads(response.text)
        if end == -1:
            end = int(data["meta"]["pages_count"])
        for i in range(len(data["items"])):
            id = data["items"][i]["id"]
            """ Проверяем что пользователь есть в редисе. Если нет - грузим в редис"""
            user = await r.get(f"{id}_user")
            if user:
                data_emp = json.loads(user)
            else:
                url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
                response = requests.request(
                    "GET", url_emp_byid, headers=headers, data=payload, verify=False
                )
                data_emp = loads(response.text)
                await r.set(f"{id}_user", json.dumps(data_emp), ex=86400)

            if data_emp["birth_date"]:
                try:
                    employee_date = datetime.strptime(
                        data_emp["birth_date"], "%Y-%m-%d"
                    )
                except:
                    employee_date = datetime.strptime(data_emp["birth_date"], "%m-%d")
                employee_birth_date_this_year = datetime(
                    date_today.year, employee_date.month, employee_date.day
                )
                time_delta = employee_birth_date_this_year - date_today 
                if (
                    8 > time_delta.days and 0 <= time_delta.days
                ) and month_today == employee_date.month:
                    arr.append(data_emp)

    await r.aclose()
    return {
        "result": sorted(
            arr, key=lambda x: parse_date(x["birth_date"]).day - date_today.day
        ),
        "url": ENV_URL,
    }


@app.get("/employee/get_url")
async def get_url():
    return {"result": ENV_URL}
