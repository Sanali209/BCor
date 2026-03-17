# Concurrency

Choose model based on I/O-bound vs. CPU-bound workload.

## Table of Contents
1. [Concurrency Model Selection](#concurrency-model-selection)
2. [Threading](#threading)
3. [asyncio and Coroutines](#asyncio-and-coroutines)
4. [Multiprocessing](#multiprocessing)
5. [subprocess](#subprocess)
6. [Synchronization Primitives](#synchronization-primitives)
7. [Migration and Mixing Patterns](#migration-and-mixing-patterns)

---

## Concurrency Model Selection

| Workload | Recommended approach | Why |
|----------|---------------------|-----|
| I/O-bound, moderate concurrency | `threading` + `ThreadPoolExecutor` | Simple, good for network/file I/O |
| I/O-bound, high concurrency (thousands) | `asyncio` coroutines | Lightweight, scales to 10k+ tasks |
| CPU-bound | `multiprocessing` + `ProcessPoolExecutor` | Bypasses the GIL |
| Running external programs | `subprocess` | Safe, flexible child process management |
| Mixed I/O and CPU | Combine `asyncio` with `ProcessPoolExecutor` | Best of both worlds |

### The GIL (Global Interpreter Lock)

CPython's GIL prevents multiple threads from executing Python bytecode simultaneously:
- Threads do **not** provide parallelism for CPU-bound work
- Threads *are* useful for I/O-bound work — GIL is released during I/O
- For true CPU parallelism, use `multiprocessing` or C extensions

---

## Threading

### Basic thread usage

```python
from threading import Thread

def worker(name):
    print(f"Worker {name} starting")
    do_io_work()
    print(f"Worker {name} done")

threads = [Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### ThreadPoolExecutor (preferred)

Manages a reusable thread pool — prefer over manual thread creation:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_url(url):
    return requests.get(url).text

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_url, url): url for url in urls}
    for future in as_completed(futures):
        url = futures[future]
        try:
            data = future.result()
        except Exception as e:
            print(f"{url} failed: {e}")
```

### Thread safety

Threads share memory. Protect shared mutable state:

```python
from threading import Lock

class Counter:
    def __init__(self):
        self.count = 0
        self._lock = Lock()

    def increment(self):
        with self._lock:
            self.count += 1
```

Even `count += 1` is not atomic — always use a `Lock` when multiple threads modify shared data.

### Queue for thread coordination

```python
from queue import Queue

def producer(q):
    for item in generate_items():
        q.put(item)
    q.put(None)  # Sentinel to signal done

def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        process(item)
        q.task_done()
```

`Queue` handles all synchronization internally — safest way to pass data between threads.

---

## asyncio and Coroutines

### Basics

```python
import asyncio

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def main():
    results = await asyncio.gather(
        fetch_data("https://api.example.com/1"),
        fetch_data("https://api.example.com/2"),
        fetch_data("https://api.example.com/3"),
    )
    return results

asyncio.run(main())
```

### Key concepts

- `async def` defines a **coroutine function** — calling it returns a coroutine object
- `await` suspends the coroutine until the awaited task completes
- `asyncio.gather()` runs multiple coroutines concurrently
- `asyncio.create_task()` schedules a coroutine to run in the background

### Fan-out / fan-in

```python
async def process_batch(items):
    tasks = [asyncio.create_task(process_item(item)) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### Async context managers and iterators

```python
async with aiofiles.open("data.txt") as f:
    async for line in f:
        process(line)
```

### Avoid blocking the event loop

Never call blocking I/O from a coroutine. Offload sync libraries to a thread:

```python
import asyncio

# Python 3.9+ (preferred)
async def main():
    result = await asyncio.to_thread(blocking_function, arg)

# Older alternative — use get_running_loop(), not get_event_loop()
async def main():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, blocking_function, arg)
```

Use `asyncio.run(main(), debug=True)` during development to detect slow coroutines.

---

## Multiprocessing

### ProcessPoolExecutor (preferred)

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(n):
    return sum(i * i for i in range(n))

with ProcessPoolExecutor() as executor:
    results = list(executor.map(cpu_heavy, [10**6, 10**7, 10**8]))
```

### Key differences from threading

- Each process has its own interpreter and GIL → true parallelism
- Data must be pickled between processes → higher overhead
- Shared state requires special objects (`multiprocessing.Value`, `Queue`, `Manager`)
- Process creation is more expensive than thread creation

### When to use multiprocessing

- CPU-bound work taking more than a few seconds per task
- Work cleanly partitioned into independent chunks
- Avoid for I/O-bound work (use threads or asyncio instead)

---

## subprocess

Run external programs:

```python
import subprocess

# Simple — run and capture output
result = subprocess.run(
    ["ls", "-la"],
    capture_output=True,
    text=True,
    timeout=30,
)
print(result.stdout)

# Advanced — streaming / pipelines
with subprocess.Popen(
    ["grep", "error"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
) as proc:
    stdout, stderr = proc.communicate(input=log_data, timeout=10)
```

Always use `timeout` to prevent hanging processes.

---

## Synchronization Primitives

### Lock (Mutex)

Ensures mutual exclusion — one thread at a time:

```python
from threading import Lock
lock = Lock()
with lock:
    # Critical section
    shared_resource.modify()
```

### Semaphore

Allows a fixed number of concurrent accesses:

```python
from threading import Semaphore
sem = Semaphore(3)  # Allow 3 concurrent accesses
with sem:
    access_limited_resource()
```

### Condition

For producer-consumer patterns w/ thread coordination:

```python
from threading import Condition
condition = Condition()

# Producer
with condition:
    buffer.append(item)
    condition.notify()

# Consumer
with condition:
    while not buffer:
        condition.wait()
    item = buffer.pop(0)
```

### Event

Simple flag for thread signaling:

```python
from threading import Event
ready = Event()

# Waiting thread
ready.wait()  # Blocks until set

# Signaling thread
ready.set()   # Unblocks all waiters
```

---

## Migration and Mixing Patterns

### Top-down migration (sync → async)

Use `asyncio.to_thread` (3.9+) or `run_in_executor` to call sync code from async context:

```python
# Python 3.9+ (preferred)
async def async_wrapper():
    result = await asyncio.to_thread(sync_function, arg1, arg2)
    return result

# Older alternative
async def async_wrapper():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,  # Default ThreadPoolExecutor
        sync_function,
        arg1, arg2,
    )
    return result
```

### Bottom-up migration (introducing async gradually)

Use `asyncio.run()` from sync code to call async functions:

```python
def sync_function():
    result = asyncio.run(async_function())
    return result
```

### Combining asyncio with multiprocessing

For mixed I/O and CPU workloads:

```python
async def main():
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_heavy_function, data)
```

### General advice

- Start w/ the simplest concurrency model that works
- Prefer `ThreadPoolExecutor` / `ProcessPoolExecutor` over raw threads/processes
- Use `Queue` (threading) or `asyncio.Queue` for coordination
- Always protect shared mutable state w/ locks
- Test concurrent code thoroughly — race conditions are intermittent and hard to reproduce
