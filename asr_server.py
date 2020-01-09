#!/usr/bin/env python3

import sys
import asyncio
import pathlib
import websockets
import concurrent.futures
from kaldi_recognizer import Model, KaldiRecognizer, Gpu

if len(sys.argv) > 1:
   model_path = sys.argv[1]
else:
   model_path = "model"

g = Gpu()
g.Init()
def thread_init():
    g.Instantiate()

model = Model(model_path)
pool = concurrent.futures.ThreadPoolExecutor(initializer=thread_init)
loop = asyncio.get_event_loop()

def process_chunk(rec, message):
    if message == '{"eof" : 1}':
        return rec.FinalResult(), True
    elif rec.AcceptWaveform(message):
        return rec.Result(), False
    else:
        return rec.PartialResult(), False

async def recognize(websocket, path):
    rec = KaldiRecognizer(model);
    while True:
        message = await websocket.recv()
        response, stop = await loop.run_in_executor(pool, process_chunk, rec, message)
        await websocket.send(response)
        if stop: break

start_server = websockets.serve(
    recognize, '0.0.0.0', 2700)

loop.run_until_complete(start_server)
loop.run_forever()
