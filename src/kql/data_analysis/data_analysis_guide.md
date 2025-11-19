# Data Analysis Methods for Anomaly Detection

This guide compares different statistical methods for setting thresholds in manufacturing anomaly detection systems.

## Overview

When analyzing sensor data (Speed, Humidity, Temperature, Vibration, etc.) to establish alert thresholds, you have two primary approaches:

1. **Percentile-Based Thresholds** (P5/P95)
2. **Z-Score Based Thresholds** (Standard Deviation)

## Method Comparison

| Aspect | P5 & P95 Percentiles | Z-Score ±2.0 |
|--------|---------------------|--------------|
| **Data Coverage** | 90% (excludes 5% each side) | 95.4% (excludes 2.3% each side) |
| **Sensitivity** | More sensitive (tighter bounds) | Less sensitive (looser bounds) |
| **Distribution Assumption** | None - works with any data shape | Assumes normal distribution |
| **Outlier Handling** | Robust to extreme outliers | Affected by outliers |
| **Symmetry** | Adapts to data asymmetry | Always symmetric around mean |
| **False Alarm Rate** | Higher (more alerts) | Lower (fewer alerts) |
| **Industry Standard** | Data-driven approach | Statistical process control |

## When to Use Each Method

### Use **Percentile Method (P5/P95)** when:
- Manufacturing sensor data with unknown distribution
- Need high sensitivity to process changes
- Data contains occasional sensor spikes/errors
- Want distribution-free approach
- Starting point for new monitoring systems

### Use **Z-Score Method (±2.0)** when:
- Data follows roughly normal distribution
- Want fewer false alarms
- Following statistical process control standards
- Need theoretical foundation for thresholds
- Percentile method generates too many alerts

## Implementation Examples

### Percentile Approach (90% Coverage)
```kql
events
| where Timestamp >= startTime and Timestamp <= endTime
| summarize 
    LowerThreshold_P5 = percentile(Humidity, 5),
    UpperThreshold_P95 = percentile(Humidity, 95),
    MedianValue = percentile(Humidity, 50)
```

### Z-Score Approach (95.4% Coverage)
```kql
events
| where Timestamp >= startTime and Timestamp <= endTime
| summarize 
    AvgValue = avg(Humidity),
    StdDevValue = stdev(Humidity),
    LowerThreshold_ZScore2 = avg(Humidity) - (2.0 * stdev(Humidity)),
    UpperThreshold_ZScore2 = avg(Humidity) + (2.0 * stdev(Humidity))
```

## Recommended Approach for Manufacturing

1. **Start with Percentile Method (P5/P95)** for initial threshold setting
2. Monitor alert frequency and accuracy over 1-2 weeks
3. **Switch to Z-Score ±2.0** if experiencing too many false alarms
4. Consider **Z-Score ±1.5** for even higher sensitivity if needed

## Time Window Recommendations

- **Historical Analysis**: Use 30 days of data excluding last 24 hours
- **Exclude Recent Data**: Avoid contaminating baseline with current anomalies
- **Regular Updates**: Recalculate thresholds monthly or quarterly

## File Examples in This Repository

- `find_humidity_range_z_score.kql` - Z-score implementation for humidity
- `speed_range.kql` - Percentile implementation for speed analysis
- `DefectProbability_range.kql` - Percentile analysis for defect prediction

## Key Takeaway

Both methods are valid. **Percentiles are often better for real-world manufacturing data** due to their robustness and sensitivity, while **Z-scores provide theoretical grounding** and are standard in statistical process control.