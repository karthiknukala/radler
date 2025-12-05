#!/usr/bin/env python3
"""
Statistics Processor - Demonstrates numpy/scipy in Radler Python nodes

Receives series values and computes running statistics using numpy/scipy.
Shows how to maintain state across step calls and use scientific libraries.
"""

import numpy as np
from scipy import stats as scipy_stats


class StatsProcessor:
    """
    Processes incoming series values and computes statistics.
    
    Uses numpy for efficient array operations and scipy for statistical functions.
    Maintains a sliding window of recent values for analysis.
    """
    
    def __init__(self):
        """Initialize the statistics processor"""
        self.count = 0
        self.window_size = 100
        self.values = np.zeros(self.window_size)
        self.write_idx = 0
        self.filled = False
        
        # For tracking extremes
        self.global_max = float('-inf')
        self.global_min = float('inf')
        
        print("StatsProcessor initialized", flush=True)
        print(f"  Sliding window size: {self.window_size}", flush=True)
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Process incoming series values and compute statistics.
        
        Uses Welford's online algorithm concepts combined with
        numpy/scipy for efficient computation.
        """
        # Check if we have valid input
        if radl_in.series is None:
            return
        
        # Get the incoming value
        value = radl_in.series.value
        index = radl_in.series.index
        x_point = radl_in.series.x_point
        
        # Update sliding window
        self.values[self.write_idx] = value
        self.write_idx = (self.write_idx + 1) % self.window_size
        self.count += 1
        
        if self.count >= self.window_size:
            self.filled = True
        
        # Update global extremes
        self.global_max = max(self.global_max, value)
        self.global_min = min(self.global_min, value)
        
        # Compute statistics on the sliding window
        if self.filled:
            window = self.values
        else:
            window = self.values[:self.count]
        
        # Use numpy for basic statistics
        mean = np.mean(window)
        std_dev = np.std(window, ddof=1) if len(window) > 1 else 0.0
        
        # Publish statistics
        radl_out.stats.count = self.count
        radl_out.stats.mean = float(mean)
        radl_out.stats.std_dev = float(std_dev)
        radl_out.stats.max_val = float(self.global_max)
        radl_out.stats.min_val = float(self.global_min)
        
        # Print detailed stats periodically (every 50 samples)
        if self.count % 50 == 0:
            # Use scipy for additional statistics
            if len(window) > 2:
                skewness = scipy_stats.skew(window)
                kurtosis = scipy_stats.kurtosis(window)
            else:
                skewness = 0.0
                kurtosis = 0.0
            
            print(f"[Stats] n={self.count:4d} | "
                  f"mean={mean:7.4f} | std={std_dev:6.4f} | "
                  f"range=[{self.global_min:.4f}, {self.global_max:.4f}] | "
                  f"skew={skewness:6.3f} | kurt={kurtosis:6.3f}",
                  flush=True)

