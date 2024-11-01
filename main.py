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

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = ProxyConnector.from_url(socks5_proxy)
            
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
                            logger.debug(send_message)
                            await websocket.send(send_message)
                            await asyncio.sleep(20)

                    await asyncio.sleep(1)
                    ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            logger.info(message)
                            
                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "extension",
                                        "version": "2.5.0"
                                    }
                                }
                                logger.debug(auth_response)
                                await websocket.send(json.dumps(auth_response))
                            
                            elif message.get("action") == "PONG":
                                pong_response = {
                                    "id": message["id"],
                                    "origin_action": "PONG"
                                }
                                logger.debug(pong_response)
                                await websocket.send(json.dumps(pong_response))
                    
                    finally:
                        ping_task.cancel()
                        
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)
            await asyncio.sleep(5)  # 添加重试延迟


async def main():
    # GANTI USERID
    _user_id = 'user_id'
    # ISI PROXY DARI IPROYAL
    socks5_proxy_list = [
        'socks5://user:pwd@ip:port',
    ]
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in socks5_proxy_list]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # # RUNNING
    asyncio.run(main())
