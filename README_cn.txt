Data Cleaning

Rawdata Overview:

- 数据规模：240,919 条交易记录，11 个变量。
- 时间范围：2017年1月至2026年9月，共117个月。
- 分类变量：包括26个市镇（town）、7种房型（flat_type）和21种住宅型号（flat_model）。
- 缺失值：11个变量均未发现缺失值。
- 变量格式：成交价格和建筑面积均大于0；剩余租期可转换为年数，楼层以区间记录。
- 地址信息：共有9,749个不同地址，以“楼栋号＋街道名”识别；每个地址对应一个市镇。
- 重复记录检查：有635条记录的所有字段与其他记录相同，直接去重会删除其中318条。由于数据不含具体单位号码和唯一交易编号，无法确认是否为重复交易，因此全部保留并标记。
- 年度覆盖：2017—2025年共有222,067条记录；2026年仅包含1—9月，共18,852条记录。

文件
- data/hdb_clean.csv: Core analysis table with separate year and month columns; MRT distances and inflation adjustment are not yet available.
- data/hdb.csv: Prepared notebook input, retained for traceability.
- *data/addresses.csv：地址清单，供 B 查询坐标。(B)
- data/duplicates.csv：疑似重复记录，已保留并标记。
- data/audit.json：数据检查和处理记录。
- tasks.txt：小组分工与截止日期。
- ai_log.txt：AI 使用记录。


字段说明

- source_row：原始数据行号，用于追溯记录。
- address_key：由楼栋号和街道名组成的地址标识，用于合并数据。
- year: Registration year in the cleaned table.
- month: Registration month number (1-12) in the cleaned table.
- remaining_lease_months、remaining_lease_years：剩余租期，分别以月和年为单位。
- storey_range: Ordered categorical floor band. 01 TO 03 means floor 1, 2 or 3; 10 TO 12 means floor 10, 11 or 12. The exact floor is not recorded.
- storey_lower, storey_upper: Lower and upper floor numbers of the band.
- log_nominal_resale_price：成交价格的自然对数，未经通胀调整。
- same_public_fields_flag：疑似重复标记，表示原始字段完全相同；相关记录仍保留。
- resale_price: Total resale price per flat in Singapore dollars (SGD), without inflation adjustment.
- floor_area_sqm: Floor area in square metres.
- lease_commence_date: Lease commencement year.
- block：文本变量，保留楼栋号中的字母。

B 的数据交接要求
1. 每个地址保留一行结果，包括 address_key、经纬度和匹配状态。
2. 核对返回地址与原地址是否一致；有多个结果时需进一步确认。
3. 保留未匹配地址及失败原因，避免遗漏交易记录。
4. 按 address_key 将结果合并回主表；合并后仍应有 240919 条交易记录。
5. MRT 距离统一以米记录，并注明使用直线距离还是步行距离。
6. 跨年分析需核实车站和出口在交易时是否已开放。

团队仍需决定
分析时期，以及 2026 不完整年度的处理。
MRT 距离口径和历史覆盖处理。
是否补 CPI、使用哪个指数和基期；没有 CPI 时保留名义价格标签。
时间固定效应、距离分段、模型样本及缺失处理方式。

已执行的验证
重新读取准备后的 CSV；原始与输出行数均为 240919；block 文本逐行一致。
source_row 唯一；地址队列键唯一；队列 transaction_count 总和等于交易行数。
模拟 many_to_one 地址合并后行数仍为 240919。
脚本成功处理该原始文件，输出名义价格标签，没有生成虚构 MRT 距离或实际价格。
