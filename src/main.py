from fastapi import FastAPI
from pydantic import BaseModel
from service.utils import LoadTest
import asyncio

class Url(BaseModel):
    url : str 
    method : str 
    headers : str | None  = None  
    payload :  str | None = None
    total_number_of_requests : int = 1

app = FastAPI()


@app.post("/test/")
async def load_test(data: Url):
    data = dict(data)
    url = data.get("url")
    method = data.get("method")
    payload = data.get("payload")
    headers = data.get("headers")
    total_number_of_requests = data.get("total_number_of_requests")

    load_test = LoadTest(
        url,
        method,
        total_number_of_requests=total_number_of_requests,
        payload=payload,
        headers=headers
    )

    await load_test.start_load_testing() 
    return {"status": "Load test completed"}