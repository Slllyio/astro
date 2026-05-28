"""App-level service helpers for the Medini stack.

Services here are runtime singletons used by the FastAPI routes. They differ
from `app/medini/ml/*` (which are CLI batch tools) by being designed for
long-lived in-process reuse (lazy model load, cached vectors).
"""
