#!/usr/bin/env python3
"""
Listener node - Python implementation
This is the Python version of the C++ Listener class
"""

# Note: In the generated node, radl_is_stale and radl_is_timeout will be 
# available in the global scope. You can also import them from radl_python_lib
# if you want to use them elsewhere.


class Listener:
    """Listener node that receives and prints counter values"""
    
    def __init__(self):
        """Initialize the listener"""
        pass
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically by the ROS2 node
        
        Args:
            radl_in: Input structure with subscriptions
            radl_in_flags: Input flags for subscriptions
            radl_out: Output structure with publications (not used by listener)
            radl_out_flags: Output flags for publications (not used by listener)
            
        Note: radl_is_stale() and radl_is_timeout() are available in the
        generated node code automatically.
        """
        # The generated code provides these helper functions:
        # - radl_is_stale(flags): Check if stale flag is set
        # - radl_is_timeout(flags): Check if timeout flag is set
        # These are imported in the generated wrapper, so we reference them here
        
        # For this simple example, we'll do inline flag checking
        # In production code, you might want to import from radl_python_lib
        RADL_STALE = 3
        RADL_TIMEOUT = 48
        
        # Check if we have valid data
        if not (radl_in_flags.chatter & RADL_STALE) and not (radl_in_flags.chatter & RADL_TIMEOUT):
            if radl_in.chatter is not None:
                print(f"Received {radl_in.chatter.data}")

