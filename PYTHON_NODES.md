# Python Nodes in Radler

## Overview

Radler now supports Python nodes in addition to C and C++ nodes. Python nodes allow you to write ROS2 nodes using Python while maintaining the same step function interface and semantics as C/C++ nodes.

## Features

- **Same Step Function API**: Python step functions have the same signature and behavior as C++ step functions
- **Automatic Code Generation**: Radler generates the ROS2 Python node wrapper automatically
- **Flag Support**: Full support for radl_flags (stale, timeout) just like C++ nodes
- **Type Safety**: Input/output structures are generated with proper ROS2 message types

## Defining a Python Node in RADL

To define a Python node, use the `PYTHON` keyword in your RADL file:

```radl
my_node : node {
    PUBLISHES
        output { TOPIC my_topic }
    SUBSCRIBES
        input { TOPIC other_topic MAXLATENCY 100msec }
    PERIOD 500msec
    PYTHON { 
        FILENAME "my_node.py"
        MODULE "my_node"
        CLASS "MyNode"
        STEP_METHOD "step"  # Optional, defaults to "step"
    }
}
```

### PYTHON Field Parameters

- **FILENAME** (required): The Python source file containing your node class
- **MODULE** (required): The Python module name (usually the filename without .py)
- **CLASS** (required): The name of the Python class to instantiate
- **STEP_METHOD** (optional): The name of the step method (defaults to "step")
- **PATH** (optional): Subdirectory path relative to user_src (defaults to ".")

## Writing a Python Step Function

Your Python node class must have a constructor and a step method with the following signature:

```python
class MyNode:
    def __init__(self):
        """Initialize your node state"""
        self.counter = 0
        # Initialize any state variables here
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically
        
        Args:
            radl_in: Input structure with subscription data
            radl_in_flags: Input flags for subscriptions
            radl_out: Output structure for publication data
            radl_out_flags: Output flags for publications
        """
        # Your step logic here
        pass
```

### Input Structure (radl_in)

The `radl_in` object has attributes for each subscription defined in your RADL node:

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # Access subscription data
    if radl_in.my_subscription is not None:
        value = radl_in.my_subscription.field_name
```

### Input Flags (radl_in_flags)

The `radl_in_flags` object provides flag values for each subscription. Use the helper functions to check flags:

```python
# Flag constants (available in generated node)
RADL_STALE_VALUE = 1
RADL_STALE_MBOX = 2
RADL_STALE = 3
RADL_TIMEOUT_VALUE = 16
RADL_TIMEOUT_MBOX = 32
RADL_TIMEOUT = 48

def radl_is_stale(flags):
    """Check if the stale flag is set"""
    return (flags & RADL_STALE) != 0

def radl_is_timeout(flags):
    """Check if the timeout flag is set"""
    return (flags & RADL_TIMEOUT) != 0

# Use in step function:
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    if not radl_is_stale(radl_in_flags.my_sub) and not radl_is_timeout(radl_in_flags.my_sub):
        # Data is fresh and valid
        process_data(radl_in.my_sub)
```

### Output Structure (radl_out)

The `radl_out` object has attributes for each publication. Set the message fields directly:

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # Set publication data
    radl_out.my_publication.field1 = 42
    radl_out.my_publication.field2 = "hello"
```

### Output Flags (radl_out_flags)

The `radl_out_flags` object allows you to set flags for publications (advanced usage):

```python
def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
    # Optionally set output flags
    radl_out_flags.my_publication = RADL_STALE_VALUE  # Mark as stale
```

## Example: Talker Node

```python
# talker.py
class Talker:
    """Talker node that publishes incrementing counter values"""
    
    def __init__(self):
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        radl_out.chatter.data = self.counter
        self.counter += 1
        print(f"Sent {radl_out.chatter.data}")
```

## Example: Listener Node

```python
# listener.py
RADL_STALE = 3
RADL_TIMEOUT = 48

def radl_is_stale(flags):
    return (flags & RADL_STALE) != 0

def radl_is_timeout(flags):
    return (flags & RADL_TIMEOUT) != 0

class Listener:
    """Listener node that receives and prints counter values"""
    
    def __init__(self):
        pass
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        if not radl_is_stale(radl_in_flags.chatter) and not radl_is_timeout(radl_in_flags.chatter):
            if radl_in.chatter is not None:
                print(f"Received {radl_in.chatter.data}")
```

## Complete RADL Example

See `examples/pubsub/single_machine/pubsub_python.radl` for a complete example:

```radl
settings : module_settings {
    MODULE_BASE_PATH "src"
}

basic_rate : duration 500msec

chatter_data : topic {
    FIELDS
        data : int64 0
}

talker : node {
    PUBLISHES
        chatter { TOPIC chatter_data }
    PERIOD basic_rate
    PYTHON { FILENAME "talker.py" MODULE "talker" CLASS "Talker" }
}

listener : node {
    SUBSCRIBES
        chatter { TOPIC chatter_data MAXLATENCY 100msec }
    PERIOD basic_rate
    PYTHON { FILENAME "listener.py" MODULE "listener" CLASS "Listener" }
}

sys1 : linux {
  NODES_UID 1000
  IMG "linux.img"
  IP 192.168.10.201
  NODES
   talker listener 
}

plant : plant {
  MACHINES
    host_computer { OS sys1 }
}
```

## How It Works

1. **RADL Parsing**: Radler parses your RADL file and recognizes `PYTHON` node definitions
2. **Code Generation**: Radler generates a Python ROS2 node wrapper (`radl__<nodename>.py`)
3. **Node Wrapper**: The generated wrapper:
   - Imports your Python class
   - Creates ROS2 publishers and subscribers
   - Manages input/output structures
   - Calls your step function periodically
   - Handles flag management automatically
4. **Execution**: Run the generated Python script directly or via a launch file

## Advantages of Python Nodes

- **Easier Development**: Python is often easier and faster to write than C++
- **No Compilation**: Python nodes don't require compilation, speeding up development
- **Rich Libraries**: Access to Python's extensive ecosystem
- **Same Semantics**: Maintains the same deterministic, periodic execution model as C++ nodes

## Mixing C++ and Python Nodes

You can freely mix C++ and Python nodes in the same RADL application. They communicate through ROS2 topics just like any other nodes:

```radl
cpp_node : node {
    PUBLISHES
        data { TOPIC shared_topic }
    PERIOD 100msec
    CXX { HEADER "cpp_node.h" FILENAME "cpp_node.cpp" CLASS "CppNode" }
}

python_node : node {
    SUBSCRIBES
        data { TOPIC shared_topic MAXLATENCY 50msec }
    PERIOD 100msec
    PYTHON { FILENAME "python_node.py" MODULE "python_node" CLASS "PythonNode" }
}
```

## Implementation Details

The Python node generator:
- Creates proper ROS2 Python nodes using `rclpy`
- Manages message passing through mailbox pattern (same as C++)
- Implements flag checking for stale and timeout conditions
- Generates callback functions for subscriptions
- Creates periodic timers for step function execution
- Maintains the same deterministic behavior as C++ nodes

## Comparison with C++ Nodes

| Feature | C++ Nodes | Python Nodes |
|---------|-----------|--------------|
| Step Function API | ✓ Same | ✓ Same |
| Flag Support | ✓ Yes | ✓ Yes |
| Compilation | Required | Not Required |
| Performance | Faster | Slightly Slower |
| Development Speed | Moderate | Fast |
| ROS2 Integration | Native | Through rclpy |
| Ecosystem | C++ libraries | Python libraries |

## Best Practices

1. **Keep State in __init__**: Initialize all state variables in the constructor
2. **Check Flags**: Always check flags before using subscription data
3. **Set All Fields**: Make sure to set all required fields in publications
4. **Avoid Blocking**: Don't use blocking calls in the step function
5. **Use Print Sparingly**: Excessive printing can affect timing
6. **Test Incrementally**: Start with simple step functions and add complexity gradually

## Troubleshooting

### "Module not found" Error
- Check that FILENAME matches your Python file name
- Verify MODULE matches the file name without .py
- Ensure PATH is correct if using subdirectories

### Step Function Not Called
- Verify CLASS name matches your Python class
- Check that __init__ method exists
- Ensure step method has correct signature

### Import Errors
- Generated node includes automatic imports for ROS2 message types
- Make sure ROS2 packages for message types are installed
- Check that your Python environment has rclpy installed

## Future Enhancements

Potential future additions:
- Support for Python-specific features (async/await)
- Better error handling and debugging
- Performance profiling tools
- Integration with Python testing frameworks

