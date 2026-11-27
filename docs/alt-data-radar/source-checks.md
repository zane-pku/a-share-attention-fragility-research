# 采源核验记录

核验时间为 2026-11-27 北京时间 18:00–18:03。以下记录回答端点是否可访问、样本覆盖到哪。区间长度是本次测试端点返回的月份数，单个样本不代表全体仓库。

| 来源 | 实测 | 接入判断 |
|---|---|---|
| [OpenDigger 新端点 · PyTorch OpenRank](https://oss.open-digger.cn/github/pytorch/pytorch/openrank.json) | HTTP 200，123 个月份键，2016-08 至 2026-10 | 可尝试月度试点。静态数据的历史首见时间和修订记录需另行归档 |
| [OpenDigger 新端点 · PyTorch 贡献者](https://oss.open-digger.cn/github/pytorch/pytorch/contributors.json) | HTTP 200，113 个月份键，2017-01 至 2026-10 | 与 OpenRank 可在共同月份比较。单条序列支持技术核验 |
| [OpenDigger 旧端点](https://oss.x-lab.info/open_digger/github/pytorch/pytorch/openrank.json) | HTTP 200，94 个月份键，最后为 2024-10 | 会产生成功响应但数据陈旧。新配置以作者现行文档的域名为准 |
| [GDELT 批量发布索引](https://data.gdeltproject.org/gdeltv2/lastupdate.txt) | HTTP 200，解析到 3 条文件列表，均有大小、校验值、链接 | 证明发布索引可读，待实际采样核对分片首见时间、重复报道与主题覆盖 |
| [GDELT DOC](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts//) | 本机集运主题文章请求发生 TLS 握手超时 | 暂不依赖它作为上线或历史检验的唯一数据通道 |
| [Wikimedia 查阅量](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/) | 两次指定样本请求均在 TLS 握手阶段超时 | 保持观察，接口未验证成功，不能用作当前已接通序列 |
| [NASA CMR 产品元数据](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=VNP46A3&version=2&page_size=3) | HTTP 200，核对产品 VNP46A3 v2 | 仅验证元数据；瓦片下载、区域覆盖和 QA 复算仍待凭据和样区 |
| [SEC Form 4 数据说明](https://www.sec.gov/files/insider_transactions_readme.pdf) · [公开更正示例](https://www.sec.gov/Archives/edgar/data/1137204/000149430312000005/primary_doc.xml) | 核对结构化披露说明和改变交易代码的 Form 4/A 实例 | 先保存原版和更正版的可见时间；当前未运行历史回测 |
| [NOAA AccessAIS](https://coast.noaa.gov/accessais/) | 核对公开范围和按季度更新规则 | 获取方法和批次用途已明确，当前未下载轨迹或计算港口指标 |

五个 GitHub fork 均核对了真实父仓库、默认分支提交和公开性。数据可得性按来源逐条核验，与代码开源许可分开。

