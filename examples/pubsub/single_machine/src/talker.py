#!/usr/bin/env python3
"""
Talker node - Python implementation
This is the Python version of the C++ Talker class
"""


class Talker:
    """Talker node that publishes incrementing counter values"""
    
    def __init__(self):
        """Initialize the talker with a counter"""
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically by the ROS2 node
        
        Args:
            radl_in: Input structure with subscriptions (not used by talker)
            radl_in_flags: Input flags for subscriptions (not used by talker)
            radl_out: Output structure with publications
            radl_out_flags: Output flags for publications
        """
        # Set the output data
        radl_out.chatter.data = self.counter
        self.counter += 1
        
        # Print for debugging
        print(f"Sent {radl_out.chatter.data}")

