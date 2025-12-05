/**
 * Alert Processor - C++ node that subscribes to Python publisher
 * 
 * Demonstrates:
 * - Receiving data published by a Python node
 * - Processing sensor data and generating alerts
 * - The seamless interoperability between Python and C++ via ROS2 topics
 */

#ifndef ALERT_PROCESSOR_H
#define ALERT_PROCESSOR_H

#include <cstdint>
#include <cstdio>

// Alert type constants
constexpr int32_t ALERT_NONE = 0;
constexpr int32_t ALERT_TEMPERATURE = 1;
constexpr int32_t ALERT_PRESSURE = 2;
constexpr int32_t ALERT_HUMIDITY = 3;

// Severity constants
constexpr int32_t SEVERITY_INFO = 0;
constexpr int32_t SEVERITY_WARNING = 1;
constexpr int32_t SEVERITY_CRITICAL = 2;

// Threshold values
constexpr double TEMP_WARNING = 30.0;    // °C
constexpr double TEMP_CRITICAL = 35.0;   // °C
constexpr double PRESSURE_LOW = 980.0;   // hPa
constexpr double PRESSURE_HIGH = 1040.0; // hPa
constexpr double HUMIDITY_HIGH = 80.0;   // %

class AlertProcessor {
private:
    uint64_t step_count_;
    uint64_t alerts_generated_;
    
    // Running statistics
    double temp_sum_;
    double temp_count_;
    
public:
    AlertProcessor() 
        : step_count_(0)
        , alerts_generated_(0)
        , temp_sum_(0.0)
        , temp_count_(0.0) {
        printf("[C++] AlertProcessor initialized\n");
        printf("[C++] Subscribing to Python SensorSimulator via ROS2 topic\n");
        fflush(stdout);
    }
    
    template<typename In, typename InF, typename Out, typename OutF>
    void step(In* in, InF* in_flags, Out* out, OutF* out_flags) {
        step_count_++;
        
        // Check if we have valid sensor data
        // Note: in_flags->sensor uses RADL flag semantics (same as Python!)
        if (in_flags->sensor & 0x30) {  // RADL_TIMEOUT
            // No data received yet or timeout
            out->alert->alert_type = ALERT_NONE;
            out->alert->message = 0;
            out->alert->severity = SEVERITY_INFO;
            return;
        }
        
        // Extract sensor values (published by Python node)
        // Note: in->sensor is a shared_ptr, so use -> to access fields
        double temperature = in->sensor->temperature;
        double pressure = in->sensor->pressure;
        double humidity = in->sensor->humidity;
        
        // Update running average
        temp_sum_ += temperature;
        temp_count_ += 1.0;
        double temp_avg = temp_sum_ / temp_count_;
        
        // Initialize output (out->alert is a pointer)
        out->alert->alert_type = ALERT_NONE;
        out->alert->message = 0;
        out->alert->severity = SEVERITY_INFO;
        
        // Check for temperature alerts
        if (temperature > TEMP_CRITICAL) {
            out->alert->alert_type = ALERT_TEMPERATURE;
            out->alert->message = static_cast<int64_t>(temperature * 100);
            out->alert->severity = SEVERITY_CRITICAL;
            alerts_generated_++;
            printf("[C++] CRITICAL: Temperature %.1f°C exceeds %.1f°C!\n", 
                   temperature, TEMP_CRITICAL);
            fflush(stdout);
        } else if (temperature > TEMP_WARNING) {
            out->alert->alert_type = ALERT_TEMPERATURE;
            out->alert->message = static_cast<int64_t>(temperature * 100);
            out->alert->severity = SEVERITY_WARNING;
            alerts_generated_++;
            printf("[C++] WARNING: Temperature %.1f°C exceeds %.1f°C\n", 
                   temperature, TEMP_WARNING);
            fflush(stdout);
        }
        
        // Check for pressure alerts
        if (pressure > PRESSURE_HIGH || pressure < PRESSURE_LOW) {
            out->alert->alert_type = ALERT_PRESSURE;
            out->alert->message = static_cast<int64_t>(pressure * 100);
            out->alert->severity = SEVERITY_WARNING;
            alerts_generated_++;
            printf("[C++] WARNING: Pressure %.1f hPa outside normal range\n", pressure);
            fflush(stdout);
        }
        
        // Check for humidity alerts
        if (humidity > HUMIDITY_HIGH) {
            out->alert->alert_type = ALERT_HUMIDITY;
            out->alert->message = static_cast<int64_t>(humidity * 100);
            out->alert->severity = SEVERITY_WARNING;
            alerts_generated_++;
            printf("[C++] WARNING: Humidity %.1f%% exceeds %.1f%%\n", 
                   humidity, HUMIDITY_HIGH);
            fflush(stdout);
        }
        
        // Print status every 50 steps (~5 seconds at 100ms period)
        if (step_count_ % 50 == 0) {
            printf("[C++] Step %lu: Received T=%.1f°C (avg=%.1f), P=%.1f, H=%.1f | Alerts: %lu\n",
                   step_count_, temperature, temp_avg, pressure, humidity, alerts_generated_);
            fflush(stdout);
        }
    }
};

#endif // ALERT_PROCESSOR_H

