import aiohttp
import asyncio
from datetime import datetime


class LoadTest:
    def __init__(self, url, method, total_number_of_requests, headers=None, payload=None, concurrency_limit=1000):
        self.url = url
        self.method = method.upper()
        self.headers = headers
        self.payload = payload
        self.total_number_of_requests = total_number_of_requests
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def send_request(self, session: aiohttp.ClientSession):
        async with self.semaphore:
            return await LoadTest.create_request(
                url=self.url,
                request_method=self.method,
                payload=self.payload,
                headers=self.headers,
                session=session,
            )

    async def start_load_testing(self) -> dict:
        start_time = datetime.now()

        connector = aiohttp.TCPConnector(
            limit=self.concurrency_limit,
            limit_per_host=self.concurrency_limit,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.send_request(session=session) for _ in range(self.total_number_of_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=False)

        duration = datetime.now() - start_time

        success = sum(1 for err, _ in results if err is None)
        failure = self.total_number_of_requests - success

        status_counts: dict[int, int] = {}
        errors: list[str] = []
        for err, status in results:
            if status is not None:
                status_counts[status] = status_counts.get(status, 0) + 1
            if err is not None:
                errors.append(str(err))

        health = await self.health_check_of_api()

        return {
            "total_requests": self.total_number_of_requests,
            "success": success,
            "failure": failure,
            "duration_seconds": round(duration.total_seconds(), 3),
            "requests_per_second": round(self.total_number_of_requests / duration.total_seconds(), 2),
            "status_code_distribution": status_counts,
            "errors": list(set(errors)),  # deduplicated
            "health_check": health,
        }

    async def health_check_of_api(self) -> dict:
        start = datetime.now()
        connector = aiohttp.TCPConnector(limit=10)

        async with aiohttp.ClientSession(connector=connector) as session:
            error, status = await LoadTest.create_request(
                url=self.url,
                request_method=self.method,
                payload=self.payload,
                headers=self.headers,
                session=session,
            )

        duration = datetime.now() - start

        if error:
            return {"passed": False, "error": str(error), "duration_seconds": round(duration.total_seconds(), 3)}
        return {"passed": True, "status_code": status, "duration_seconds": round(duration.total_seconds(), 3)}

    @staticmethod
    async def create_request(
        url: str,
        request_method: str,
        payload=None,
        headers=None,
        params=None,
        session: aiohttp.ClientSession = None,
    ) -> tuple:
        request_headers = {"Authorization": f"Bearer {headers}"} if headers else None
        try:
            async with session.request(
                request_method,
                url,
                json=payload,
                headers=request_headers,
                params=params,
            ) as response:
                await response.read()
                return None, response.status
        except Exception as e:
            return e, None