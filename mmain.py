import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
import websockets
from typing import List, Dict, Tuple

# 账号和代理的配置类
class AccountConfig:
    def __init__(self, user_id: str, proxy: str):
        self.user_id = user_id
        self.proxy = proxy

async def connect_to_wss(account_config: AccountConfig):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, account_config.proxy))
    logger.info(f"Starting connection for user {account_config.user_id} with device {device_id}")
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = ProxyConnector.from_url(account_config.proxy)
            
            async with ClientSession(connector=connector) as session:
                async with websockets.connect(
                    'wss://proxy.wynd.network:4650/',
                    extra_headers=custom_headers,
                    ssl=ssl_context
                ) as websocket:
                    
                    async def send_ping():
                        while True:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"[User: {account_config.user_id}] {send_message}")
                            await websocket.send(send_message)
                            await asyncio.sleep(20)

                    await asyncio.sleep(1)
                    ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            logger.info(f"[User: {account_config.user_id}] {message}")
                            
                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": account_config.user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "extension",
                                        "version": "2.5.0"
                                    }
                                }
                                logger.debug(f"[User: {account_config.user_id}] {auth_response}")
                                await websocket.send(json.dumps(auth_response))
                            
                            elif message.get("action") == "PONG":
                                pong_response = {
                                    "id": message["id"],
                                    "origin_action": "PONG"
                                }
                                logger.debug(f"[User: {account_config.user_id}] {pong_response}")
                                await websocket.send(json.dumps(pong_response))
                    
                    finally:
                        ping_task.cancel()
                        
        except Exception as e:
            logger.error(f"[User: {account_config.user_id}] Error: {e}")
            logger.error(f"[User: {account_config.user_id}] Proxy: {account_config.proxy}")
            await asyncio.sleep(5)

async def main():
    # 账号和代理的配置列表
    configs = [
        AccountConfig(
            user_id="user_id_1",
            proxy="socks5://user1:pwd1@ip1:port1"
        ),
        AccountConfig(
            user_id="user_id_2",
            proxy="socks5://user2:pwd2@ip2:port2"
        ),
        AccountConfig(
            user_id="user_id_3",
            proxy="socks5://user3:pwd3@ip3:port3"
        ),
        # 可以继续添加更多账号和代理的配置
    ]
    
    tasks = [asyncio.ensure_future(connect_to_wss(config)) for config in configs]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    # 设置日志格式
    logger.add(
        "logs/wynd_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        encoding="utf-8"
    )
    
    # 运行主程序
    asyncio.run(main())
