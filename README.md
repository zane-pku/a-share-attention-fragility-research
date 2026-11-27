# A 股行为情绪、拥挤度与反向指标

研究 **财经博主何时开始追热点、普通讨论何时变成「怎么买」，以及讨论升温后市场有没有真实承接**。仓库汇总 A 股行为指标、行业拥挤度、短线接力和市场风险的计算口径及验证结果，可作为 Mangrove 投研平台的指标研究入口。

[宝妈指数与同类指标](#宝妈小白散户社区情绪指数) · [精选与 Excel](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-behavior) · [历史事件检验](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-contrarian)

## 宝妈·小白·散户社区情绪指数

**宝妈指数是本研究的核心参考。** 上游项目把公开社区文本按六个信号聚合。同一条文本可以含有追涨、提问或恐慌表达。三条曲线是不同权重的观察视角，计算只基于文本和可见样本，无需推断发帖者的婚育、性别、职业或投资水平。来源为 [上游 README](https://github.com/xzrd021/baoma-xiaobai-sanhu-zhishu/blob/752885b352cd49f8b24663d00a68120c2f43add9/README.md#三个分指数权重) 和 [本账号 fork](https://github.com/zane-pku/baoma-xiaobai-sanhu-zhishu)。

| 六项信号的权重 | 宝妈指数 | 小白指数 | 散户指数 |
|---|---:|---:|---:|
| 情绪方向 | 25% | 15% | 30% |
| 追涨冲动 | 25% | 20% | 20% |
| 新手提问 | 15% | 30% | 5% |
| 情绪强度 | 15% | 15% | 15% |
| 讨论活跃 | 15% | 15% | 20% |
| 板块扩散 | 5% | 5% | 10% |

**怎么算。** 上游对每个渠道和交易日校准，再在渠道内合并固定入口。东方财富、新浪、同花顺和淘股吧各占 25%，最近三个交易日按 50%、30%、20% 合成。热门流可以提供文本证据，严格时序流才可核验声量与零帖。缺测降低覆盖，样本不足的板块不做强制排名。恐慌独立展示。细节以 [固定版本的渠道模型](https://github.com/xzrd021/baoma-xiaobai-sanhu-zhishu/blob/752885b352cd49f8b24663d00a68120c2f43add9/channel_fairness_model.py) 为准。

**怎么看。** 宝妈指数更偏向乐观与追涨表达，小白指数对操作类提问更敏感，散户指数对方向和活跃度权重更高。三条曲线共享底层输入，使用时应避免把它们当成三份独立证据。可以观察「小白提问先升、博主集体看多、盘面承接走弱」是否先后出现。

**实证进度。** 上游公开了代码和脱敏演示。完整的真实长样本需要另行取得。研究库自己的六条社区计算序列采用独立口径，详见 [社区指标协议](docs/社区指标与验证协议.md)。聚合适配见 [社区导出分支](https://github.com/zane-pku/baoma-xiaobai-sanhu-zhishu/tree/mangrove/community-attention)。

## 同类特色指标

| 指标 | 可观察的行为 | 当前证据 |
|---|---|---|
| **网红集体喊多** | 固定财经作者池。每作者、每行业、每交易日最多一次明确方向票，同时记录明确表态与采样覆盖 | 有研究定义，待真实点时历史 |
| **网红追热点迟到** | 记录价格先涨、讨论破圈、作者共识达到阈值三个时间，比较早响应、晚响应和无共识 | 待验证。观察从信号真正可见的日期开始 |
| **价格没跌，网红先退潮** | 价格仍近高点时，覆盖合格的财经作者群看多比例由高位下降 | 待验证。停更和采集失败单独保留 |
| **大家开始问怎么买** | 开户、买入和交易规则问询的占比。解套和补仓另计 | 有候选定义，仍需授权样本 |
| **题材破圈** | 某主题在多个固定渠道同时出现异常原创讨论，转载和切片回到同一内容簇 | 有计算原型与待测变体 |
| **昨日涨停，今天集体被套** | 昨日涨停名单在今日的收益中位数和跌超5%比例，分首板、连板与交易制度 | 有短线数据参考。仍需可追溯的长历史 |
| **ETF 越跌越申购** | 标的下跌而固定 ETF 的份额明显增加，与上涨时同等强度申购对比 | 510300 已做历史初筛，两组20日匹配差接近 |
| **冷西西韭菜50** | 把价格追涨、换手、龙虎榜注意力和特大单流量组合成每日 Top50，按次日到再下一日开盘等权计理论收益 | 第三方公开方法，本库作为纯行情基准。[Bagholder 50 fork](https://github.com/zane-pku/bagholder50) |

另一项目 [mom-index-lite](https://github.com/EastSunWong/mom-index-lite/tree/0c68a455b60a973c6e31ea7c8c335c868ba346f2) 可参考问询、求助、提及博主等表达分类。其公开示例含模拟小红书数据，README 表明尚未完成历史回测。项目不是上面的四渠道社区指数。

## 指标目录与证据

[统一研究目录](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-behavior) 收录 **13 项精选行为指标、88 条底层与事件口径、11 个指标家族**。Excel 从精选开始，后面可按研究角色、家族、观察层级和证据阶段筛选。上游三条特色总指数的权重单独在首页和研究目录说明。

| 角色 | 家族 | 想回答的问题 |
|---|---|---|
| 行为主线 | 博主共识、入场问询、跨平台扩散 | 谁在表达什么，话题是否扩散 |
| 交叉验证 | 讨论和交易承接、短线接力、ETF融资与持仓、开户与发行 | 围观有没有变成市场参与 |
| 行情基准 | 价格与宽度、成交拥挤与流动性、衍生品与风险偏好、市场状态 | 在类似行情下，行为信息是否增加解释力 |

已完成的固定历史检验放在 [A 股反向指标研究](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-contrarian) 和 [早期市场脆弱性报告](docs/回测报告.md)。研究记录区分「历史初筛」「计算或字段核验」「已有原型，缺历史」「待验证」。样本外回报、事件次数与价格回撤分别展示。

## 怎么从研究走到平台

1. **先冻结口径与时间。** 按市场、行业或个股分层。价格上涨、话题扩散、作者共识和方向回落各记录自己的首次可见时间。重复转载合并，无法判断留空。
2. **再做对照。** 以相近过去收益、波动和公告环境的标的为对照，报告 5、20、60 日收益与回撤。围观量、情绪方向和交易行为分别入模。
3. **接适配，再验收。** 指标携带稳定 ID、口径版本、覆盖率与可见时间。已实现的 [市场风险离线适配](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/market-risk)、[行业拥挤度导出](https://github.com/zane-pku/a-share-crowding-research/tree/mangrove/sector-crowding) 和 [短线接力导出](https://github.com/zane-pku/vibe-astock/tree/mangrove/shortline) 可作接入参考。完整分工见 [仓库与分支](https://github.com/zane-pku/a-share-attention-fragility-research/blob/mangrove/a-share-contrarian/docs/a-share-behavior/仓库与分支.md)。

## 复算与来源

- **市场历史检验。** 从 [固定行情快照](https://github.com/qrq3838/a-share-market-sentiment-dashboard/tree/77f6f14d60d62f0aa8109d3d741b9e5e73733b75/data) 准备三份有权使用的 JSON。文件名与 SHA-256 见 [输入清单](results/input_manifest.json)。补充复盘表的出处和哈希见 [辅助样本清单](results/review-comparison/input_manifest.json)。

```sh
python -m pip install -r requirements.txt
python scripts/backtest.py --snapshot-dir inputs/dashboard --out outputs/market
python scripts/backtest.py --snapshot-dir inputs/dashboard --review-xlsx inputs/market-review.xlsx --out outputs/review
```

- **社区分项。** 按 [社区输入说明](docs/社区指标与验证协议.md) 准备授权聚合 CSV、交易日日历和平台配置，再运行 `scripts/community.py`。
- **资料。** [开源项目及研究证据](docs/开源项目与证据.md) · [行为指标研报与 GitHub 原型](https://github.com/zane-pku/a-share-attention-fragility-research/tree/mangrove/a-share-contrarian/docs/a-share-behavior) · [结果工作簿](A股社区情绪与市场脆弱性.xlsx) · [离线结果页](回测结果浏览.html)

项目内的研究统计可复核，源数据和第三方代码的使用条件分别依原提供方约定。生产看板的接入、刷新和数据授权另行验收。

