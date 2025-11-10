# SimPy Core Concepts (From Official Documentation)

This document summarizes key SimPy concepts from the official documentation to ensure correct implementation.

---

## 1. Fundamental Architecture

**SimPy is a discrete-event simulation library** where:
- Simulation components are modeled as **processes**
- Processes exist within an **environment**
- Processes interact via **events**

```python
import simpy

env = simpy.Environment()  # Create simulation environment
# ... add processes ...
env.run(until=100)  # Run simulation until time 100
```

---

## 2. Processes

### Definition
- Implemented as **Python generator functions** (or generator methods)
- Describe behavior of active simulation components
- Can create and **yield events**
- Get **suspended** when yielding an event
- **Resumed** when the event occurs

### Example
```python
def car(env):
    """Process representing a car"""
    while True:
        print(f'Start parking at {env.now}')
        yield env.timeout(5)  # Park for 5 time units

        print(f'Start driving at {env.now}')
        yield env.timeout(2)  # Drive for 2 time units

env = simpy.Environment()
env.process(car(env))  # Start the car process
env.run(until=15)
```

### Key Points
- Generator functions control process behavior
- `yield` statements **pause and resume** process execution
- Infinite loops can model **continuous behaviors**
- Processes are **resumed in order** of event yielding

---

## 3. Events

### Core Mechanism
- Events control simulation flow
- Processes can **wait for events** to occur
- **Multiple processes** can wait for the same event
- Events determine when processes continue

### Timeout Event
- **Most common event type**
- Represents **time passage** in simulated environment
- `yield env.timeout(duration)` - wait for specified time

```python
def process(env):
    yield env.timeout(5)  # Wait 5 time units
    print(f'Event occurred at {env.now}')
```

### Process as Event
- **A process can yield another process**
- Waits for that process to complete
- Enables process synchronization

```python
def sub_process(env):
    yield env.timeout(3)
    return "Done"

def main_process(env):
    result = yield env.process(sub_process(env))  # Wait for sub_process
    print(f'Got result: {result}')
```

---

## 4. Environment

### Purpose
- Tracks **simulation time** via `env.now`
- Manages event scheduling
- Coordinates process execution

### Methods
- `env.process(generator)` - Start a new process
- `env.run(until=time)` - Run simulation until specified time
- `env.now` - Current simulation time (read-only)

### Environment Types
- `simpy.Environment()` - Standard discrete-event simulation
- `simpy.RealtimeEnvironment()` - Real-time simulation (for visualization)

---

## 5. Process Interaction

### Waiting for Processes
```python
def worker(env, name, duration):
    yield env.timeout(duration)
    return f'{name} done'

def supervisor(env):
    # Wait for worker to finish
    result = yield env.process(worker(env, 'Worker-1', 5))
    print(result)
```

### Interrupting Processes
```python
def chargeable_process(env):
    while True:
        try:
            print('Start charging...')
            yield env.timeout(duration)
            print('Charging complete')
        except simpy.Interrupt:
            print('Was interrupted! Aborting...')
```

Interrupt from another process:
```python
def interruptor(env, process_to_interrupt):
    yield env.timeout(3)
    process_to_interrupt.interrupt()
```

---

## 6. Shared Resources

### Resource Types
SimPy offers three types of resources:
1. **Resource** - Basic resource with capacity
2. **PriorityResource** - Processes with higher priority get resource first
3. **PreemptiveResource** - Can preempt lower-priority processes

### Basic Resource Usage

**Create resource:**
```python
bcs = simpy.Resource(env, capacity=2)  # 2 charging spots
```

**Request and release:**
```python
def car(env, name, bcs):
    print(f'{name} arriving at {env.now}')

    # Request resource (wait if not available)
    with bcs.request() as req:
        yield req  # Wait until resource available

        print(f'{name} starting to charge at {env.now}')
        yield env.timeout(5)  # Use resource for 5 time units
        print(f'{name} leaving at {env.now}')

    # Resource automatically released when exiting 'with' block
```

### Key Resource Characteristics
- Manages **limited capacity** scenarios
- Processes **wait** if all slots occupied
- **Automatic queuing** (FIFO by default)
- **Automatic release** with `with` statement
- Supports **concurrent access** up to defined capacity

---

## 7. Common Patterns

### Pattern 1: Continuous Process Loop
```python
def machine(env):
    """Machine that produces items continuously"""
    while True:
        print(f'[{env.now}] Start producing')
        yield env.timeout(2)  # Production takes 2 time units
        print(f'[{env.now}] Item produced')
```

### Pattern 2: Resource Request with Timeout
```python
def process_with_timeout(env, resource):
    with resource.request() as req:
        # Wait for resource or timeout
        result = yield req | env.timeout(10)

        if req in result:
            print('Got resource')
            yield env.timeout(5)  # Use resource
        else:
            print('Timed out waiting for resource')
```

### Pattern 3: Process Communication
```python
def producer(env, store):
    """Produce items and put in store"""
    for i in range(5):
        yield env.timeout(2)
        yield store.put(f'item-{i}')
        print(f'Produced item-{i}')

def consumer(env, store):
    """Get items from store"""
    while True:
        item = yield store.get()
        print(f'Consumed {item}')
        yield env.timeout(3)
```

---

## 8. Important Notes for Implementation

### Generator Functions
- MUST use `yield` to create events
- Cannot use `return` with value in Python < 3.3 (use `env.exit(value)`)
- Can use `return value` in Python >= 3.3

### Time
- Simulation time is **unitless** (you define what it represents)
- Time only advances via events (`timeout`, `process`, etc.)
- `env.now` is **read-only**

### Order of Execution
- Events scheduled for same time are processed in order they were created
- Processes resumed in order they yielded events

### Common Mistakes
- ❌ Forgetting to `yield` events
- ❌ Using `time.sleep()` instead of `env.timeout()`
- ❌ Modifying `env.now` directly
- ❌ Not using `with` statement for resources (causing resource leaks)

---

## 9. Zurvan-SimPy Mapping

| Zurvan Concept | SimPy Implementation |
|----------------|---------------------|
| **Resource Node** | Python object with `env` attribute |
| **Action (Atomic)** | Generator function with `yield env.timeout()` |
| **Action (Composite)** | Generator function calling `yield env.process()` |
| **Temporal Layer** | SimPy Environment + event scheduling |
| **Resource Constraint** | SimPy Resource with capacity |
| **State** | Object attributes (e.g., `node.state['inventory']`) |
| **Scenario** | Simulation class wrapping env + processes |

---

## 10. Example: Manufacturing Center (Zurvan Pattern)

```python
import simpy

class ManufacturingCenter:
    """Zurvan ResourceNode with SimPy"""
    def __init__(self, env, node_id):
        self.env = env
        self.node_id = node_id
        self.state = {
            'inventory': 0,
            'production_rate': 0
        }

    def continuous_production(self):
        """Atomic action: produce items continuously"""
        while True:
            if self.state['production_rate'] > 0:
                # Wait based on production rate
                yield self.env.timeout(1.0 / self.state['production_rate'])
                self.state['inventory'] += 1
                print(f"[{self.env.now:.2f}] {self.node_id}: Produced 1 unit (inventory={self.state['inventory']})")
            else:
                # Idle - check again in 1 time unit
                yield self.env.timeout(1.0)

# Usage
env = simpy.Environment()
center = ManufacturingCenter(env, 'chicago_center')
center.state['production_rate'] = 10  # 10 units/hour

env.process(center.continuous_production())
env.run(until=5)  # Run for 5 time units
```

---

## 11. Verification Checklist

Before implementing, ensure:
- [ ] Processes are generator functions using `yield`
- [ ] Events are yielded (not just created)
- [ ] Resources use `with` statement for automatic release
- [ ] Time advances via `env.timeout()` not `time.sleep()`
- [ ] Simulation time accessed via `env.now` (read-only)
- [ ] Environment passed to all processes
- [ ] Processes started with `env.process()`
- [ ] Simulation run with `env.run()`

---

## References

- [SimPy Basic Concepts](https://simpy.readthedocs.io/en/latest/simpy_intro/basic_concepts.html)
- [SimPy Process Interaction](https://simpy.readthedocs.io/en/latest/simpy_intro/process_interaction.html)
- [SimPy Shared Resources](https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html)
