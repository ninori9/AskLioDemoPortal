from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from contextlib import contextmanager
import signal, uuid
from pydantic import BaseModel

I = TypeVar("I", bound=BaseModel)
O = TypeVar("O", bound=BaseModel)

class AgentError(RuntimeError): ...
class AgentTimeout(AgentError): ...

@contextmanager
def deadline(seconds: float):
    def _timeout(_signum, _frame): raise AgentTimeout("agent timed out")
    old = signal.signal(signal.SIGALRM, _timeout)
    try:
        signal.alarm(int(seconds))
        yield
    finally:
        signal.alarm(0); signal.signal(signal.SIGALRM, old)

class Agent(Generic[I, O], ABC):
    """Single-skill agent: I -> O (typed)."""
    name: str = "agent"
    version: str = "1.0"

    @abstractmethod
    def run(self, payload: I) -> O: ...

    def run_with_timeout(self, payload: I, timeout_s: float = 5.0) -> O:
        with deadline(timeout_s):
            return self.run(payload)

    @staticmethod
    def new_trace_id() -> str:
        return str(uuid.uuid4())