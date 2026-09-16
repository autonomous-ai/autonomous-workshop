"""Cancellable native geometry in one disposable, sequential worker process."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time


MAX_RESPONSE_BYTES = 16 * 1024 * 1024


def seconds(name: str, default: float) -> float:
    value = float(os.environ.get(name, default))
    if not math.isfinite(value) or value <= 0 or value > 86_400:
        raise ValueError(f"{name} must be finite and in (0, 86400]")
    return value


class GeometryWorker:
    def __init__(self, *, command=None, timeout=None, operation_timeout=None):
        self.command = command or [sys.executable, str(Path(__file__).resolve().parents[1]), "worker"]
        self.timeout = seconds("WORKSHOP_GEOMETRY_TIMEOUT", 600) if timeout is None else timeout
        self.operation_timeout = seconds("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", 60) if operation_timeout is None else operation_timeout
        self.deadline = time.monotonic() + self.timeout
        self.process = None
        self.selector = None
        self.progress_fd = None
        self.lifetime_fd = None
        self.buffers = {}
        self.cancelled = False
        self.last_notice = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        process, self.process = self.process, None
        if process is not None:
            # Reap the entire owned process group, including native children.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        if self.selector is not None:
            self.selector.close()
            self.selector = None
        if self.progress_fd is not None:
            os.close(self.progress_fd)
            self.progress_fd = None
        if self.lifetime_fd is not None:
            os.close(self.lifetime_fd)
            self.lifetime_fd = None
        self.buffers = {}

    def cancel(self):
        self.cancelled = True
        self.close()

    def _start(self):
        control_read, control_write = os.pipe()
        lifetime_read, self.lifetime_fd = os.pipe()
        environment = {**os.environ, "CADGEN_WARM": "0", "WORKSHOP_INSPECTION_CHILD": "1",
                       "PYTHONDONTWRITEBYTECODE": "1", "WORKSHOP_GEOMETRY_PROGRESS_FD": str(control_write)}
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("worker_guard.py")),
                 str(lifetime_read), str(max(.01, self.deadline - time.monotonic())), *self.command],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=environment, bufsize=0, start_new_session=True, pass_fds=(control_write, lifetime_read),
            )
        except BaseException:
            os.close(control_read)
            os.close(self.lifetime_fd)
            self.lifetime_fd = None
            raise
        finally:
            os.close(control_write)
            os.close(lifetime_read)
        self.progress_fd = control_read
        self.selector = selectors.DefaultSelector()
        for stream, kind in ((self.process.stdout, "stdout"), (self.process.stderr, "stderr"), (control_read, "control")):
            fd = stream if isinstance(stream, int) else stream.fileno()
            os.set_blocking(fd, False)
            self.selector.register(fd, selectors.EVENT_READ, kind)
            self.buffers[kind] = b""

    @staticmethod
    def _unfinished(request, reason, progress):
        failed = bool(progress.get("failures", 0))
        result = {"ok": False, "status": "failed" if failed else "unverified",
                  "failureCount": progress.get("failures", 0), "errors": [],
                  "unverified": [reason], "completedChecks": progress.get("completed", 0),
                  "lastOperation": progress.get("label", "request startup")}
        return {"id": request.get("id"), "ok": False, "exitCode": 2 if failed else 3, "result": result}

    def request(self, request):
        progress = {}
        if self.cancelled or time.monotonic() >= self.deadline:
            return self._unfinished(request, "geometry inspection cancelled" if self.cancelled else "geometry inspection time allowance exhausted", progress)
        if self.process is None:
            self._start()
        operation_deadline = self.deadline
        try:
            self.process.stdin.write((json.dumps(request) + "\n").encode())
            while True:
                now = time.monotonic()
                if now >= min(self.deadline, operation_deadline):
                    reason = "geometry inspection time allowance exhausted" if now >= self.deadline else "native geometry operation exceeded its time allowance"
                    self.close()
                    return self._unfinished(request, reason, progress)
                events = self.selector.select(min(0.2, self.deadline - now, operation_deadline - now))
                for key, _ in events:
                    block = os.read(key.fd, 65536)
                    if not block:
                        self.selector.unregister(key.fd)
                        continue
                    kind = key.data
                    if kind == "stderr":
                        sys.stderr.write(block.decode("utf-8", errors="replace"))
                        sys.stderr.flush()
                        continue
                    self.buffers[kind] += block
                    if len(self.buffers[kind]) > MAX_RESPONSE_BYTES:
                        raise ValueError("geometry worker response exceeds its size bound")
                    while b"\n" in self.buffers[kind]:
                        line, self.buffers[kind] = self.buffers[kind].split(b"\n", 1)
                        message = json.loads(line)
                        if not isinstance(message, dict):
                            raise ValueError("geometry worker returned a non-object")
                        if kind == "stdout":
                            if message.get("id") != request.get("id") or type(message.get("ok")) is not bool or message.get("exitCode") not in (0, 2, 3):
                                raise ValueError("geometry worker response does not match its request")
                            return message
                        if message.get("request") is not None and message["request"] != json.dumps(request.get("id")):
                            continue
                        event = message.get("event")
                        known_failures = progress.get("failures", 0)
                        if event == "measurement-failed":
                            progress["failures"] = max(1, known_failures)
                            continue
                        # Liveness is deliberately not progress. Only a concrete
                        # operation boundary resets the per-operation allowance.
                        if event == "operation-start":
                            progress.update(message)
                            progress["failures"] = max(known_failures, progress.get("failures", 0))
                            allowance = self.timeout if message.get("kind") == "build" else self.operation_timeout
                            operation_deadline = min(self.deadline, time.monotonic() + allowance)
                        elif event == "operation-done":
                            progress.update(message)
                            progress["failures"] = max(known_failures, progress.get("failures", 0))
                            operation_deadline = self.deadline
                        if event in ("operation-start", "operation-done") and time.monotonic() - self.last_notice >= 1:
                            self.last_notice = time.monotonic()
                            if os.environ.get("WORKSHOP_PROGRESS", "").lower() not in ("0", "off", "false", "no"):
                                print(f"[inspect] {message.get('kind')}: {message.get('label')}; "
                                      f"completed={progress.get('completed', 0)} reused={progress.get('reused', 0)}",
                                      file=sys.stderr, flush=True)
                if self.process.poll() is not None and not self.selector.get_map():
                    reason = "geometry worker exited without a complete verdict"
                    self.close()
                    return self._unfinished(request, reason, progress)
        except KeyboardInterrupt:
            self.cancel()
            return self._unfinished(request, "geometry inspection cancelled", progress)
        except (OSError, ValueError) as error:
            self.close()
            # Protocol/input errors are failures, not an authorization to skip.
            return {"id": request.get("id"), "ok": False, "exitCode": 2,
                    "result": {"ok": False, "errors": [{"message": str(error)}]}}
