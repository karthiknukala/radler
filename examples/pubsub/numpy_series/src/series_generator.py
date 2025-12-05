#!/usr/bin/env python3
"""
Series Generator - Demonstrates numpy/scipy in Radler Python nodes

Generates successive values from Chebyshev polynomials of the first kind.
These polynomials are used extensively in numerical analysis and approximation theory.

The nth Chebyshev polynomial T_n(x) satisfies: T_n(cos(θ)) = cos(nθ)
"""

import numpy as np
from scipy.special import eval_chebyt


class SeriesGenerator:
    """
    Generates Chebyshev polynomial values at successive points.
    
    For each step, computes T_n(x) where:
    - n cycles through polynomial degrees 0-10
    - x sweeps through [-1, 1] (the natural domain of Chebyshev polynomials)
    """
    
    def __init__(self):
        """Initialize the series generator"""
        self.index = 0
        self.degree = 0  # Polynomial degree (0-10)
        self.num_points = 50  # Points per polynomial
        self.point_index = 0
        
        # Pre-compute x values using Chebyshev nodes (optimal for interpolation)
        # x_k = cos((2k+1)π / 2n) for k = 0, 1, ..., n-1
        self.x_values = np.cos(
            (2 * np.arange(self.num_points) + 1) * np.pi / (2 * self.num_points)
        )
        
        print("SeriesGenerator initialized", flush=True)
        print(f"  Computing Chebyshev polynomials T_0(x) through T_10(x)", flush=True)
        print(f"  Using {self.num_points} Chebyshev nodes per polynomial", flush=True)
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Generate the next value in the Chebyshev polynomial series.
        
        Uses scipy.special.eval_chebyt for numerically stable evaluation.
        """
        # Get current x value
        x = self.x_values[self.point_index]
        
        # Evaluate Chebyshev polynomial T_n(x) using scipy
        # This is more numerically stable than the recurrence relation
        value = eval_chebyt(self.degree, x)
        
        # Publish the result
        radl_out.series.index = self.index
        radl_out.series.value = float(value)
        radl_out.series.x_point = float(x)
        
        # Print progress periodically
        if self.point_index == 0:
            print(f"[Gen] Starting T_{self.degree}(x), index={self.index}", flush=True)
        
        # Advance to next point
        self.point_index += 1
        self.index += 1
        
        # Move to next polynomial when done with current one
        if self.point_index >= self.num_points:
            self.point_index = 0
            self.degree = (self.degree + 1) % 11  # Cycle through degrees 0-10

