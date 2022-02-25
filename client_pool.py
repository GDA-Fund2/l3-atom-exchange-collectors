from datetime import datetime
import sys
import asyncio
import websockets
import signal
import json
import random

host = "194.233.73.248"
port = "30205"

random.seed(30205)

topics = [
    "bybit", 
    "ftx", 
    "kraken", 
    "binance", 
    "bitfinex", 
    "okex", 
    "kucoin", 
    "kraken-futures", 
    "phemex", 
    "coinbase",
    "deribit",
    "huobi",
    "dydx",
    "apollox",
    "BTCUSD",
    "BTCUSDT"
]

total_messages = 0
clients_connected = 0

async def subscribe(ws):
    for topic in topics:
        request = {
            "op": "subscribe",
            "topic": topic
        }
        await ws.send(json.dumps(request))

async def unsubscribe(ws):
    for topic in topics:
        request = {
            "op": "unsubscribe",
            "topic": topic
        }
        await ws.send(json.dumps(request))

async def recv_messages(ws):
    global total_messages
    async for msg in ws:
        total_messages += 1

async def send_rand(ws):
    while True:
        op = "subscribe" if random.randint(0, 1) == 0 else "unsubscribe"
        topic = topics[random.randint(0,len(topics)-1)]
        request = {
            "op": op,
            "topic": topic
        }
        await ws.send(json.dumps(request))
        await asyncio.sleep(random.randint(0,10))

async def start_dummy_client(cid):
    global clients_connected
    async with websockets.connect("ws://" + host + ":" + port + "/") as ws:
        clients_connected += 1
        try:
            print(f"[{datetime.now()}] {cid}: started")
            await subscribe(ws)
            # asyncio.create_task(send_rand(ws))
            await recv_messages(ws)
        except websockets.ConnectionClosed:
            print(f"[{datetime.now()}] {cid}: websocket connection closed")
        except asyncio.CancelledError:
            print(f"[{datetime.now()}] {cid}: websocket task cancelled, unsubscribing...")
            await unsubscribe(ws)
            print(f"[{datetime.now()}] {cid}: unsubscribed")
        finally:
            clients_connected -= 1

async def main():
    if len(sys.argv) == 2:
        n_clients = int(sys.argv[1])
    else:
        n_clients = 10

    tasks = []
    stop = asyncio.Future()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGUSR1, lambda: asyncio.create_task(shutdown("SIGUSR1", tasks, stop)))
    loop.add_signal_handler(signal.SIGUSR2, lambda: asyncio.create_task(dump_handler("SIGUSR2", n_clients)))
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown("SIGINT", tasks, stop)))
    
    for i in range(n_clients):
        tasks.append(asyncio.create_task(start_dummy_client(i)))
        await asyncio.sleep(0.5)
    print(f"[{datetime.now()}] system: started {n_clients} clients")

    asyncio.create_task(dump(n_clients, stop))
    await stop

async def dump(n_clients, stop):
    while not stop.done():
        print(f"[{datetime.now()}] system: total_messages={total_messages}, avg_messages={total_messages/n_clients}, clients_connected={clients_connected}", flush=True)
        await asyncio.sleep(600)

async def dump_handler(signum, n_clients):
    print(f"[{datetime.now()}] system: dump signal {signum} received")
    print(f"[{datetime.now()}] system: total_messages={total_messages}, avg_messages={total_messages/n_clients}, clients_connected={clients_connected}", flush=True)

async def shutdown(signum, tasks, stop):
    print(f"[{datetime.now()}] system: shutdown signal {signum} received")
    print(f"[{datetime.now()}] system: cancelling tasks...")
    for task in tasks:
        task.cancel()
    print(f"[{datetime.now()}] system: setting stop flag...")
    stop.set_result(True)
    print(f"[{datetime.now()}] system: client pool finished")

if __name__ == "__main__":
    asyncio.run(main())