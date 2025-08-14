import aiohttp
import asyncio
from datetime import datetime

class LoadTest:
    def __init__(self, url, method, total_number_of_requests, headers=None, payload=None, concurrency_limit=100):
        self.url = url
        self.method = method.upper()
        self.headers = headers
        self.payload = payload
        self.total_number_of_requests = total_number_of_requests
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def send_request(self, session=None):
        """
        Send an HTTP request asynchronously using aiohttp.
        Uses a semaphore to limit concurrency.
        """
        async with self.semaphore:
            return await LoadTest.create_request(
                url=self.url,
                request_method=self.method,
                payload=self.payload,
                headers=self.headers,
                session=session
            )

    async def start_load_testing(self):
        print(f"🔁 Starting load test with {self.total_number_of_requests} async requests...")
        start_time = datetime.now()

        connector = aiohttp.TCPConnector(limit=1000, limit_per_host=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.send_request(session=session) for _ in range(self.total_number_of_requests)]
            results = await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n⏱️ Total Time: {duration}")

        success = sum(1 for err, status in results if err is None)
        failure = self.total_number_of_requests - success

        print(f"✅ Success: {success}")
        print(f"❌ Failure: {failure}")

        await self.health_check_of_api()

    async def health_check_of_api(self):
        """
        Performs a single request to verify if the API is still healthy.
        """
        print("\n🩺 Performing API Health Check...")
        start = datetime.now()

        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            error, status = await self.send_request(session=session)

        end = datetime.now()
        duration = end - start

        if error:
            print(f"❌ Health Check Failed: {error}")
        else:
            print(f"✅ Health Check Passed - Status: {status} | Time: {duration}")

    @staticmethod
    async def create_request(url, request_method, payload=None, headers=None, params=None, session=None):
        """
        Executes an HTTP request and returns a tuple: (error or None, status code or None).
        """
        try:
            if not session:
                session = aiohttp.ClientSession()

            async with session.request(
                request_method,
                url,
                json=payload,
                headers={"Authorization": f"Bearer {headers}"} if headers else None,
                params=params
            ) as response:
                await response.text()  # consume response to avoid warning
                return None, response.status

        except Exception as e:
            return e, None

