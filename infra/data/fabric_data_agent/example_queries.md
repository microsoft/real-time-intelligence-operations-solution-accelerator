# Example Questions and KQL Queries 

## Overview

This document provides example question and query pairs you can use to provide additional guidance to your data agent. The KQL query must have fewer than 1000 characters. 

### 1. Can you show me the baseline statistics and performance ranges for each asset?

events
| summarize 
    EventCount = count(),
    SpeedMean = round(avg(Speed), 2),
    SpeedStdev = round(stdev(Speed), 2),
    SpeedMin = round(min(Speed), 1),
    SpeedMax = round(max(Speed), 1),
    TempMean = round(avg(Temperature), 2),
    TempStdev = round(stdev(Temperature), 2),
    TempMin = round(min(Temperature), 1),
    TempMax = round(max(Temperature), 1),
    DefectMean = round(avg(DefectProbability), 4),
    DefectStdev = round(stdev(DefectProbability), 4),
    DefectMin = round(min(DefectProbability), 4),
    DefectMax = round(max(DefectProbability), 4)
by AssetId
| order by AssetId



### 2. What are the detailed defect statistics and quality issue rates by asset?

events
| summarize 
    Events = count(),
    MinDefect = round(min(DefectProbability), 4),
    MaxDefect = round(max(DefectProbability), 4),
    MeanDefect = round(avg(DefectProbability), 4),
    MedianDefect = round(percentile(DefectProbability, 50), 4),
    StdDevDefect = round(stdev(DefectProbability), 4),
    P95Defect = round(percentile(DefectProbability, 95), 4),
    Above5Percent = countif(DefectProbability > 0.05),
    Above10Percent = countif(DefectProbability > 0.10),
    Above15Percent = countif(DefectProbability > 0.15)
by AssetId
| extend 
    MeanPercent = round(MeanDefect * 100, 2),
    MedianPercent = round(MedianDefect * 100, 2),
    P95Percent = round(P95Defect * 100, 2)
| extend
    QualityIssueRate = round(Above5Percent * 100.0 / Events, 1),
    HighDefectRate = round(Above10Percent * 100.0 / Events, 1),
    CriticalDefectRate = round(Above15Percent * 100.0 / Events, 1)
| order by MeanPercent asc



### 3. Can you give me a high-level overview of our manufacturing data and operations?

events 
| summarize 
    EventCount = count(),
    DateFrom = min(Timestamp),
    DateTo = max(Timestamp),
    UniqueAssets = dcount(AssetId),
    AvgSpeed = round(avg(Speed), 1),
    AvgTemp = round(avg(Temperature), 1),
    AvgDefectRate = round(avg(DefectProbability) * 100, 2)

