# JSON原生类型诊断

Outcomes are mutually exclusive and sum to planned calls within each provider/arm/scope.

Native type is finite int/float excluding bool for numeric tasks, and expected top-level JSON type for exact tasks.

Array element types, shape and content remain part of strict correctness, not this top-level type endpoint.

Strings are never decoded or coerced. Invalid JSON and truncation are not native-type successes.

Type intervals use returned matched pairs and task-cluster percentile bootstrap, 2000 draws, seed 2026100301.

Fresh task parameters within known families; not new domains, population inference or equivalence evidence.

|模型|条件|范围|类型正确/返回/计划|类型错误|类型对但答案错|答案正确|JSON错误/截断|请求失败/待定/未尝试|
|---|---|---|---|---:|---:|---:|---|---|
|deepseek|native_control|all|30/32/32|2|4|26|0/0|0/0/0|
|deepseek|native_control|answer_type:number|24/24/24|0|4|20|0/0|0/0/0|
|deepseek|native_control|answer_type:array|6/8/8|2|0|6|0/0|0/0/0|
|deepseek|native_explicit|all|32/32/32|0|4|28|0/0|0/0/0|
|deepseek|native_explicit|answer_type:number|24/24/24|0|4|20|0/0|0/0/0|
|deepseek|native_explicit|answer_type:array|8/8/8|0|0|8|0/0|0/0/0|
|kimi|native_control|all|11/32/32|20|1|10|1/0|0/0/0|
|kimi|native_control|answer_type:number|5/24/24|18|1|4|1/0|0/0/0|
|kimi|native_control|answer_type:array|6/8/8|2|0|6|0/0|0/0/0|
|kimi|native_explicit|all|30/30/32|0|5|25|0/0|2/0/0|
|kimi|native_explicit|answer_type:number|22/22/24|0|5|17|0/0|2/0/0|
|kimi|native_explicit|answer_type:array|8/8/8|0|0|8|0/0|0/0/0|

## 同题类型变化

|模型|范围|配对/缺失|类型正确次数|改善/退步|类型合格率差|95%描述区间（仅整体）|
|---|---|---|---|---|---|---|
|deepseek|all|32/0|30→32|2/0|0.0625|[0.0, 0.1875]|
|deepseek|answer_type:number|24/0|24→24|0/0|0.0|—|
|deepseek|answer_type:array|8/0|6→8|2/0|0.25|—|
|kimi|all|30/2|10→30|20/0|0.6666666666666666|[0.4373958333333333, 0.8666666666666667]|
|kimi|answer_type:number|22/2|4→22|18/0|0.8181818181818182|—|
|kimi|answer_type:array|8/0|6→8|2/0|0.25|—|
