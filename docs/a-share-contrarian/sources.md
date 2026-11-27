# 采源与开源项目

## A 股专用开源参考

| 项目 | 复用点与状态 |
|---|---|
| [CNEquity fork](https://github.com/zane-pku/CNEquity) | Apache-2.0。核对到 `dd6881ad7a3e8fce4ed4314711c99f6251ec06f8`。借鉴历史股票池、行级来源、深沪历史分层和涨跌停数据。按数据集逐条核对覆盖和许可 |
| [AKShare fork](https://github.com/zane-pku/akshare) | MIT。核对到 `2864afc111ae6ffdbfd64673f4ba649af5a96926`。参考上交所期权每日统计解析及股吧人气入口。代码许可不自动授予上游数据分发权 |
| [Vibe AStock，已有 fork](https://github.com/zane-pku/vibe-astock/tree/mangrove/shortline) | 参考昨天涨停今天表现、封板质量、1进2晋级和收盘定稿归档 |
| [社区情绪指数，已有 fork](https://github.com/zane-pku/baoma-xiaobai-sanhu-zhishu/tree/mangrove/community-attention) | 参考平台等权、中性收缩和缺测区分，可为实际提问、追涨、恐慌提供采样结构。公开项目不含真实长样本 |
| [宽基 ETF 份额参考](https://github.com/wwww1998/national-team-etf-flow/tree/c3b08d5376403e87a393b1a1fab8e628aded9ce9) 与 [口径变化说明](https://github.com/wj624/national-team-etf-flow/tree/9d67621890b784495f2f3a42c7f40d3f30c50b46) | GitHub 未列明确许可证。保留线上出处，复算使用 `_broad_shares_cache.json` 中固定的510300。尤其借鉴其对篮子变更和源数据延迟的记录。计算不复制代码，也不分发原缓存 |
| [股吧量化参考](https://github.com/meignot/Guba-Sentiment-Quant) | README 与代码入口可借鉴取样设计。未见明确开源许可，只作来源线索。热门排序页面无法从当前快照还原历史首见帖子 |

## 实测输入与证据

- 主行情采用 [原研究固定快照](https://github.com/qrq3838/a-share-market-sentiment-dashboard/tree/77f6f14d60d62f0aa8109d3d741b9e5e73733b75/data) 三个文件。需在有权使用时保存为 `public-snapshot.json`、`market-profit-effect-snapshot.json`、`financing-snapshot.json`。
- 涨跌停辅助输入来自 [市场复盘表固定提交](https://github.com/bulletforyou/AShareMarketReview/tree/1fe70ab06765bfca1a1cabcfd64015384c727152)。前期已将2,812行日期、上证指数和创业板涨跌对齐参考行情。逐股涨跌停状态尚未双源复核。
- ETF 数据一期覆盖2021-11-01至2026-11-26，原缓存内的510050、510300、510500、512100均有1,231个份额观测。简单相邻观测绝对变化超过15%的次数分别为4、0、3、34，查验前不当作真实资金冲击。当前检验只用与价格对齐的510300，不包含当前池事后汇总。
- [上交所期权每日统计](https://star.sse.com.cn/assortment/options/date/) 的查询接口已实测可读。2024-06-26、2026-10-12及2026-11-23三个样本日均返回5个标的的统计。独立复算 510050、510300、510500 各自的成交量PCR和持仓量PCR，结果见 [交易所样本检查](results/option-check.json)。PCR比率使用张数相除。可提取字段，未做期权历史回测。
- [上交所投资者统计月报](https://star.sse.com.cn/aboutus/publication/monthly/investor/) 与 [上交所统计年鉴](https://www.sse.com.cn/aboutus/publication/yearly/documents/c/10801255/files/02acb566841a48f0b2ca8941c73f4541.pdf) 对应A股开户数。历史月份标签和发布时点应分别录入，避免用月末事后回填。

## 近期研究如何用于本项目

- [华泰证券 2026-03《A股情绪温度计》作者发布稿](https://finance.sina.com.cn/wm/2026-03-18/doc-inhrkfux7605158.shtml) 对比贪婪与恐慌端，指出认沽持仓可由上涨期间套保推动。本项目据此要求成交、持仓及价格环境同时保留。
- [渤海证券 2026-10《A股行业情绪的监测》报告摘要](https://stock.finance.sina.com.cn/stock/go.php/vReport_Show/kind/strategy/rptid/846588693204/index.phtml) 把相对全A的事件检验放到行业层级，并比较两端的不对称性。这里借鉴分层与期限设计，宽基试验不等于复刻行业结论。
- [Salience and return reversals: Evidence from China](https://www.sciencedirect.com/science/article/abs/pii/S0927538X25003749) 使用 A 股股吧发帖量研究注意力与后续收益。借鉴股票层关注度的基准控制，新闻注意力和方向在输入层单独保存。
- [系统管理学报 2026 年 A 股关注度研究](https://coaa.istic.ac.cn/openjournal/periodicalArticle/0120260401706715) 区分市场、行业和个股，并报告三层后续表现不同。社区信号应按标的层级回测，不能把个股结论套到指数。

采购本地样本时以原始证据、实际可得时间与核验记录为准。本文数据文件仅包含方法、统计和三日字段复算。
