# Local SDK contracts

Run `uv run --project tools/consumers --locked python tools/consumers/check.py`.
The separate lock fixes LangChain Core 1.7.6, LangSmith 0.14.17 and uuid-utils
0.19.0. LangSmith still requires uuid-utils `<1.0`, while LangChain itself allows
1.x; this consumer environment deliberately respects the combined resolver.

Checks pass explicit UUID values through `RunnableLambda`'s public `run_id`
configuration, a local callback, and LangSmith's Run schema/JSON serializer.
No client is created and tracing is disabled. This checks consumption, not a
drop-in replacement of every uuid-utils function or LangChain's timestamp API.
`uuid7_at(unix_ms=...)` has an explicit millisecond, independent-randomness
contract; it is not an alias for SDK nanosecond generation with monotonic state.
