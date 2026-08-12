from route.repositories.database.common import CommonRepository
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from typing import List,Dict, Optional
from enum import Enum
from schemas.object_search import AnswerProxy ,Protocol
from aiohttp_socks import ProxyConnector
import time

class ProxySites(str, Enum):
    BESTPROXIES = "https://best-proxies.ru/proxylist/free/"

class CommonService:
    """Сервис, который опрашивает внешние прокси сайты,
    выбирает рабочие прокси и вносит в бд,
    обновление бд должно происходить ежедневно или по вызову"""

    def __init__(self, repo: CommonRepository):
        self.repo = repo
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.request_on_sites_proxy: Dict[str, Dict] = {}



    """
    Этот метод создан для специально для sheduler.
    Ежедневно подключенная база данных redis пополняется новыми записями proxy-servers.
    данные записи формируются из выдачи откветов сайта proxy
    "https://best-proxies.ru/proxylist/free/"
    """
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
        res_bach = []
        if new_proxys is not None:
            for proxy in new_proxys:
                try:
                    proxy_addr = f"{proxy.ip}:{proxy.port}"
                    proxy_type = proxy.protocol.value
                    proxy_url = f"{proxy_type}://{proxy_addr}"
                    connector = ProxyConnector.from_url(proxy_url)

                    async with aiohttp.ClientSession(connector=connector) as session:
                        start_time = time.time()
                        async with session.get(
                            'https://api.ipify.org/',
                            timeout=aiohttp.ClientTimeout(total=10),
                            ssl=False
                        ) as response:
                            response_time = time.time() - start_time
                            ip = await response.text()

                            if ip:
                                res_bach.append(proxy)
                                print(f"✅ {proxy_addr} работает, IP: {ip}, время: {response_time:.2f}с")
                            else:
                                print(f"❌ {proxy_addr} - не удалось получить IP")

                except Exception as e:
                    print(f"❌ {proxy_addr} - ошибка: {str(e)}")
                    continue

        pipeline = await self.repo.add_proxies_batch(res_bach)

    async def get_works_proxy(self)-> Dict[str, Dict]:
        if  len(self.request_on_sites_proxy) < 8:
            proxys = await self.repo.get_all_proxies()
            for proxy in proxys:
                if not proxy.ip in self.request_on_sites_proxy:
                    self.request_on_sites_proxy[proxy.ip] = {
                        "port": proxy.port,
                        "hostname": proxy.hostname,
                        "protocol": proxy.protocol,
                        "count_of_calls": 0
                    }
        return self.request_on_sites_proxy
