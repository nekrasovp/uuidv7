"""Actual ASGI application for the isolated load study."""

import os
import resource
import time
import uuid

from common import TEXTS
from fastapi import FastAPI
from integration import BulkModel, FastUUID, NativeModel, ScalarModel, StandardModel

VARIANT = os.environ.get("UUID_LAB_VARIANT", "standard")
MODEL = {
    "standard": StandardModel,
    "scalar": ScalarModel,
    "bulk": BulkModel,
    "native": NativeModel,
}[VARIANT]
PATH_TYPE = uuid.UUID if VARIANT == "standard" else FastUUID
app = FastAPI()
READY = MODEL(ids=TEXTS[:1000])


@app.get("/health")
async def health():
    return {"ready": True, "variant": VARIANT}


@app.get("/metrics")
async def metrics():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"cpu": time.process_time(), "rss": usage.ru_maxrss}


@app.get("/item/{item_id}")
async def item(item_id: PATH_TYPE):
    return {"id": str(item_id)}


@app.post("/batch", response_model=MODEL)
async def batch(payload: MODEL):
    return payload


@app.get("/response", response_model=MODEL)
async def response():
    return READY
