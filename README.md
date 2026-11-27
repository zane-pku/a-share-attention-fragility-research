# A 股社区情绪与市场脆弱性

在交易拥挤度之外，检验**市场参与、短线接力、融资与社区注意力**能否解释或预测后续回撤。优先问两个问题：哪个指标值得继续跟踪？加入成交拥挤度、动量、波动与量能后，它能否提高样本外预测？

## 本轮得到什么

- 对 **14 个市场指标**做历史事件检验，其中 10 个使用固定市场快照，4 个使用通达信复盘表补测。中证800为主目标，检验未来 5/20 个交易日收益与最大回撤。
- 20 日赚钱效应在 2023 年起的留出段给出明显的分组差异，但在验证期反号，逐年加入基准模型后也未改善留出段总体 Brier。量价背离候选有小幅样本外改善，适合独立复测。
- 构建 **28 项因子字典**和 **6 条社区指标的计算原型**。目前可验证的是程序行为与市场指标，真实社区情绪的历史预测力仍待有授权和点时记录的数据检验。

| 入口 | 内容 |
|---|---|
| [回测报告](docs/回测报告.md) | 研究设计、分样本结果、失败结果、风险解释 |
| [因子字典](docs/factors.csv) | 公式、样本要求、研究状态和易错点 |
| [社区指标与验证协议](docs/社区指标与验证协议.md) | 异常提及、求教、追涨、恐慌、净多空及扩散假说 |
| [开源项目与证据](docs/开源项目与证据.md) | 项目许可、借鉴点、资料来源和适用边界 |
| [分组结果](results/tail_groups.csv) · [HAC](results/conditional_hac.csv) · [逐年预测](results/annual_prediction.csv) | 主样本的全量统计 |
| [复盘表补充结果](results/review-comparison) · [Excel](A股社区情绪与市场脆弱性.xlsx) · [离线浏览](回测结果浏览.html) | 对照样本与便于筛选的汇总表 |

已 fork [社区情绪指数](https://github.com/zane-pku/baoma-xiaobai-sanhu-zhishu) 和 [Vibe AStock](https://github.com/zane-pku/vibe-astock)，可分别查看渠道计分与短线复盘口径。此前的 [A 股交易拥挤度研究](https://github.com/zane-pku/a-share-crowding-research) 提供拥挤定义和构建过程。

## 复跑

1. 安装 `requirements.txt`。本轮记录的点位和指标输入来自 [看板的固定提交](https://github.com/qrq3838/a-share-market-sentiment-dashboard/tree/77f6f14d60d62f0aa8109d3d741b9e5e73733b75/data)。有访问及使用权限时，将 `public-snapshot.json`、`market-profit-effect-snapshot.json` 和 `financing-snapshot.json` 三份文件保存到自己的 `inputs/dashboard`。和 [主样本清单](results/input_manifest.json) 比对 SHA-256。
2. 第二组可选样本自行从 [复盘表固定提交](https://github.com/bulletforyou/AShareMarketReview/tree/1fe70ab06765bfca1a1cabcfd64015384c727152) 准备全表 Excel。同 [补充样本清单](results/review-comparison/input_manifest.json) 比对 SHA-256。
3. 跑下面两条命令。结果目录可以任意替换。将社区历史另按 [数据契约](docs/社区指标与验证协议.md) 接入。

```sh
python -m pip install -r requirements.txt
python scripts/backtest.py --snapshot-dir inputs/dashboard --out outputs/market
python scripts/backtest.py --snapshot-dir inputs/dashboard --review-xlsx inputs/market-review.xlsx --out outputs/review
```

源数据版权以各自条款为准。表格中的收益为指数点位的事件研究结果，实际交易还需指定产品、成本、入场时点和执行约束。
