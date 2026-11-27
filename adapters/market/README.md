# Mangrove 市场看板适配

对照平台当前拥挤度入口、刷新批次和证据字段，将研究输出先转为离线验收包。四类指标按功能分支维护，统一交换格式只带汇总序列。平台默认部署与公共 fork 不共享私有实现代码。

| 区域 | 来源 | 展示及注册决策 |
|---|---|---|
| 拥挤度 | 行业拥挤度研究分支 | 用不同前缀登记独立序列，放在现有拥挤度分类候选中。量纲分位必须是 0–100。原始倍数/比率只留研究预览 |
| 赚钱效应与脆弱性 | 本仓库市场因子 | 赚钱效应、指数和参与面背离、异常成交、融资与波动作为市场状态候选，使用单独区域 |
| 社区关注与方向 | 社区项目 fork | 文本方向、活跃与情绪发布为社区汇总，市场与板块两级分别索引 |
| 短线接力 | 短线项目的收盘适配 | 涨停池与承接指标展示零值和缺测的区别。收益中位数明确标签为昨日涨停股的当日收益 |

平台目前可核对的类型里已有 `cn_crowding`，其它三部分需后续独立注册。首次接入应在平台侧完成契约注册、按权限写入、支持刷新/可得时点、前端路由及回归验证。当前适配不调用数据库、刷新任务或线上接口。

## 生成市场研究聚合

```sh
python adapters/market/export_market.py --snapshot-dir inputs/dashboard --start 2026-11-01 --out market.json
```

需按主仓库 README 准备有权限的同版本快照。该档案只证明整批数据的定版可用时间，因此导出将这三份输入的最晚生成时间写入 `available_at`。逐时点回测仍需逐日留档，不能用定版档案回写首见时间。

## 汇总离线预览

```sh
python adapters/market/stage_market_board.py --as-of 2026-11-28T00:30:00+08:00 --out out market.json crowding.json community.json shortline.json
```

- `market-board-preview.json` 隔离四个区域，列出序列覆盖、最新日期的状态、最近成功观测和按自然日计算的滞后。最新值为空时，最近成功观测仍有独立位置。现实线上状态和预览截止时点应分别显示。
- `crowding-refresh-candidate.json` 按平台 V2 批次形状给出**仅包含拥挤度分位**的候选，序列默认禁用、使用研究前缀，缺值保留在预览并从批次移除。
- 导出格式为 `{"version": 1, "records": [...]}`。每条包含 family、scope、date、metric、value、unit、available_at、state、method，可选 coverage。scope 和 metric 使用可版本维护的 ASCII 编号。无值必须用 `unobserved` 与 null。时间戳须带时区。重复键、量纲冲突、口径冲突、非法数值在预览入口拒绝。
- 上游口径切换须拆系列。对于任意可见时点，预览仅纳入观测日不晚于当时交易日、可见时间不晚于截止时间的值。已知缺测状态也单独保留。
- 这两个文件是离线验收材料。平台侧后续应先用其真实 Schema 解码，再做受权的集成测试；本分支不向线上记录提交。


## 平台对照点

- [当前拥挤度收集器](https://github.com/zane-pku/mangrove-platform/blob/5165bd6a024efab97f6bc01117930fabcab1c98b/packages/platform/src/macro/crowding/collector.ts) 使用既有授权行情和序列。
- [平台批次契约](https://github.com/zane-pku/mangrove-platform/blob/5165bd6a024efab97f6bc01117930fabcab1c98b/packages/contracts/src/api-schema/macro/contracts.ts) 定义数据源枚举和每个字段。
- [刷新用例](https://github.com/zane-pku/mangrove-platform/blob/5165bd6a024efab97f6bc01117930fabcab1c98b/packages/domain/src/macro/macro-refresh-service.ts) 在外部数据验证后才写入仓库。离线候选应走独立测试入口。
