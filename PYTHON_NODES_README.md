# Python Nodes for Radler - Implementation Complete ✓

## What Was Implemented

Radler now fully supports Python nodes with the same step function interface as C++ nodes. Users can write ROS2 nodes in Python without dealing with C++ compilation, while maintaining the same deterministic, periodic execution semantics.

## Quick Example

### Python Node (talker.py)
```python
class Talker:
    def __init__(self):
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        radl_out.chatter.data = self.counter
        self.counter += 1
```

### RADL Definition (pubsub.radl)
```radl
talker : node {
    PUBLISHES
        chatter { TOPIC chatter_data }
    PERIOD 500msec
    PYTHON { FILENAME "talker.py" MODULE "talker" CLASS "Talker" }
}
```

That's it! Radler generates a complete ROS2 Python node automatically.

## Documentation

Three documentation files have been created:

1. **[PYTHON_QUICK_START.md](PYTHON_QUICK_START.md)** - 5-minute introduction with examples
2. **[PYTHON_NODES.md](PYTHON_NODES.md)** - Comprehensive user guide (30+ pages)
3. **[PYTHON_IMPLEMENTATION_SUMMARY.md](PYTHON_IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

## Examples

Working examples are available in `examples/pubsub/single_machine/`:

- **talker.py** - Python publisher node
- **listener.py** - Python subscriber node with flag checking
- **pubsub_python.radl** - RADL file defining Python nodes

These demonstrate the exact same functionality as the C++ examples but in pure Python.

## Core Components

### 1. Language Support (radler/radlr/language.py)
- Added `python_class` definition
- Added `PYTHON` field to node class
- Enables RADL syntax: `PYTHON { FILENAME "x.py" MODULE "x" CLASS "X" }`

### 2. Code Generator (radler/radlr/ros/rosnodepy.py) - NEW
- Generates complete ROS2 Python nodes
- Creates input/output data structures
- Manages publishers and subscribers
- Handles flag computation automatically
- Calls user's step function periodically

### 3. Helper Library (radler/radlr/ros/radl_python_lib.py) - NEW
- Flag constants (RADL_STALE, RADL_TIMEOUT, etc.)
- Flag checking functions (radl_is_stale, radl_is_timeout, etc.)
- Optional RadlerNode base class

### 4. Build Integration (radler/radlr/ros/roscmake.py)
- Detects Python nodes
- Skips C++ compilation for Python nodes
- Generates Python scripts instead

### 5. User Sources (radler/radlr/gen_utils/user_sources.py)
- Recognizes PYTHON source type
- Handles Python nodes in code generation pipeline

## Features

✓ **Same API as C++** - Step function signature matches exactly  
✓ **Automatic Code Generation** - Full ROS2 wrapper generated  
✓ **Flag Support** - Complete flag semantics (stale, timeout)  
✓ **Message Types** - Automatic import of ROS2 messages  
✓ **No Compilation** - Pure Python, no build step  
✓ **Mixed Systems** - C++ and Python nodes work together  
✓ **State Management** - Maintain state in `__init__`  
✓ **ROS2 Integration** - Uses rclpy for native ROS2 support  

## API Overview

### Step Function Signature
```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # radl_in: Access subscription data
    # radl_in_flags: Check data validity (stale, timeout)
    # radl_out: Set publication data
    # radl_out_flags: Set publication flags (optional)
```

### Reading Subscriptions
```python
if radl_in.my_subscription is not None:
    value = radl_in.my_subscription.field_name
```

### Writing Publications
```python
radl_out.my_publication.field_name = value
```

### Checking Flags
```python
RADL_STALE = 3
RADL_TIMEOUT = 48

if not (radl_in_flags.my_sub & RADL_STALE) and \
   not (radl_in_flags.my_sub & RADL_TIMEOUT):
    # Data is fresh and valid
    process(radl_in.my_sub)
```

## File Structure

```
kn-radler/
├── radler/radlr/
│   ├── language.py              [MODIFIED] Language grammar
│   ├── gen_utils/
│   │   └── user_sources.py      [MODIFIED] Source type handling
│   └── ros/
│       ├── roscmake.py           [MODIFIED] Build integration
│       ├── rosnodepy.py          [NEW] Python node generator
│       └── radl_python_lib.py    [NEW] Helper library
├── examples/pubsub/single_machine/src/
│   ├── talker.py                 [NEW] Example publisher
│   └── listener.py               [NEW] Example subscriber
├── examples/pubsub/single_machine/
│   └── pubsub_python.radl        [NEW] Example RADL file
├── PYTHON_NODES.md               [NEW] User documentation
├── PYTHON_QUICK_START.md         [NEW] Quick start guide
├── PYTHON_IMPLEMENTATION_SUMMARY.md [NEW] Technical details
└── PYTHON_NODES_README.md        [THIS FILE] Overview
```

## How It Works

1. **Parse**: Radler parses RADL file with `PYTHON { ... }` definition
2. **Generate**: Radler generates Python ROS2 node wrapper
3. **Import**: Generated code imports your Python class
4. **Execute**: ROS2 runs Python script directly (no compilation)

The generated Python node:
- Imports ROS2 dependencies (rclpy, messages)
- Imports your Python class
- Creates input/output structures
- Sets up publishers and subscribers
- Calls your step function periodically
- Manages flags automatically

## Advantages

**vs C++ Nodes:**
- Faster development (no compilation)
- Easier to write and test
- Access to Python ecosystem
- Better for rapid prototyping

**vs Pure ROS2 Python:**
- Deterministic periodic execution
- Automatic flag management
- Structured input/output
- Consistent with C++ nodes

## Use Cases

**Use Python for:**
- Rapid prototyping
- Complex algorithms
- Integration with ML/AI libraries
- Less time-critical nodes
- High-level coordination
- Data processing

**Use C++ for:**
- Hard real-time requirements
- High-frequency control (>1kHz)
- Performance-critical paths
- Low-level hardware interfaces

## Testing

```python
# Unit test your Python class directly
from talker import Talker

class MockOut:
    def __init__(self):
        self.chatter = type('obj', (object,), {'data': 0})

t = Talker()
out = MockOut()
t.step(None, None, out, None)
assert out.chatter.data == 0
```

## Compatibility

- **ROS2**: Requires rclpy (standard ROS2 Python)
- **Python**: Python 3.8+ recommended
- **Radler**: Fully integrated with existing infrastructure
- **C++ Nodes**: Complete interoperability

## Next Steps

1. Read [PYTHON_QUICK_START.md](PYTHON_QUICK_START.md) for a 5-minute intro
2. Review [examples/pubsub/single_machine/pubsub_python.radl](examples/pubsub/single_machine/pubsub_python.radl)
3. Try modifying the examples
4. Write your own Python nodes
5. Consult [PYTHON_NODES.md](PYTHON_NODES.md) for detailed documentation

## Summary

Python node support is fully implemented and ready to use. Users can now write Radler nodes in Python with the same step function interface as C++, enabling faster development while maintaining deterministic execution semantics. The implementation includes comprehensive documentation, working examples, and a helper library for common operations.

**Key Achievement:** Python nodes provide the exact same step function API and semantics as C++ nodes, just without the compilation overhead.

---

*Implementation completed November 2025*

