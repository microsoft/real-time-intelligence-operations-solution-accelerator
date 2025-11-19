# Sample User Questions for Fabric Data Agent
*Reverse-engineered from KQL Analytics to Drive Smart Business Insights*

## 📋 Overview
These sample questions are designed to help business users get maximum value from the Fabric Data Agent by leveraging the comprehensive manufacturing analytics we've built. Each question category maps to specific KQL utilities and business scenarios.

---

## 🏭 Executive & Strategic Questions
*Maps to: Manufacturing Data Overview, Business Intelligence Dashboard*

### 1. Production Overview

| #    | Question                                                   | Expected Answer (Sample)                                     | Tested Answer (Sample)                                       |
| ---- | ---------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1    | What's our total production volume over the last 3 months? | *Expected: Total event count (259K+), breakdown by asset, production period coverage* | Your total production volume over the last 3 months is 259,446 records. This represents the total number of production events captured in your system during that period. |
| 2    | Which asset is producing more units - A_1000 or A_1001?    | *Expected: Comparative production counts, percentage split, performance ranking* | Your total production volume over the last 3 months is 259,446 units (each representing a production event recorded by your assets). This reflects all assets and batches tracked in your manufacturing system during this time period. If you need a breakdown by asset, product, or another dimension, just let me know! |
| 3    | Show me daily production trends for the past month         | *Expected: Daily production counts, trend analysis, peak/low production days* | Here are your daily production trends for the past month (per asset):Each day, both A_1000 and A_1001 typically produced 1,440 units. On 10/15/2025, both assets produced 192 units—lower than the following days, which may indicate a partial production day or start-up/ramp-up. From 10/16/2025 onward, production stabilized at 1,440 units per day per asset. |
| 4    | What's our average daily production capacity?              | *Expected: Daily averages, capacity utilization, asset-specific rates* | Your average daily production capacity over the past month is approximately 2,734 units per day. This reflects a strong and consistent production rate during this period. |

### 2. Financial Performance

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | What's the total revenue generated from our manufacturing operations? | *Expected: Total revenue calculations, quality premiums, asset contributions* | The total revenue generated from your manufacturing operations is $18,940,446.64. This is calculated by multiplying the quantity of each produced product by its list price and summing across all units. If you’d like to see revenue broken down by product, asset, or time period, just let me know! |
| 2 | Which asset is more profitable - A_1000 or A_1001? | *Expected: Profit comparison, margin analysis, ROI metrics by asset* | Here's a profitability comparison for A_1000 and A_1001 over the last 3 months: <br />   Both assets produced the same number of units: 129,742 each. A_1000 had a lower average defect rate (0.47%) compared to A_1001 (1.12%). Total revenue was similar for both assets, around 9.45 million. Quality Adjusted Revenue (which factors in defect rates) was higher for A_1000 ($9,404,759) than A_1001 ($9,349,379). <br /> |
| 3 | How does product quality affect our revenue per unit? | *Expected: Quality premium calculations, defect rate impact on pricing* | Product quality (measured by defect probability) has a direct, though relatively small, impact on your revenue per unit:<br/>For most products, the average defect rate is between 0.72% and 0.88%.<br/>Base revenue per unit varies by product, but the quality-adjusted revenue per unit is reduced by roughly the same percentage as the defect rate (for example: a 0.8% defect rate reduces revenue per unit by 0.8%).<br/>For every product, a higher defect rate slightly decreases the quality-adjusted revenue per unit, which reflects lost revenue on defective items.<br/>In summary: Even small improvements in product quality will incrementally boost your revenue per unit. Keeping defect rates as low as possible directly supports higher profitability. If you want to focus on a specific product or time period, let me know!<br/> |
| 4 | What are our total production costs versus revenue? | *Expected: Cost breakdown, profit margins, operational efficiency ratios* | For the last 3 months:<br />  Total Production Costs: $11,328,244.36 Total Revenue: $18,217,543.15<br />This means your manufacturing operations generated approximately $6.89 million more in revenue than in direct production costs over this period. **If you want a breakdown by asset, time period, or product, just let me know!** |
| 5 | Show me profit margins by asset | *Expected: Asset-specific margins, performance ranking, profitability trends* | Here are the profit margins by asset for the last 3 months:<br />  A_1000: Profit Margin = 37.82% A_1001: Profit Margin = 37.81%<br />Both assets deliver nearly identical profit margins, with A_1000 having a very slight edge. If you’d like this broken down further by month, shift, or with more granularity, let me know! |

### 3. Asset Utilization

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | What's the utilization rate of our manufacturing assets? | *Expected: Utilization percentages, operating hours, efficiency metrics* | The utilization rate of your manufacturing assets over the last 3 months is:<br />  A_1000: 96.7% A_1001: 96.7%<br />Both assets have been active on 88 out of 91 possible days, indicating highly efficient and consistent use of your manufacturing equipment. If you want to analyze downtime patterns or look at utilization by shift or week, just let me know! |
| 2 | How many hours per day are our assets running? | *Expected: Daily operating hours, shift coverage, uptime analysis* | On average, both A_1000 and A_1001 are running for approximately 23.6 hours per day over the last 3 months.<br />This indicates near-continuous operation, with very minimal downtime each day. If you’d like more detail—such as downtime analysis or hourly production patterns—just let me know! |
| 3 | Which asset has better overall performance? | *Expected: Performance comparison, efficiency scores, quality metrics* | Asset A_1000 has better overall performance than A_1001 based on key metrics from the last 3 months:<br />  Total units produced: Equal (124,648 each) Average defect probability (quality): A_1000 = 5%, A_1001 = 10.02% Profit margin: Both at 27.63% Utilization rate: Both at 100% Overall performance: A_1000 is best due to significantly higher quality (lower defect rate) with equal output, margin, and uptime.<br />**A_1000 is your top-performing asset**. If you’d like targeted recommendations to bring A_1001 up to A_1000’s standard, just let me know! |

---

## 📊 Quality Management Questions
*Maps to: Quality Control Analytics, Defect Analysis*

### 1. Quality Performance

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | What's our current defect rate across all production? | *Expected: Overall defect percentage, asset breakdown, quality benchmarks* |  |
| 2 | Which asset produces higher quality products? | *Expected: Quality comparison, defect rates by asset, performance ranking* | Asset A_1000 produces higher quality products than A_1001.<br />  A_1000: Average Defect Probability = 5%, Quality Score = 95 A_1001: Average Defect Probability = 10.02%, Quality Score = 90<br />This means A_1000 operates closer to Six Sigma quality and delivers consistently better product quality compared to A_1001. If you’d like recommendations on optimizing A_1001 or detailed insights by shift or condition, just ask! |
| 3 | Are we meeting Six Sigma quality standards? | *Expected: Six Sigma compliance (<2% defects), gap analysis, quality grades* | No, your manufacturing operations are not currently meeting Six Sigma quality standards. The average defect rate over the last 3 months is approximately 7.51%, which is above the Six Sigma benchmark of 2%.<br />To close the gap and reach Six Sigma levels, consider focusing on root cause analysis for defects, process improvements, and stricter quality controls. If you’d like detailed breakdowns by shift, asset, or product to pinpoint areas for improvement, let me know! |
| 4 | Show me quality trends over the last month | *Expected: Quality trend analysis, improvement/decline patterns, time-based insights* | Here are your quality trends (average daily defect probability, in percent) for the last month:<br />  Most days show an average defect probability between 7.4% and 7.6%. The trend is quite stable—there are no major upward or downward shifts.<br />Example from selected days:<br />10/4/2025: 7.41% 10/9/2025: 7.59% 10/14/2025: 7.60% 10/22/2025: 7.48% 10/28/2025: 7.53%<br />Interpretation: Your daily quality is consistent, but consistently above Six Sigma standards (2%). This indicates a stable process but highlights an opportunity for targeted process improvements to bring defect rates down. |
| 5 | What percentage of products meet our quality targets? | *Expected: Quality compliance rates, target achievement, performance metrics* |  |

### 2. Quality Benchmarking

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | How do we compare to industry quality standards? | *Expected: Benchmark comparison, industry standard analysis, competitive positioning* | Based on your recent data:<br />Your average defect rate over the last 3 months is approximately 7.51%.<br />Industry quality standards for world-class manufacturing are often measured by the Six Sigma benchmark, which targets a defect rate below 2% (that is, fewer than 2 defects per 100 units produced).<br />Comparison summary:<br />  Your defect rate (7.51%) is significantly above the Six Sigma standard (2%). This suggests your operation is reasonably stable but not yet world-class in quality compared to leading manufacturers in the industry. Most top-tier manufacturers strive for defect rates well below 5%, and truly elite operations achieve or approach Six Sigma quality levels.<br />Recommendation:<br />  To reach or exceed industry standards, focusing on process improvements, defect root cause analysis, and continuous quality initiatives will be necessary. If you’d like benchmarking against specific competitors or want a breakdown by product line or shift to target improvements, just let me know! |
| 2 | What's our quality grade compared to best practices? | *Expected: Quality grading (A+ to D), best practice gaps, improvement opportunities* | Your current quality grade over the last 3 months is D, with an average defect rate of 7.51%.<br />Compared to best practices:<br />  Best practice in manufacturing is achieving an A+ (≤2% defect rate) or A (≤3.5% defect rate). Your quality is below best practice levels.<br />To improve your grade and move towards industry-leading quality, consider implementing tighter quality control processes, root cause defect analysis, and continuous improvement programs. If you want more detailed recommendations or breakdowns by product or asset, just let me know! |
| 3 | Are we improving or declining in quality over time? | *Expected: Quality trend analysis, improvement rates, time-series comparison* | Your month-over-month quality trend for the last 3 months is as follows (defect rate, %):<br />  August 2025: 7.51% September 2025: 7.50% October 2025: 7.52%<br />Interpretation:<br />  Product quality has remained very stable with minimal variation (within ±0.02%). There is no clear improvement or decline—your quality trends are essentially flat. This stability suggests process consistency, but does not indicate progress toward improvement.<br /> |
| 4 | Which shift produces the highest quality products? | *Expected: Shift-based quality analysis, performance ranking, operational insights* | All three shifts—Day, Evening, and Night—produce products with the same average defect probability: 7.51%.<br />This means there is no significant difference in product quality by shift. Quality performance is consistent across all shift patterns for the last 3 months. |



---

## 📈 Statistical & Analytical Questions
*Maps to: Baseline Statistics, Defect Analysis*

### 1. Performance Benchmarking

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | What are the baseline performance metrics for each asset? | *Expected: Baseline statistics, mean/std deviation, performance benchmarks* | Here are the baseline performance metrics for each asset (last 3 months):<br />A_1000<br />Total Units Produced: 124,427 Average Speed: 30 RPM Average Temperature: 24°C Average Defect Probability: 5% Average Profit Margin: 37.77% Utilization Rate: 60.02%<br />A_1001<br />  Total Units Produced: 124,427 Average Speed: 55 RPM Average Temperature: 30°C Average Defect Probability: 10.02% Average Profit Margin: 37.77% Utilization Rate: 60.02% |
| 2 | How consistent is our production performance? | *Expected: Performance consistency analysis, variability metrics, stability indicators* | Both assets, A_1000 and A_1001, have a daily standard deviation in production of about 79.6 units over the last 3 months.<br />Given their average daily production is around 2,880 units, this represents very low variability (less than 3% fluctuation day-to-day). This indicates that your production performance is highly consistent, with minimal swings or interruptions.<br />If you’d like to see consistency for other metrics (like speed, quality, or shift output), just let me know! **Yes**  <br /><br />Here's a summary of your production consistency, not just for output, but also for speed, quality, and profit margin over the last 3 months:<br />A_1000<br />  Daily Production Std Dev: 79.6 units (very low versus ~2,880 average) Speed Std Dev: 0.29 RPM (very stable daily speed) Daily Defect Probability Std Dev: 0.0006 (extremely consistent quality) Daily Profit Margin Std Dev: 0.0006 (profit delivery is steady)<br />A_1001<br />  Daily Production Std Dev: 79.6 units (also highly consistent) Speed Std Dev: 0.43 RPM (still stable, slightly more variable than A_1000) Daily Defect Probability Std Dev: 0.0012 (slightly more variation than A_1000) Daily Profit Margin Std Dev: 0.0012 (also stable financially)<br />**Conclusion: Both assets demonstrate very high consistency in production quantity, speed, quality, and profitability day-to-day, with A_1000 being marginally more stable in speed and quality. This reflects well-controlled operations across critical performance metrics.** |
| 3 | What's the standard deviation in our quality metrics? | *Expected: Quality variability analysis, statistical dispersion, control limits* | For the last 3 months, the standard deviation in your key quality metric (defect probability) is as follows:<br />  A_1000: 0.0006 (very low variability—quality is highly consistent) A_1001: 0.0012 (also low, but with slightly more variability than A_1000)<br />This demonstrates that your quality metrics remain stable on a daily basis for both assets, with A_1000 showing even greater consistency. |
| 4 | What's the coefficient of variation in our operations? | *Expected: CV calculations, process variation, consistency metrics* | Your coefficient of variation for the last 3 months is:<br />A_1000<br />  Daily Production: 0.0557 (5.57%) Defect Probability: 0.0119 (1.19%)<br />A_1001<br />  Daily Production: 0.0557 (5.57%) Defect Probability: 0.0118 (1.18%)<br />Interpretation:<br />  A coefficient of variation below 10% indicates highly consistent operations in both production and quality. Your manufacturing processes are stable, with low variability relative to their averages.<br /> |

### 2. Deep Analytics

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | Show me the statistical distribution of defect rates | *Expected: Distribution analysis, histogram insights, statistical summary* | Here is the statistical distribution of defect rates for the last 3 months:<br />  0–2% defect probability: 10,994 events 2–5%: 65,424 events 5–7.5%: 68,044 events 7.5–10%: 42,140 events Above 10%: 62,238 events<br />This shows most production events cluster in the 2–7.5% range, with a substantial number above 10%. Only a small proportion (about 4.4%) of events meet Six Sigma (≤2%) defect rates. |
| 2 | What percentage of products exceed 5% defect probability? | *Expected: Defect threshold analysis, percentage calculations, quality compliance* | 69.29% of your products (production events) in the last 3 months had a defect probability exceeding 5%.<br />This highlights a significant opportunity for quality improvement, as a majority of production events are above typical industry defect benchmarks. If you want strategies to reduce this rate or to see which products or shifts are most affected, let me know! |
| 3 | What are the 95th percentile values for our key metrics? | *Expected: Percentile analysis, extreme value identification, statistical boundaries* | Here are the 95th percentile values for your key metrics over the last 3 months:<br />  Speed: 75.0 RPM Temperature: 38°C Defect Probability: 15.25%<br />This means that 95% of your production events occurred at or below these levels for each metric. Values beyond these thresholds are rare and may indicate outlier or non-standard operating conditions. |

---

## 💡 Sample Follow-up Questions

### 1. Drill-Down Queries

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | Show me more details about that quality issue | *Expected: Detailed drill-down analysis, incident specifics, contextual data* | Here is the statistical distribution of defect rates for the last 3 months:<br />  0–2% defect probability: 10,994 events 2–5%: 65,424 events 5–7.5%: 68,044 events 7.5–10%: 42,140 events Above 10%: 62,238 events<br />Most production events fall in the 2–7.5% range, while a substantial number are above 10%. Only a small portion (about 4.4% of events) have a defect probability at or below the Six Sigma standard (2%). |
| 2 | What were the operating conditions during that time? | *Expected: Operational context, parameter values, environmental conditions* |  |
| 3 | Can you break that down by hour/day/week? | *Expected: Time-based breakdown, granular analysis, temporal patterns* |  |
| 4 | What other metrics were affected? | *Expected: Cross-impact analysis, related metric correlation, system-wide effects* |  |

### 2. Correlation Analysis

| # | Question | Expected Answer Type | Sample Answer |
|---|----------|---------------------|---------------|
| 1 | How does that relate to our revenue? | *Expected: Revenue correlation analysis, financial impact assessment* | Here’s how defect rate bands relate to your revenue for the past 3 months:<br />  2–5%: $4,774,794 total ($72.99 avg/unit) 5–7.5%: $4,979,281 total ($73.18 avg/unit) 7.5–10%: $3,078,689 total ($73.06 avg/unit) Above 10%: $4,545,110 total ($73.03 avg/unit)<br />**Insights**:<br />  The average revenue per unit remains relatively stable across defect bands (about $73 per unit), with only small variations. However, a large number of your products are produced in higher defect bands, which increases the risk of non-saleable or returned products, hidden costs, or the need for discounts. Lower defect rates ensure more saleable units and reduced hidden costs, helping maintain strong actual realized revenue. |
| 2 | Is there a connection between speed and quality? | *Expected: Speed-quality correlation, trade-off analysis, relationship insights* | Yes, there is a noticeable connection between production speed and quality: <br />At moderate speeds (30–89 RPM), the defect probability is very low (~0.18–0.28%), indicating optimal quality. <br />At higher speeds (90–119 RPM), defect probability increases to 2.39%. <br />At the highest speeds (120+ RPM), defect probability spikes significantly to 45.29%. <br />At very low speeds (<30 RPM), defect probability is also very high (31.09%).<br /> Summary: The best product quality is achieved at moderate speeds. Both extremely high and very low speeds lead to much higher defect rates, which can negatively impact your revenue and customer satisfaction. For optimal results, operate within the 30–89 RPM range. If you need more detailed insight by asset or shift, let me know! |
| 3 | What factors influence that metric? | *Expected: Factor analysis, influence drivers, correlation identification* | Great question! The metric of product quality—measured here as defect probability—is typically influenced by several key factors in manufacturing environments. According to your available production data, these are the most significant factors: <br />**Speed of Operation:** As shown in your data, both very high and very low operating speeds increase defect rates, while moderate speeds maintain low defects.<br /> **Temperature:** Operating temperature affects material properties and process stability. Temperatures outside the optimal range can introduce quality issues.<br />**Vibration:**  Excessive vibration is often a sign of equipment wear or misalignment and can affect product consistency, leading to higher defects.<br /> **Asset/Equipment Condition**: Well-maintained assets generally produce higher quality output. Maintenance status can impact vibration and temperature control, indirectly affecting quality.<br />**Operator and Shift Patterns:** Human factors, such as experience and fatigue, can influence setup precision and reaction to process anomalies. Certain shifts may have slightly different quality profiles. <br />**Product Complexity/Type:**  Some products are more prone to defects due to their design, assembly complexity, or required material precision.<br />**Humidity and Environmental Conditions**:  Changes in ambient humidity can affect material behavior, especially for certain components or adhesives.<br />**Summary**: The primary, data-supported influencers in your system are speed, temperature, vibration, and asset health. Optimizing these parameters can help maintain low defect rates and high product quality. If you want to drill down into any specific factor or see recent trends, let me know!<br /><br /><br /> |

---

## 📚 Tips for Effective Questions

### Best Practices
1. **Be Specific:** Ask about specific assets, time periods, or metrics
2. **Use Context:** Reference recent events or known issues
3. **Ask Follow-ups:** Drill down into interesting findings
4. **Compare:** Ask for comparisons between assets, time periods, or benchmarks
5. **Action-Oriented:** Ask for recommendations and actionable insights

### Question Starters
- What's the...
- How does... compare to...
- Show me trends in...
- Why did... happen?
- What's causing...
- How can we improve...
- What would happen if..
