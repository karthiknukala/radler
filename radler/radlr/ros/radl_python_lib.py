"""
Radler Python Library

This module provides helper functions and constants for Radler Python nodes.
These functions match the C++ radl_flags.h interface.
"""

# Flag constants (matching radl_flags.h)
RADL_STALE_VALUE = 1
RADL_STALE_MBOX = 2
RADL_STALE = 3
RADL_OPERATIONAL_1 = 4
RADL_OPERATIONAL_2 = 8
RADL_OPERATIONAL_FLAGS = 15

RADL_TIMEOUT_VALUE = 16
RADL_TIMEOUT_MBOX = 32
RADL_TIMEOUT = 48
RADL_FAILURE_1 = 64
RADL_FAILURE_2 = 128
RADL_FAILURE_FLAGS = ~RADL_OPERATIONAL_FLAGS & 0xFF

RADL_MBOX_FLAGS = RADL_STALE_MBOX | RADL_TIMEOUT_MBOX
RADL_VALUE_FLAGS = RADL_STALE_VALUE | RADL_TIMEOUT_VALUE


def radl_is_stale(flags):
    """
    Check if the stale flag is set.
    
    Args:
        flags: radl_flags_t value
        
    Returns:
        True if stale flag is set, False otherwise
    """
    return (flags & RADL_STALE) != 0


def radl_is_timeout(flags):
    """
    Check if the timeout flag is set.
    
    Args:
        flags: radl_flags_t value
        
    Returns:
        True if timeout flag is set, False otherwise
    """
    return (flags & RADL_TIMEOUT) != 0


def radl_is_operational(flags):
    """
    Check if only operational flags are set (no failure flags).
    
    Args:
        flags: radl_flags_t value
        
    Returns:
        True if operational, False if any failure flag is set
    """
    return (flags & RADL_FAILURE_FLAGS) == 0


def radl_has_failure(flags):
    """
    Check if any failure flag is set.
    
    Args:
        flags: radl_flags_t value
        
    Returns:
        True if any failure flag is set, False otherwise
    """
    return (flags & RADL_FAILURE_FLAGS) != 0


def radl_is_fresh(flags):
    """
    Check if data is fresh (not stale and not timeout).
    
    Args:
        flags: radl_flags_t value
        
    Returns:
        True if data is fresh, False otherwise
    """
    return not radl_is_stale(flags) and not radl_is_timeout(flags)


# Base class for Radler nodes (optional, but provides better structure)
class RadlerNode:
    """
    Base class for Radler Python nodes.
    
    Users can inherit from this class to get type hints and structure,
    but it's not required - any class with a step method will work.
    """
    
    def __init__(self):
        """Initialize the node. Override this in your subclass."""
        pass
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically.
        
        Override this in your subclass to implement node behavior.
        
        Args:
            radl_in: Input structure with subscription data
            radl_in_flags: Input flags for subscriptions
            radl_out: Output structure for publication data
            radl_out_flags: Output flags for publications
        """
        raise NotImplementedError("step() must be implemented in subclass")

