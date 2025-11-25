# Python Nodes Quick Start Guide

## 5-Minute Introduction to Radler Python Nodes

### Step 1: Write Your Python Class

Create a Python file (e.g., `my_node.py`) in your `user_src` directory:

```python
class MyNode:
    def __init__(self):
        self.count = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        # Your node logic here
        radl_out.my_output.value = self.count
        self.count += 1
```

### Step 2: Define in RADL

Add to your `.radl` file:

```radl
my_topic : topic {
    FIELDS
        value : int64 0
}

my_node : node {
    PUBLISHES
        my_output { TOPIC my_topic }
    PERIOD 100msec
    PYTHON { 
        FILENAME "my_node.py" 
        MODULE "my_node" 
        CLASS "MyNode" 
    }
}
```

### Step 3: Run Radler

```bash
./radler.sh compile your_file.radl
```

That's it! Radler generates a complete ROS2 Python node.

## Complete Pub/Sub Example

### Publisher (talker.py)

```python
class Talker:
    def __init__(self):
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        radl_out.chatter.data = self.counter
        self.counter += 1
        print(f"Sent {self.counter}")
```

### Subscriber (listener.py)

```python
class Listener:
    def __init__(self):
        pass
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        # Check for valid data
        RADL_STALE = 3
        RADL_TIMEOUT = 48
        
        if radl_in.chatter is not None:
            flags = radl_in_flags.chatter
            if not (flags & RADL_STALE) and not (flags & RADL_TIMEOUT):
                print(f"Received {radl_in.chatter.data}")
```

### RADL Definition

```radl
settings : module_settings {
    MODULE_BASE_PATH "src"
}

chatter_data : topic {
    FIELDS
        data : int64 0
}

talker : node {
    PUBLISHES
        chatter { TOPIC chatter_data }
    PERIOD 500msec
    PYTHON { FILENAME "talker.py" MODULE "talker" CLASS "Talker" }
}

listener : node {
    SUBSCRIBES
        chatter { TOPIC chatter_data MAXLATENCY 100msec }
    PERIOD 500msec
    PYTHON { FILENAME "listener.py" MODULE "listener" CLASS "Listener" }
}

sys1 : linux {
  NODES_UID 1000
  NODES talker listener 
}

plant : plant {
  MACHINES
    machine1 { OS sys1 }
}
```

## Common Patterns

### Reading Subscriptions

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # Check if data is valid
    if radl_in.my_subscription is not None:
        # Access message fields
        value = radl_in.my_subscription.field_name
```

### Writing Publications

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # Set message fields
    radl_out.my_publication.field1 = 42
    radl_out.my_publication.field2 = "hello"
```

### Checking Flags

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    RADL_STALE = 3
    RADL_TIMEOUT = 48
    
    flags = radl_in_flags.my_subscription
    if not (flags & RADL_STALE) and not (flags & RADL_TIMEOUT):
        # Data is fresh and valid
        process_data(radl_in.my_subscription)
```

### Maintaining State

```python
class StatefulNode:
    def __init__(self):
        # Initialize state in constructor
        self.history = []
        self.max_value = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        # Use state in step function
        if radl_in.data is not None:
            value = radl_in.data.value
            self.history.append(value)
            self.max_value = max(self.max_value, value)
            
            # Publish computed result
            radl_out.result.average = sum(self.history) / len(self.history)
            radl_out.result.maximum = self.max_value
```

## Flag Constants Reference

```python
# Operational flags
RADL_STALE_VALUE = 1       # Value was marked stale by publisher
RADL_STALE_MBOX = 2        # No new value received (mailbox stale)
RADL_STALE = 3             # Either stale condition

# Failure flags
RADL_TIMEOUT_VALUE = 16    # Value was marked timeout by publisher
RADL_TIMEOUT_MBOX = 32     # Expected value not received in time
RADL_TIMEOUT = 48          # Either timeout condition
```

## Comparison: C++ vs Python

### C++ Node
```cpp
// talker.h
class Talker {
  private:
    int counter;
  public:
    Talker();
    void step(const radl_in_t*, const radl_in_flags_t*, 
              radl_out_t*, radl_out_flags_t*);
};

// talker.cpp
#include "talker.h"
Talker::Talker() { this->counter = 0; }
void Talker::step(const radl_in_t* in, const radl_in_flags_t* inflags,
                  radl_out_t* out, radl_out_flags_t* outflags) {
    out->chatter->data = this->counter++;
}
```

### Python Node (Same Functionality)
```python
# talker.py
class Talker:
    def __init__(self):
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        radl_out.chatter.data = self.counter
        self.counter += 1
```

**Key Differences:**
- No header file needed in Python
- No pointers in Python (direct attribute access)
- No type declarations in Python
- Same step function concept
- Same semantics and behavior

## Tips

1. **File Organization**: Put Python files in the same directory structure as C++ files
2. **Naming**: Use descriptive class names that match your node purpose
3. **Testing**: Import and test your class directly in Python REPL
4. **Debugging**: Use print statements or Python debugger (pdb)
5. **Libraries**: Import any Python library you need in your file
6. **Errors**: Check generated node file if imports fail

## Next Steps

- Read [PYTHON_NODES.md](PYTHON_NODES.md) for comprehensive documentation
- See [examples/pubsub/single_machine](examples/pubsub/single_machine) for working example
- Check [PYTHON_IMPLEMENTATION_SUMMARY.md](PYTHON_IMPLEMENTATION_SUMMARY.md) for technical details

## Getting Help

If something doesn't work:

1. Check that FILENAME, MODULE, and CLASS match your Python file
2. Verify your Python file is in the correct directory (user_src)
3. Ensure your step function has the correct signature
4. Look at the generated `radl__<nodename>.py` file for errors
5. Test your Python class independently before integrating

## Example Command Flow

```bash
# 1. Create your Python node files
cd examples/pubsub/single_machine/src
# (create talker.py and listener.py)

# 2. Create RADL file
cd ..
# (create pubsub_python.radl)

# 3. Compile with Radler
cd ../../..
./radler.sh compile examples/pubsub/single_machine/pubsub_python.radl

# 4. Run the generated nodes
cd build/pubsub_python
# Run generated Python scripts directly or via launch files
```

Enjoy using Python with Radler!

