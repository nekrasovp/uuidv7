"""Loopback HTTP server for the full UUID request/response benchmark."""

import os
import resource
import sys
import time

from common import TEXTS, identity
from contracts import configuration
from fastapi import FastAPI, HTTPException
from pydantic import Field, create_model


def create_app(variant=None):
    variant = variant or os.environ["UUID_BENCH_VARIANT"]
    model, single, scalar_type, provider = configuration(variant)
    ready = model(ids=TEXTS)
    generated = {}
    for version in (4, 7):
        generator = getattr(provider, f"uuid{version}")
        generated[version] = create_model(
            f"GeneratedV{version}",
            __base__=model,
            ids=(
                model.__annotations__["ids"],
                Field(default_factory=lambda gen=generator: [gen() for _ in range(64)]),
            ),
        )
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"variant": variant, "identity": identity()}

    @app.get("/metrics")
    async def metrics():
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "cpu": time.process_time(),
            "rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
        }

    @app.get("/item/{item_id}", response_model=single)
    async def item(item_id: scalar_type):
        return {"id": item_id}

    @app.post("/batch", response_model=model)
    async def batch(payload: model):
        return payload

    @app.get("/response", response_model=model)
    async def response():
        return ready

    @app.get("/generate/{version}", response_model=model)
    async def generate(version: int):
        if version not in generated:
            raise HTTPException(status_code=404)
        return generated[version]()

    return app
