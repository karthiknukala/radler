#!/usr/bin/env python3
"""
Sensor Simulator - Python node that publishes to a C++ subscriber

Demonstrates:
- Using numpy in a Radler Python node
- Publishing data that a C++ node will consume
- The seamless interoperability between Python and C++ via ROS2 topics
"""

import numpy as np
import time


class SensorSimulator:
    """
    Simulates environmental sensor readings using numpy for signal generation.
    
    Generates realistic-looking sensor data with:
    - Base values with sinusoidal variation (daily cycles)
    - Random noise
    - Occasional spikes to trigger alerts in the C++ processor
    """
    
    def __init__(self):
        """Initialize the sensor simulator"""
        self.step_count = 0
        self.start_time = time.time_ns()
        
        # Base values for sensors
        self.base_temp = 22.0      # 22°C room temperature
        self.base_pressure = 1013.25  # Standard atmospheric pressure hPa
        self.base_humidity = 45.0  # 45% relative humidity
        
        # Random seed for reproducibility in demos
        np.random.seed(42)
        
        print("SensorSimulator initialized (Python + NumPy)", flush=True)
        print("  Publishing to C++ AlertProcessor via ROS2 topic", flush=True)
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Generate and publish simulated sensor readings.
        
        Uses numpy for:
        - Sinusoidal base signal (simulating daily temperature cycle)
        - Gaussian noise
        - Occasional anomaly injection
        """
        # Time-based variation (simulate daily cycle compressed to ~30 seconds)
        t = self.step_count * 0.1  # Time factor
        daily_cycle = np.sin(t * 0.2)  # Slow oscillation
        
        # Generate sensor values with numpy
        noise_temp = np.random.normal(0, 0.5)
        noise_pressure = np.random.normal(0, 2.0)
        noise_humidity = np.random.normal(0, 1.0)
        
        # Base values with cycle and noise
        temperature = self.base_temp + daily_cycle * 5 + noise_temp
        pressure = self.base_pressure + daily_cycle * 10 + noise_pressure
        humidity = self.base_humidity + daily_cycle * 10 + noise_humidity
        
        # Inject anomalies occasionally (every ~20 steps, ~10 seconds)
        if self.step_count % 20 == 15:
            anomaly_type = self.step_count % 3
            if anomaly_type == 0:
                temperature += 15  # Temperature spike
                print(f"[Python] Injecting TEMPERATURE anomaly: {temperature:.1f}°C", flush=True)
            elif anomaly_type == 1:
                pressure += 50     # Pressure spike
                print(f"[Python] Injecting PRESSURE anomaly: {pressure:.1f} hPa", flush=True)
            else:
                humidity = 95      # Humidity spike
                print(f"[Python] Injecting HUMIDITY anomaly: {humidity:.1f}%", flush=True)
        
        # Clamp humidity to valid range
        humidity = np.clip(humidity, 0, 100)
        
        # Publish the reading
        radl_out.reading.timestamp = time.time_ns()
        radl_out.reading.temperature = float(temperature)
        radl_out.reading.pressure = float(pressure)
        radl_out.reading.humidity = float(humidity)
        
        # Print status every 10 steps (~5 seconds)
        if self.step_count % 10 == 0:
            print(f"[Python] Step {self.step_count}: "
                  f"T={temperature:.1f}°C, P={pressure:.1f}hPa, H={humidity:.1f}%", 
                  flush=True)
        
        self.step_count += 1

