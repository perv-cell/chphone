from route.repositories.database.common import CommonRepository
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from typing import List,Dict, Optional
from enum import Enum
from schemas.object_search import AnswerProxy ,Protocol


class ProxySites(str, Enum):
    BESTPROXIES = "https://best-proxies.ru/proxylist/free/"

class CommonService:
    """Сервис, который опрашивает внешние прокси сайты,
    выбирает рабочие прокси и вносит в бд,
    обновление бд должно происходить ежедневно или по вызову"""

    def __init__(self, repo: CommonRepository):
        self.repo = repo
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.request_on_sites_proxy = {}

    async def checking_work_proxy(self)-> List[AnswerProxy]:
        params = {
                "key": "developer",
                "limit": 50,
                "type": "socks4,socks5",
            }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
            async with session.get("https://api.best-proxies.ru/proxylist.json", params=params) as response:
                data = await response.json()
                result = []

                if type(data) == list:
                    for server in data:
                        ip = server.get("ip")
                        port= server.get("port")
                        hostname = server.get("hostname")
                        socks4= server.get("socks4", False)
                        socks5 = server.get("socks5",False)
                        use_protocol = None

                        if ip is None or port is None or hostname is None:
                            continue

                        if socks4:
                            use_protocol = Protocol.SOCKS4

                        if socks5:
                            use_protocol = Protocol.SOCKS5

                        if use_protocol is None:
                            continue

                        param_proxy = AnswerProxy(
                            ip=ip,
                            port=port,
                            hostname=hostname,
                            protocol=use_protocol
                        )
                        result.append(param_proxy)
                return result

    async def save_works_proxys(self, new_proxys: Optional[List[AnswerProxy]] = None):
        if new_proxys is not None:
            pipeline = await self.repo.add_proxies_batch(new_proxys)
