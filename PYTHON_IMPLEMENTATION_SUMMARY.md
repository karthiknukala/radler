# Python Nodes Implementation Summary

## Overview

This document summarizes the implementation of Python node support in Radler. Python nodes provide the same step function interface as C++ nodes, but without requiring compilation.

## Files Modified

### 1. `radler/radlr/language.py`
- Added `python_class` definition to the RADL language grammar
- Added `PYTHON` field to `node` class definition
- Enables parsing of `PYTHON { ... }` blocks in RADL files

### 2. `radler/radlr/gen_utils/user_sources.py`
- Updated `node_sources_type()` to recognize 'PYTHON' nodes
- Modified `user_node_class()` to return `(None, None, None)` for Python nodes
  - Python nodes don't need C++ init/step/finish code generation

### 3. `radler/radlr/ros/roscmake.py`
- Imported `gennode_python` from `rosnodepy`
- Imported `node_sources_type` from `user_sources`
- Modified `_from_node()` to detect Python nodes and call `gennode_python()`
- Python nodes skip CMake compilation steps

### 4. `radler/radlr/ros/rosnodepy.py` (NEW FILE)
- Complete Python ROS2 node generator
- Generates executable Python scripts that:
  - Import ROS2 message types
  - Import user's Python class
  - Create input/output data structures
  - Provide flag constants and helper functions
  - Set up ROS2 publishers and subscribers
  - Call user's step function periodically
  - Handle flag management automatically

### 5. `radler/radlr/ros/radl_python_lib.py` (NEW FILE)
- Optional helper library for Python nodes
- Provides flag constants matching `radl_flags.h`
- Provides flag checking functions:
  - `radl_is_stale()`
  - `radl_is_timeout()`
  - `radl_is_operational()`
  - `radl_has_failure()`
  - `radl_is_fresh()`
- Provides optional `RadlerNode` base class

## Example Files

### 6. `examples/pubsub/single_machine/src/talker.py` (NEW)
- Python implementation of Talker node
- Demonstrates publication from Python

### 7. `examples/pubsub/single_machine/src/listener.py` (NEW)
- Python implementation of Listener node
- Demonstrates subscription and flag checking in Python

### 8. `examples/pubsub/single_machine/pubsub_python.radl` (NEW)
- Example RADL file using Python nodes
- Shows complete Python node definitions

## Documentation Files

### 9. `PYTHON_NODES.md` (NEW)
- Comprehensive user documentation
- Explains Python node concepts
- Provides examples and best practices
- Includes troubleshooting guide

### 10. `PYTHON_IMPLEMENTATION_SUMMARY.md` (THIS FILE)
- Technical implementation details
- Lists all modified files
- Explains architecture and design decisions

## How It Works

### RADL Parsing
1. User writes RADL file with `PYTHON { FILENAME "x.py" MODULE "x" CLASS "X" }`
2. `language.py` grammar recognizes the `PYTHON` field
3. Parser creates AST node with Python source information

### Code Generation
1. `roscmake._from_node()` detects Python node via `node_sources_type()`
2. Calls `gennode_python()` instead of `gennode()`
3. `gennode_python()` generates executable Python script:
   - Imports ROS2 dependencies (rclpy, message types)
   - Imports user's Python class
   - Creates wrapper classes for in/out structures
   - Defines flag constants and helper functions
   - Creates ROS2 Node subclass that:
     - Instantiates user's class
     - Sets up publishers and subscribers
     - Creates periodic timer for step function
     - Manages input/output structures
     - Handles flag computation
4. Generated Python file is written to workspace

### Execution
1. Generated Python script is executable (has shebang and main())
2. Can be run directly: `./radl__nodename.py`
3. Or included in ROS2 launch files
4. No compilation required - pure Python execution

## Design Decisions

### Why Skip CMake for Python Nodes?
- Python doesn't need compilation
- CMake would add unnecessary complexity
- Python scripts can be run directly
- Simpler deployment (no build step)

### Why Generate Wrapper Code?
- Maintains consistent step function interface
- Handles ROS2 boilerplate automatically
- Manages input/output structures
- Computes flags automatically
- Users only write step logic

### Why Return None from user_node_class()?
- Python nodes don't need C++ init/step/finish code
- Returning None signals to caller to skip C++ generation
- Clean separation between C++ and Python paths

### Data Structure Approach
- Created simple Python classes for in/out/flags structures
- Attributes match RADL subscription/publication names
- Direct field access like C++ structs
- Intuitive Python API

### Flag Management
- Provided flag constants in generated code
- Included helper functions (radl_is_stale, etc.)
- Matches C++ API exactly
- Optional radl_python_lib for reusable code

## Architecture Diagram

```
RADL File (with PYTHON node)
         |
         v
    [Parser] (language.py)
         |
         v
      [AST]
         |
         v
  [roscmake._from_node()]
         |
    [detects PYTHON]
         |
         v
  [gennode_python()] (rosnodepy.py)
         |
         v
  [Generated Python Script]
    - Imports user class
    - Creates ROS2 wrapper
    - Manages step execution
         |
         v
    [Execution]
    - No compilation
    - Direct Python execution
```

## Key Features

1. **Same API as C++**: Step function signature matches exactly
2. **Automatic Generation**: Full ROS2 node wrapper generated
3. **Flag Support**: Complete flag semantics from C++
4. **Message Types**: Automatic import of ROS2 messages
5. **No Compilation**: Pure Python, no build step
6. **Easy Testing**: Can import and test step functions directly
7. **Mixed Systems**: C++ and Python nodes work together seamlessly

## Testing Strategy

To test Python nodes:

1. **Unit Testing**: Import user class directly and test step function
   ```python
   from talker import Talker
   
   # Create mock structures
   class MockRadlOut:
       def __init__(self):
           self.chatter = type('obj', (object,), {'data': 0})
   
   # Test step function
   t = Talker()
   out = MockRadlOut()
   t.step(None, None, out, None)
   assert out.chatter.data == 0
   ```

2. **Integration Testing**: Run generated node and check ROS2 topics
   ```bash
   ./radl__talker.py &
   ros2 topic echo /chatter
   ```

3. **System Testing**: Run complete RADL application with launch files

## Future Enhancements

Potential improvements:
1. Add type hints to generated code
2. Support async/await for step functions
3. Better error handling and validation
4. Performance profiling hooks
5. Debugging support
6. Hot reloading for development
7. Type checking with mypy
8. Generate stubs for better IDE support

## Compatibility

- **ROS2**: Requires rclpy (standard ROS2 Python client library)
- **Python**: Tested with Python 3.8+
- **Radler**: Compatible with existing Radler infrastructure
- **C++ Nodes**: Full interoperability with C++ nodes

## Performance Considerations

- Python nodes are slightly slower than C++ nodes
- Acceptable for most control applications
- ROS2 message passing is the bottleneck, not Python
- Consider C++ for:
  - Hard real-time requirements
  - High-frequency control loops (>1kHz)
  - Performance-critical paths
- Use Python for:
  - Rapid prototyping
  - Complex logic
  - Integration with Python libraries
  - Less time-critical nodes

## Conclusion

The Python node implementation provides a clean, Pythonic API while maintaining full compatibility with Radler's step function semantics. Users can write nodes in Python without losing any functionality compared to C++ nodes. The generated code handles all ROS2 boilerplate, allowing users to focus on implementing their node logic in the step function.

