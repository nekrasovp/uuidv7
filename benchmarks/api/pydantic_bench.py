"""One fresh-process Pydantic measurement; no HTTP transport overhead."""

import argparse
import json
import random
import statistics
import timeit

from common import TEXTS, identity
from contracts import configuration
from pydantic import ValidationError


def measure(variant, seed):
    model, _, _, _ = configuration(variant)
    cases = []
    for size in (1, 64, 1000):
        payload = {"ids": TEXTS[:size], "label": "sample"}
        body = json.dumps(payload).encode()
        ready = model.model_validate_json(body)
        assert json.loads(ready.model_dump_json()) == payload
        scope = {"model": model, "body": body, "ready": ready}
        for operation, statement in (
            ("validate_json", "model.model_validate_json(body)"),
            ("dump_json", "ready.model_dump_json()"),
            ("round_trip", "model.model_validate_json(body).model_dump_json()"),
        ):
            cases.append((f"{operation}/{size}", statement, scope))
    bad = json.dumps({"ids": [TEXTS[0], "bad"], "label": "sample"}).encode()

    def reject():
        try:
            model.model_validate_json(bad)
        except ValidationError as error:
            return error
        raise AssertionError("invalid UUID accepted")

    assert reject().errors()[0]["loc"] == ("ids", 1)
    cases.append(("invalid/2", "reject()", {"reject": reject}))
    random.Random(seed).shuffle(cases)
    rows = []
    for key, statement, scope in cases:
        timer = timeit.Timer(statement, globals=scope)
        loops = 1
        while timer.timeit(loops) < 0.025:
            loops *= 2
        timer.timeit(loops)
        values = [timer.timeit(loops) * 1e9 / loops for _ in range(3)]
        rows.append(
            {
                "case": key,
                "unit": "ns/model",
                "loops": loops,
                "samples_ns": values,
                "mean_ns": statistics.mean(values),
            }
        )
    return {"variant": variant, "seed": seed, "identity": identity(), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(measure(args.variant, args.seed)))
