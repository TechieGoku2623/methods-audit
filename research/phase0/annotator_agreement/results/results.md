# annotator_agreement results

n = 15 papers, two committed gold passes.

Value agreement is 0.981 on 480 field-pairs. Exact-span agreement on jointly filled fields is 1.000 (mean IoU 1.000). Extraction accuracy cannot honestly exceed this agreement on the same texts.

| metric | value |
| --- | --- |
| n papers | 15 |
| value agreement | 0.981 |
| exact span agreement | 1.000 |
| mean span IoU | 1.000 |
| accuracy upper bound | 0.981 |

Fields with any disagreement:

| field | value agreement |
| --- | --- |
| antibody_rrid | 0.800 |
| culture_conditions | 0.800 |
| karyotype_or_cn_check | 0.800 |
