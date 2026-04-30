from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator
from service.utils import LoadTest

app = FastAPI(title="Load Test API")


class LoadTestRequest(BaseModel):
    url: HttpUrl
    method: str
    headers: str | None = None
    payload: dict | None = None          # proper dict, not a raw string
    total_number_of_requests: int = 1
    concurrency_limit: int = 1000        # exposed so callers can tune it

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"method must be one of {allowed}")
        return upper

    @field_validator("total_number_of_requests")
    @classmethod
    def validate_requests(cls, v: int) -> int:
        if v < 1:
            raise ValueError("total_number_of_requests must be >= 1")
        if v > 10_000:
            raise ValueError("total_number_of_requests must be <= 10000")
        return v


class LoadTestResponse(BaseModel):
    total_requests: int
    success: int
    failure: int
    duration_seconds: float
    requests_per_second: float
    status_code_distribution: dict[int, int]
    errors: list[str]
    health_check: dict


@app.post("/test/", response_model=LoadTestResponse)
async def run_load_test(data: LoadTestRequest):
    try:
        tester = LoadTest(
            url=str(data.url),
            method=data.method,
            total_number_of_requests=data.total_number_of_requests,
            concurrency_limit=data.concurrency_limit,
            payload=data.payload,
            headers=data.headers,
        )
        results = await tester.start_load_testing()
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))