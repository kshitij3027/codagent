---
status: resolved
trigger: "Pressing Ctrl-C at the idle >>> prompt causes a Python traceback from the threading module instead of exiting cleanly"
created: 2026-02-25T10:00:00Z
updated: 2026-02-25T10:30:00Z
---

## Current Focus

hypothesis: CONFIRMED -- SystemExit in asyncio signal handler cannot interrupt the blocking input() thread, causing deadlock during shutdown
test: Code path analysis + CPython issue research
expecting: n/a (confirmed)
next_action: Return diagnosis to caller

## Symptoms

expected: Ctrl-C at idle prompt exits the program cleanly without Python traceback
actual: Had to press Ctrl-C multiple times. Got traceback from threading module
errors: |
  Exception ignored in: <module 'threading' from '/usr/local/lib/python3.12/threading.py'>
  Traceback (most recent call last):
    File "/usr/local/lib/python3.12/threading.py", line 1594, in _shutdown
      atexit_call()
    File "/usr/local/lib/python3.12/concurrent/futures/thread.py", line 31, in _python_exit
      t.join()
    File "/usr/local/lib/python3.12/threading.py", line 1149, in join
      self._wait_for_tstate_lock()
    File "/usr/local/lib/python3.12/threading.py", line 1169, in _wait_for_tstate_lock
      if lock.acquire(block, timeout):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  KeyboardInterrupt:
reproduction: Test 9 in UAT -- at idle >>> prompt, press Ctrl-C
started: Discovered during UAT

## Eliminated

## Evidence

- timestamp: 2026-02-25T10:01:00Z
  checked: signals.py _handle_sigint() idle branch
  found: When agent_task is None (idle), handler raises SystemExit(0). This is raised inside the asyncio event loop callback.
  implication: SystemExit propagates up through the event loop into asyncio.run(), triggering its shutdown sequence.

- timestamp: 2026-02-25T10:02:00Z
  checked: main.py line 56 -- REPL input path
  found: At idle, the REPL is awaiting `loop.run_in_executor(None, _get_input)` where `_get_input` calls blocking `input(">>> ")`. This runs on the default ThreadPoolExecutor. The thread is blocked on stdin.
  implication: When SystemExit is raised, asyncio.run() begins shutdown. It calls loop.shutdown_default_executor() which tries to join all executor threads. But the input() thread is blocked on stdin -- it will NEVER complete until the user types something or the process is killed.

- timestamp: 2026-02-25T10:03:00Z
  checked: asyncio.run() shutdown sequence (CPython source)
  found: asyncio.run() catches SystemExit/KeyboardInterrupt, cancels all tasks, then calls loop.shutdown_default_executor(). shutdown_default_executor sets a shutdown sentinel on the executor and calls executor._threads to join them. The thread running input() is blocked and cannot be joined.
  implication: The join() call blocks indefinitely (or until timeout in newer Python). The user pressing Ctrl-C again during this join produces the traceback from threading._shutdown.

- timestamp: 2026-02-25T10:04:00Z
  checked: CPython issues #96827 and #111358
  found: This is a known CPython limitation. ThreadPoolExecutor threads running blocking I/O cannot be interrupted by SystemExit or cancellation. The executor shutdown deadlocks trying to join the blocked thread. Multiple Ctrl-C presses are needed, and the threading._shutdown traceback is the direct consequence.
  implication: The current design (raise SystemExit from signal handler while input() thread is blocking) will always hit this issue. The fix must either: (a) avoid blocking input() in a thread entirely, (b) use os._exit() to bypass Python shutdown, or (c) make the input thread interruptible/daemon.

- timestamp: 2026-02-25T10:05:00Z
  checked: main.py outer wrapper (main() function, lines 103-113)
  found: The `except (KeyboardInterrupt, SystemExit): pass` in main() catches the exception from asyncio.run(), but by that point asyncio.run() has already attempted (and deadlocked on) shutdown_default_executor. The traceback occurs during Python interpreter shutdown (threading._shutdown atexit handler), which is AFTER main() has returned.
  implication: The try/except in main() cannot prevent this traceback because it happens after main() completes, in the interpreter's atexit shutdown phase.

## Resolution

root_cause: |
  The signal handler (signals.py line 47) raises SystemExit(0) when Ctrl-C is pressed at idle.
  At that moment, main.py line 56 has a thread blocked on input(">>> ") via run_in_executor.

  The shutdown sequence is:
  1. SystemExit(0) raised in _handle_sigint callback
  2. asyncio.run() catches it, begins cleanup
  3. asyncio.run() calls loop.shutdown_default_executor()
  4. Executor tries to join() the thread running input() -- but input() is blocked on stdin
  5. join() deadlocks (thread will never finish on its own)
  6. User presses Ctrl-C again, interrupting the join() call
  7. Python interpreter exits, threading._shutdown atexit handler tries to join again
  8. Another Ctrl-C interrupts that join, producing the traceback

  This is a known CPython limitation (issues #96827, #111358): ThreadPoolExecutor threads
  running blocking I/O cannot be cancelled or interrupted during executor shutdown.

  The fundamental problem: using run_in_executor + blocking input() for the REPL prompt
  creates an unjoinable thread that deadlocks Python's shutdown sequence.
fix:
verification:
files_changed: []
