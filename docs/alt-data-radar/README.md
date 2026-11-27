# Mangrove 另类数据指标雷达

核验日期为 2026-11-27。研究范围从投资者表达扩展到经济活动、物流瓶颈、开发者采用、新闻扩散与原始披露。表中的计算是 Mangrove 候选研究口径，项目仓库提供数据处理和方法参考。

## 核心项目

| 工具 | 可复用部分 | 拟接入 Mangrove | 数据可得性 |
|---|---|---|---|
| [BlackMarblePy](https://github.com/zane-pku/blackmarblepy) | NASA 瓦片下载、投影和分区统计。MIT 加 World Bank IGO Rider | 宏观／实体活动、行业／产能区域跟踪 | NASA VNP46A3 为月度产品。下载需 Earthdata 凭据。产品 QA、瓦片发布日期和数据再分发条件单独核对。[NASA 产品目录](https://cmr.earthdata.nasa.gov/search/site/collections/directory/LAADS/gov.nasa.eosdis) |
| [AISdb](https://github.com/zane-pku/AISdb) | 航迹解码、时空查询、航迹分段、网格化。AGPL-3.0 | 供应链／港口吞吐和拥堵 | 需单独取得 AIS 数据。NOAA AccessAIS 可用于美国沿海样本，记录按季度增加。全球研究先对照 IMF PortWatch 已发布聚合。拟复用的处理方式与代码许可独立评估。[NOAA AccessAIS](https://coast.noaa.gov/accessais/) · [IMF PortWatch](https://portwatch.imf.org/) |
| [OpenDigger](https://github.com/zane-pku/open-digger) | OpenRank、贡献者、新增贡献者和注意力月度数据。Apache-2.0 | 科技产业／AI 软件生态、人气与采用分栏 | 官方导出指南给出 GitHub/Gitee 指标。项目代码活跃与任一仓库的静态导出及时性是两回事，须对每条序列核对末期与版本。[指标目录](https://open-digger.cn/en/docs/user_docs/metrics/metrics_usage_guide) |
| [GDELT DOC API Python 客户端](https://github.com/zane-pku/gdelt-doc-api) | 查询过滤、文章列表、新闻份额与情绪时间线。MIT，固定版本是较早的轻量客户端 | 另类数据／全球产业、政策与供应链新闻专题 | DOC 适合查询验证，窗口和速率按模式确认。长历史用 Events/Mentions 或 GKG 发布分片，固定实体与主题定义。原文权利归发布方。[GDELT 原始数据](https://gdeltproject.org/data.html) |
| [EdgarTools](https://github.com/zane-pku/edgartools) | Form 4 交易和报告人解析。MIT | 公司事件／美股高管与董事交易 | SEC 公共档案。以披露可见时点进入样本，Form 4/A 以新版本追加。表内 P 代码含公开市场或私下购买，单靠代码无法区分两者。[SEC Form 4](https://www.sec.gov/files/form4.pdf) |

### 其他保留来源

- [StatsWiki](https://github.com/thepriben/StatsWiki) 提供 Wikidata 和页面流量的分区归档示例。指标优先走 Wikimedia 官方逐页接口，固定语言站、页面重定向和 user 流量口径。可作为社区与新闻关注的独立旁证。[Wikimedia Analytics API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/)
- [USAspending API](https://github.com/fedspendingtransparency/usaspending-api) 作为美股政府订单数据来源。先用官方 API 检索，记录授标交易级增减额、历史修订和母子公司映射。上限金额、已承诺义务和实际支出分别存储。[USAspending 官方 API](https://api.usaspending.gov/)
- [Neptune](https://github.com/xang1234/neptune) 包含港口停靠识别的做法，目前所核验的 GitHub 元数据和文件树未发现明确代码许可证。可阅读其方法描述，海运方向选了许可明确的 AISdb。

## 三个优先试点

数据就绪程度有所不同。OpenDigger 新端点已有两条数据样本验证，GDELT 目前验证到批量发布索引，遥感和 AIS 分别需要区域数据与质量检查。详见采源记录。

### 1. 新闻关注开始跨出单一来源了吗

预设三个研究主题，例如存储涨价、集运扰动、创新药授权。每个主题冻结实体别名、排除词及媒体语言组。每天以最早可见时间收录，同一事件的通讯社转载合为一簇，事件簇保留来源分布。输出主题报道份额和来源广度，避免总参照集变化导致假异动。

验证先比较基准新闻量和加上扩散率后的辨识度，标签可用后续有证据支持的供应链事件或公告。用于收益研究时，再检验控制过去涨幅、波动、财报日和已知新闻事件之后的边际变化。近期看板应同时展示有效来源数及代表证据。

### 2. 开源生产力增长来自更多维护者，还是只来自更多围观

先固定若干开源主题，例如推理框架、向量检索、数据库。每个主题冻结仓库成员和版本。在同一仓库比较活跃贡献者、新贡献者和公开注意力变化。合成时对单仓库等权，另做剔除最大仓库、迁仓、批量导入、机器人和活动月的对照。

不把星标、新仓库数或 OpenRank 直接折算为企业营收。先用版本发布频率、后续合并 PR 数或次季贡献者留存做领先检验，再评估是否有业务可解释的上市公司敞口。一个依赖库被多家公司采用时保留多对多关系和生效日。

### 3. 工业区域与港口活动能否跟踪基本面

夜光采用固定工业区边界、同一 NASA 产品及质量标记，计算可比较像元中位数的同比与匹配对照。港口用固定货运港、泊位与锚地边界，计算船舶停靠、等待与覆盖。先把同地春节、季节性、停电、台风、区域接收变化列成对照。高滞后的公开 AIS 批次适合方法回放，经验证的及时聚合才适合看板。

港口等待时间同时受货量、泊位效率、天气和劳资事件影响。与货船进港数量、吞吐统计和航运价格同屏看。夜光与工业增加值、用电量或产能利用率对照，检验相较季节基线是否降低误差。

## 统一归档与验证

- 每条数据保留 provider、指标版本、scope、period、event_time、available_at、采集时间、修订序号、source_url、coverage 及 missing_reason。公告和 AIS 原始点位只保留必要的证据定位。
- 可见时间使用发布或在研究系统中首次采集到的时间，月度指标以真实发布时点进入下一可交易区间。事后能下载到历史，与当年当日能够看到同一版本是两个问题。可见时间缺失时只用于描述性研究。
- 市场事件用处置适当的标的做独立回测。常规观测对照季节性和过去收益、波动及流动性。夜光、港口和订单优先用产出、吞吐或后续订单作为验证目标。Form 4 匹配同市值、行业、流动性和公告状态的公司。留出样本保留扩散方向、无增量和覆盖不足的结果。
- 展示格式建议使用三部分：变化值与历史位置、覆盖与时效、原始证据。各类信号保留原始量纲。数据发布规律和可信度不同，暂缓汇总成单一分数。

[因子登记表](factor-catalog.csv) · [Fork 验证清单](forks.json) · [实际采源探测](source-checks.md)

