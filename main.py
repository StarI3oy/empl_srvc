import aioredis
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from json import loads, dump
from datetime import datetime
from fastapi.staticfiles import StaticFiles
import redis
import json
import redis.asyncio as redis

load_dotenv()
ENV_URL = os.getenv("ENV_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
# ENV_URL= "https://vk.lab-sp.com/"
# REDIS_URL = "127.0.0.1"
# REDIS_PORT = "53192"
print(REDIS_URL)
print(REDIS_PORT)

app = FastAPI()
origins = ["*"]  # TODO: подтягивать ORIGINS из ENV_URL
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
    client = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=0)
    await client.set(f"test", "foo", ex=86400)
    await client.aclose()
    return {"ping": "pong"}


@app.get("/get")
async def getK():
    client = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=0)
    user = await client.get(f"test")
    await client.aclose()
    return {"ping": user}


app.mount("/bdaywidget/", StaticFiles(directory="bdaywidget", html=True))
app.mount("/hdaywidget/", StaticFiles(directory="hdaywidget", html=True))


@app.get("/employee/birthdate")
async def get_employees_with_bdate():
    # * Используем переменную окружения, и обьявленный в ней URL нашего API
    r = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=0)
    url = f"{ENV_URL}/api/groups/public/v_alpha/employees"
    payload = {}
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    data = loads(response.text)
    arr = []
    date_today = datetime.now()
    today = date_today.day
    month_today = date_today.month
    for i in range(len(data["items"])):
        id = data["items"][i]["id"]
        user = await r.get(f"{id}_user")
        if user:
            data_emp = json.loads(user)
            if data_emp["birth_date"]:
                try:
                    employee_date = datetime.strptime(
                        data_emp["birth_date"], "%Y-%m-%d"
                    ).date()
                except:
                    employee_date = datetime.strptime(
                        data_emp["birth_date"], "%m-%d"
                    ).date()
                if (
                    8 > (employee_date - date_today)
                    or 0 >= (employee_date - date_today)
                ) and month_today == employee_date.month:
                    arr.append(data_emp)
        else:
            url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
            response = requests.request(
                "GET", url_emp_byid, headers=headers, data=payload, verify=False
            )
            data_emp = loads(response.text)
            if data_emp["birth_date"]:
                try:
                    employee_date = datetime.strptime(
                        data_emp["birth_date"], "%Y-%m-%d"
                    ).date()
                except:
                    employee_date = datetime.strptime(
                        data_emp["birth_date"], "%m-%d"
                    ).date()
                if (
                    8 > (employee_date - date_today)
                    or 0 >= (employee_date - date_today)
                ) and month_today == employee_date.month:
                    arr.append(data_emp)
            await r.set(f"{id}_user", json.dumps(data_emp), ex=86400)
    await r.aclose()
    return {"result": arr, "url": ENV_URL}


@app.get("/employee/get_url")
async def get_url():
    return {"result": ENV_URL}


# @app.get("/employee/birthdate_test")
# async def get_employees_with_bdate_test():
#     url = f"{ENV_URL}/api/groups/public/v_alpha/employees"
#     payload = {}
#     headers = {"Accept": "application/json"}
#     response = requests.request("GET", url, headers=headers, data=payload, verify=False)
#     data = loads(response.text)
#     arr = []
#     for i in range(len(data["items"])):
#         id = data["items"][i]["id"]
#         url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
#         response = requests.request(
#             "GET", url_emp_byid, headers=headers, data=payload, verify=False
#         )
#         today = datetime(2024, 11, 24, 15, 8, 24, 78915).day
#         month_today = datetime(2024, 11, 24, 15, 8, 24, 78915).month
#         data_emp = loads(response.text)
#         if data_emp["birth_date"]:
#             try:
#                 employee_date = datetime.strptime(
#                     data_emp["birth_date"], "%Y-%m-%d"
#                 ).date()
#             except:
#                 employee_date = datetime.strptime(
#                     data_emp["birth_date"], "%m-%d"
#                 ).date()
#             if (
#                 8 > abs(employee_date.day - today)
#             ) and month_today == employee_date.month:
#                 arr.append(data_emp)
#     return {"result": arr, "url": ENV_URL}


# @app.get("/employee/hiredate")
# async def get_employees_with_hiredate():
#     url = f"{ENV_URL}/api/groups/public/v_alpha/employees"
#     payload = {}
#     headers = {"Accept": "application/json"}
#     response = requests.request("GET", url, headers=headers, data=payload, verify=False)
#     data = loads(response.text)
#     arr = []
#     for i in range(len(data["items"])):
#         id = data["items"][i]["id"]
#         url_emp_byid = f"{ENV_URL}/profile/public/v_alpha/users/{id}/"
#         response = requests.request(
#             "GET", url_emp_byid, headers=headers, data=payload, verify=False
#         )
#         day = datetime.now().day
#         data_emp = loads(response.text)
#         if data_emp["start_of_work"]:
#             if 8 > abs(
#                 datetime.strptime(data_emp["start_of_work"], "%Y-%m-%d").date().day
#                 - day
#             ):
#                 arr.append(data_emp)
#     return {"result": arr, "url": ENV_URL}
