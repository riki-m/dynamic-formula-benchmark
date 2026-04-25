# Dynamic Benchmark Intelligence Report

_Generated on 2026-04-25 21:30:32_

## Executive Summary
This analysis was generated directly from measured benchmark logs over 1,000,000 records and 11 formulas. C# Engine delivered the strongest overall runtime profile, while SQL Dynamic showed the most stable timing behavior. The performance spread between the fastest and slowest engine reached 38.969s per formula, which makes execution architecture a meaningful production decision.

## Key Findings
- **Fastest Overall**: C# Engine - C# Engine achieved the lowest average runtime at 22.618s per formula, beating Python Eval by 38.969s.
- **Most Stable Runtime**: SQL Dynamic - Runtime variance stayed lowest for SQL Dynamic, with a standard deviation of 2.760s.
- **Closest Race**: Formula 10 - C# Engine won this formula by only 7.866s.
- **Largest Advantage**: Formula 4 - C# Engine created the widest gap here at 16.333s.

## Warnings and Signals
- **Large performance spread**: The slowest engine is more than 2x slower than the fastest one, so architecture choice materially affects latency.
- **Correctness stayed fully aligned**: All 3 validated pairwise comparisons returned mismatched_rows = 0, so the benchmark ranking is safe to trust.

## Category-Level Winners
- **Arithmetic**: C# Engine led. C# Engine 22.908s, SQL Dynamic 31.103s, Python Eval 60.236s.
- **Complex**: C# Engine led. C# Engine 20.533s, SQL Dynamic 32.314s, Python Eval 63.410s.
- **Conditional**: C# Engine led. C# Engine 24.218s, SQL Dynamic 35.185s, Python Eval 62.013s.

## Per-Formula Winners
- Formula 1 (Arithmetic): SQL Dynamic won at 26.696s with a 13.986s lead.
- Formula 2 (Arithmetic): C# Engine won at 18.000s with a 11.519s lead.
- Formula 3 (Arithmetic): C# Engine won at 19.333s with a 14.157s lead.
- Formula 4 (Arithmetic): C# Engine won at 17.634s with a 16.333s lead.
- Formula 5 (Arithmetic): C# Engine won at 18.892s with a 12.953s lead.
- Formula 6 (Complex): C# Engine won at 21.177s with a 10.239s lead.
- Formula 7 (Complex): C# Engine won at 20.918s with a 9.893s lead.
- Formula 8 (Complex): C# Engine won at 19.504s with a 15.210s lead.
- Formula 9 (Conditional): C# Engine won at 23.237s with a 10.570s lead.
- Formula 10 (Conditional): C# Engine won at 26.546s with a 7.866s lead.
- Formula 11 (Conditional): C# Engine won at 22.871s with a 14.465s lead.

## Scenario Recommendations
- **Best overall production choice**: C# Engine - This engine delivered the strongest benchmark profile on the measured workload.
- **Best for rapid prototyping**: Python Eval - The simplest formula-to-execution path with minimal implementation ceremony.
- **Best for DB-centric deployment**: SQL Dynamic - Keeps execution close to the data and avoids repeated application-side transfer work.

