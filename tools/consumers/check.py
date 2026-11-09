"""Local-only UUID consumption through actual LangChain/LangSmith interfaces."""

import importlib.metadata
import json
import os
import uuid
from datetime import datetime, timezone

# Do not create a client or send a trace; callbacks and schemas run locally.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_core.callbacks import BaseCallbackHandler  # noqa: E402
from langchain_core.runnables import RunnableLambda  # noqa: E402
from langsmith.schemas import Run  # noqa: E402

import fastuuid7 as f  # noqa: E402


class Recorder(BaseCallbackHandler):
    def __init__(self):
        self.ids = []

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):  # noqa: ARG002
        self.ids.append(run_id)


def main():
    for value in [f.uuid4(), f.uuid7(), f.parse(str(f.uuid7())), f.uuid7_at(unix_ms=42)]:
        assert isinstance(value, uuid.UUID)
        recorder = Recorder()
        result = RunnableLambda(lambda x: x + 1).invoke(
            4, config={"run_id": value, "callbacks": [recorder]}
        )
        assert result == 5 and recorder.ids == [value]
        run = Run(
            id=value,
            name="local-uuid-contract",
            start_time=datetime.now(timezone.utc),
            run_type="chain",
            inputs={"x": 4},
            outputs={"x": result},
        )
        assert run.id == value and json.loads(run.model_dump_json())["id"] == str(value)
    print(
        json.dumps(
            {
                "status": "passed",
                "packages": {
                    name: importlib.metadata.version(name)
                    for name in ["fastuuid7", "langchain-core", "langsmith", "uuid-utils"]
                },
                "contracts": [
                    "explicit Runnable run_id and local callback",
                    "LangSmith Run UUID and JSON",
                ],
                "limitations": "No SDK default replacement, trace upload, or throughput claim",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
