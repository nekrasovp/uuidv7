"""Executable contracts; run with --build PATH --expected-gil on|off.

Uses unittest only. Dangerous fork probes run in timeout-bounded subprocesses.
Never imports the production extension into a no-GIL test process.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path

MAX_MS = (1 << 48) - 1
MAX_COUNTER = (1 << 42) - 1
FIXED_MS = 1_800_000_000_000


def values(raw):
    return [int.from_bytes(raw[i : i + 16], "big") for i in range(0, len(raw), 16)]


def check_records(records):
    """Check sequence tickets AND real-time precedence, not return order."""
    ordered = sorted(records, key=lambda record: record[0])
    all_values = []
    next_ticket = ordered[0][0]
    for ticket, raw, _, _ in ordered:
        assert ticket == next_ticket, "gap or overlap in successful reservations"
        parsed = values(raw)
        next_ticket += len(parsed)
        all_values.extend(parsed)
    assert len(set(all_values)) == len(all_values), "duplicate UUID"
    assert all(a < b for a, b in zip(all_values, all_values[1:])), "value-order violation"
    for value in all_values:
        assert (value >> 76) & 15 == 7 and (value >> 62) & 3 == 2, "invalid UUID layout"
    ended = sorted(records, key=lambda record: record[3])
    cursor, completed_max = 0, -1
    for record in sorted(records, key=lambda record: record[2]):
        while cursor < len(ended) and ended[cursor][3] < record[2]:
            completed_max = max(completed_max, values(ended[cursor][1])[-1])
            cursor += 1
        assert values(record[1])[0] > completed_max, "non-overlapping calls reordered"
    return len(all_values)


def concurrent_records(module, threads, calls=1000):
    barrier = threading.Barrier(threads)

    def worker():
        records = []
        barrier.wait(timeout=30)
        for i in range(calls):
            count = 1 if i % 2 == 0 else 17
            start = time.perf_counter_ns()
            ticket, raw, _, _ = module.generate(count, FIXED_MS, True)
            end = time.perf_counter_ns()
            records.append((ticket, raw, start, end))
        return records

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        jobs = [pool.submit(worker) for _ in range(threads)]
        return [record for job in jobs for record in job.result(timeout=60)]


def interpreter_record(build_path, timestamp):
    # Stateless callable copied by concurrent.interpreters.call: no parent
    # globals, PyObject pointers, or extension-module instances are transferred.
    import sys
    import time
    import uuid

    sys.path.insert(0, build_path)
    import _ft_uuid7 as module

    assert module.cached_type() is uuid.UUID
    start = time.perf_counter_ns()
    ticket, raw, _, _ = module.generate(1000, timestamp, True)
    end = time.perf_counter_ns()
    assert type(module.as_uuid(raw[:16])) is uuid.UUID
    return ticket, raw, start, end


def fork_probe(module, active):
    # Exercise multiple threads first, joined before the ordinary fork case.
    check_records(concurrent_records(module, 4, calls=100))
    module.set_state(MAX_MS - 1, 123)
    worker = None
    if active:
        ready_read, ready_write = os.pipe()
        worker = threading.Thread(target=module.hold_lock, args=(ready_write,))
        worker.start()
        assert os.read(ready_read, 1) == b"L"
        os.close(ready_read)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        # A timed-out parent probe must not leave a deadlocked child behind.
        signal.alarm(10)
        try:
            state = module.snapshot()
            assert state[:4] == (0, 0, os.getpid(), 0), state
            assert state[4:] == (4096, 0), state
            # Empty inherited pool must need fresh entropy: hard failure proves
            # the child cannot silently consume its parent's cached bytes.
            module.entropy_fault(1)
            try:
                module.generate()
            except OSError:
                pass
            else:
                raise AssertionError("child used inherited entropy")
            module.entropy_fault(0)
            raw = module.generate(64)
            assert values(raw)[0] >> 80 < MAX_MS - 1
            os.write(write_fd, raw)
            os._exit(0)
        except BaseException:
            os._exit(2)
    os.close(write_fd)
    child_raw = bytearray()
    while True:
        chunk = os.read(read_fd, 4096)
        if not chunk:
            break
        child_raw.extend(chunk)
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    if worker:
        worker.join(timeout=5)
        assert not worker.is_alive()
        os.close(ready_write)
    assert os.waitstatus_to_exitcode(status) == 0, status
    assert len(child_raw) == 64 * 16
    parent = module.generate(64)
    assert not set(values(parent)) & set(values(child_raw))
    assert values(parent)[0] >> 80 == MAX_MS - 1


class PrototypeContracts(unittest.TestCase):
    def setUp(self):
        ft.reset()

    def test_gil_mode_is_verified_after_import(self):
        self.assertEqual(sys._is_gil_enabled(), EXPECTED_GIL)

    def test_ordering_oracle_rejects_corrupted_histories(self):
        raw = ft.generate(2, FIXED_MS)
        first, second = raw[:16], raw[16:]
        valid = [(0, first, 0, 2), (1, second, 3, 4)]
        self.assertEqual(check_records(valid), 2)
        for invalid in (
            [(0, first, 0, 2), (1, first, 3, 4)],  # duplicate value
            [(0, first, 0, 2), (0, second, 3, 4)],  # ticket overlap
            [(0, second, 0, 2), (1, first, 3, 4)],  # value inversion
            [(0, first, 20, 30), (1, second, 0, 10)],  # real-time precedence
        ):
            with self.assertRaises(AssertionError):
                check_records(invalid)

    def test_concurrent_scalar_batch_linearization(self):
        for threads in (1, 2, 4, 8):
            with self.subTest(threads=threads):
                ft.reset()
                records = concurrent_records(ft, threads)
                self.assertEqual(check_records(records), threads * 9000)

    def test_completion_order_is_not_value_order(self):
        read_fd, write_fd = os.pipe()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(ft.generate, 1, FIXED_MS, True, False, False, read_fd)
            try:
                deadline = time.monotonic() + 10
                while ft.snapshot()[3] == 0:
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.001)
                second = ft.generate(1, FIXED_MS, True)
                self.assertFalse(first.done())
            finally:
                os.write(write_fd, b"R")
            earlier = first.result(timeout=10)
        os.close(read_fd)
        os.close(write_fd)
        self.assertLess(earlier[0], second[0])
        self.assertLess(earlier[1], second[1])

    def test_rollback_and_counter_carry(self):
        for initial_counter in ((1 << 30) - 2, MAX_COUNTER - 1):
            ft.set_state(FIXED_MS, initial_counter)
            raw = ft.generate(4, FIXED_MS - 100)
            parsed = values(raw)
            self.assertEqual(parsed, sorted(set(parsed)))
            self.assertGreaterEqual(parsed[-1] >> 80, FIXED_MS)
        self.assertEqual(parsed[-1] >> 80, FIXED_MS + 1)

    def test_timestamp_exhaustion_consumes_prefix_but_returns_no_batch(self):
        ft.set_state(MAX_MS, MAX_COUNTER - 1)
        with self.assertRaises(OverflowError):
            ft.generate(2, MAX_MS)
        self.assertEqual(ft.snapshot()[:2], (MAX_MS, MAX_COUNTER))
        self.assertEqual(ft.snapshot()[3], 1)
        with self.assertRaises(OverflowError):
            ft.generate(1, MAX_MS)

    def test_entropy_failure_does_not_commit_failed_item(self):
        ft.set_state(FIXED_MS, 100)
        before = ft.snapshot()
        ft.entropy_fault(1)
        with self.assertRaises(OSError):
            ft.generate(1, FIXED_MS)
        self.assertEqual(ft.snapshot()[:4], before[:4])
        ft.entropy_fault(0)
        ft.generate(1, FIXED_MS)
        self.assertEqual(ft.snapshot()[1], 101)

    def test_seed_success_then_tail_failure_does_not_commit(self):
        ft.generate(1, FIXED_MS)
        before = ft.snapshot()
        ft.entropy_fault(2)
        with self.assertRaises(OSError):
            ft.generate(1, FIXED_MS + 1)
        self.assertEqual(ft.snapshot()[:4], before[:4])

    def test_mid_batch_entropy_failure_consumes_successful_prefix(self):
        ft.generate(1, FIXED_MS)
        before = ft.snapshot()
        ft.entropy_fault(2)
        with self.assertRaises(OSError):
            ft.generate(2, FIXED_MS)
        self.assertEqual(ft.snapshot()[1], before[1] + 1)
        self.assertEqual(ft.snapshot()[3], before[3] + 1)
        ft.entropy_fault(0)
        self.assertEqual(len(ft.generate(2, FIXED_MS)), 32)

    def test_eintr_and_short_entropy_reads(self):
        ft.entropy_fault(3)
        raw = ft.generate(1500, FIXED_MS)
        self.assertEqual(len(set(values(raw))), 1500)

    def test_result_allocation_failure_keeps_consumed_reservation(self):
        with self.assertRaises(MemoryError):
            ft.generate(3, FIXED_MS, False, True)
        self.assertEqual(ft.generate(1, FIXED_MS, True)[0], 3)

    def test_validation_and_empty_batch_do_not_advance(self):
        before = ft.snapshot()
        for args, error in (
            ((-1,), ValueError),
            ((1.5,), TypeError),
            ((sys.maxsize,), MemoryError),
            ((1, MAX_MS + 1), ValueError),
        ):
            with self.assertRaises(error):
                ft.generate(*args)
        self.assertEqual(ft.generate(0), b"")
        self.assertEqual(ft.snapshot(), before)

    def test_concurrent_failures_release_mutex_and_allow_recovery(self):
        ft.entropy_fault(1)

        def fail():
            with self.assertRaises(OSError):
                ft.generate(17)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: fail(), range(80)))
        self.assertEqual(ft.snapshot()[3], 0)
        ft.entropy_fault(0)
        self.assertEqual(check_records(concurrent_records(ft, 4, 100)), 3600)

    def test_historical_calls_share_entropy_without_advancing_live_sequence(self):
        ft.set_state(FIXED_MS, 0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs = [
                pool.submit(ft.generate, 1000, FIXED_MS + 100, False, False, True) for _ in range(4)
            ]
            historical = [value for job in jobs for value in values(job.result())]
        self.assertEqual(len(set(historical)), 4000)
        self.assertEqual(ft.snapshot()[:2], (FIXED_MS, 0))
        self.assertTrue(all(value >> 80 == FIXED_MS + 100 for value in historical))
        self.assertEqual(values(ft.generate(1, FIXED_MS))[0] >> 80, FIXED_MS)

    def test_module_owned_uuid_type(self):
        self.assertIs(ft.cached_type(), uuid.UUID)
        value = ft.as_uuid(ft.generate())
        self.assertIs(type(value), uuid.UUID)
        self.assertEqual(value.version, 7)

    def test_subinterpreter_ownership_and_process_sequence(self):
        # Public 3.14 API; lack of it is reported as an unexecuted test on 3.13.
        try:
            from concurrent import interpreters
        except ImportError:
            self.skipTest("public concurrent.interpreters requires Python 3.14")
        main_type = id(ft.cached_type())
        start = time.perf_counter_ns()
        before = ft.generate(1, FIXED_MS, True)
        records = [(before[0], before[1], start, time.perf_counter_ns())]
        for _ in range(3):
            children = [interpreters.create() for _ in range(2)]
            try:
                for child in children:
                    child.exec(
                        f"import sys; sys.path.insert(0, {str(BUILD)!r}); "
                        "import _ft_uuid7 as f, uuid; "
                        "assert f.cached_type() is uuid.UUID; "
                        f"assert id(f.cached_type()) != {main_type}; "
                        f"assert type(f.as_uuid({before[1]!r})) is uuid.UUID"
                    )
                # Each interpreter's own GIL and cache, one native reservation domain.
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    jobs = [
                        pool.submit(child.call, interpreter_record, str(BUILD), FIXED_MS)
                        for child in children
                    ]
                    records.extend(job.result(timeout=30) for job in jobs)
                self.assertIs(ft.cached_type(), uuid.UUID)
            finally:
                for child in children:
                    child.close()
        start = time.perf_counter_ns()
        after = ft.generate(1, FIXED_MS, True)
        records.append((after[0], after[1], start, time.perf_counter_ns()))
        self.assertEqual(after[0] - before[0], 6001)
        self.assertEqual(check_records(records), 6002)
        self.assertLess(before[1], after[1])

    def test_fork_after_multithreaded_work(self):
        self.run_fork(False)

    def test_fork_with_native_mutex_held(self):
        self.run_fork(True)

    def run_fork(self, active):
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--build",
            str(BUILD),
            "--expected-gil",
            "on" if EXPECTED_GIL else "off",
            "--fork-probe",
            "active" if active else "joined",
        ]
        result = subprocess.run(
            command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    if sys.flags.optimize:
        raise SystemExit("Contract assertions require Python without -O or -OO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--expected-gil", required=True, choices=("on", "off"))
    parser.add_argument("--fork-probe", choices=("joined", "active"))
    args = parser.parse_args()
    BUILD = args.build.resolve()
    EXPECTED_GIL = args.expected_gil == "on"
    sys.path.insert(0, str(BUILD))
    ft = importlib.import_module("_ft_uuid7")
    if sys._is_gil_enabled() != EXPECTED_GIL:
        raise SystemExit("GIL state mismatch; refusing mislabeled evidence")
    if args.fork_probe:
        fork_probe(ft, args.fork_probe == "active")
        print(json.dumps({"fork": args.fork_probe, "status": "pass"}))
    else:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
