# cost_per_paper results

n papers = 50. Local render+tokenize = 8.50 ms total. API RTT = unmeasured.

Default extraction model: gemini-2.0-flash ($0.000345/paper). Escalate to a larger tier only when the cache miss fails span-grounded validation.

| model | mean input tok/paper | USD/paper | USD/1000 papers |
| --- | --- | --- | --- |
| gpt-4o-mini | 247.5 | 0.000517 | 0.52 |
| gpt-4o | 247.5 | 0.008619 | 8.62 |
| claude-haiku-4-5 | 247.5 | 0.004248 | 4.25 |
| claude-sonnet-4-5 | 247.5 | 0.012743 | 12.74 |
| gemini-2.0-flash | 247.5 | 0.000345 | 0.34 |
