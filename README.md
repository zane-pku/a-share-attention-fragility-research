# A 股情绪、拥挤度与反向指标

本仓库是 Mangrove 的指标研究入口。当前优先研究**财经博主、入场问询、话题破圈，以及盘面有没有承接**。指标的定义、证据阶段、行情对照和接入位置可以从同一目录进入。

**[进入统一研究目录](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-behavior)**

| 你要找什么 | 去哪里 |
|---|---|
| 先看有趣的行为指标 | [精选指标与 Excel](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-behavior) |
| 过去有哪些信号跑过、效果怎样 | [反向事件检验](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-contrarian) · [早期市场脆弱性回测](docs/回测报告.md) |
| 各个研究库和分支怎么分工 | [仓库与分支](https://github.com/zane-pku/a-share-attention-fragility-research/blob/mangrove/a-share-contrarian/docs/a-share-behavior/仓库与分支.md) |
| 找社区计算原型或协议 | [社区指标与验证协议](docs/社区指标与验证协议.md) · [早期因子表](docs/factors.csv) |
| 找行情数据或开源参考 | [开源项目与证据](docs/开源项目与证据.md) · [博主与社区 GitHub 项目](https://github.com/zane-pku/a-share-attention-fragility-research/blob/mangrove/a-share-contrarian/docs/a-share-behavior/GitHub项目.md) |
| 找可运行的 Mangrove 离线接入样例 | [市场风险适配](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/market-risk) |

## 复算早期市场检验

使用 [固定行情快照](https://github.com/qrq3838/a-share-market-sentiment-dashboard/tree/77f6f14d60d62f0aa8109d3d741b9e5e73733b75/data) 中有权使用的三份 JSON。文件名与 SHA-256 见 [输入清单](results/input_manifest.json)。辅助复盘表及哈希见 [补充样本清单](results/review-comparison/input_manifest.json)。

```sh
python -m pip install -r requirements.txt
python scripts/backtest.py --snapshot-dir inputs/dashboard --out outputs/market
python scripts/backtest.py --snapshot-dir inputs/dashboard --review-xlsx inputs/market-review.xlsx --out outputs/review
```

[结果工作簿](A股社区情绪与市场脆弱性.xlsx) · [离线结果页](回测结果浏览.html)
