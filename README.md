# MySQL 备份、复制与恢复演练

从数据保护到故障切换。作者 **Aias00**，个人原创，保留所有权利。

本书用一套订单、账务分录与账户余额贯穿18章，重点回答恢复后哪些事务确实存在。四个真实MySQL实例完成并发一致快照、独立恢复、事务边界binlog回放、GTID异步复制、暂停追平、已确认事务丢失与隔离旧主后的手工提升。

- 在线阅读：https://aias00.github.io/mysql-recovery-book/
- EPUB：https://aias00.github.io/mysql-recovery-book/downloads/mysql-recovery-book.epub
- 实验：`python3 lab/run.py --evidence evidence/runtime.json`，见 [lab/README.md](lab/README.md)。
- 一手来源与下载指纹：[research/sources.md](research/sources.md)。

GitHub Actions使用真实Docker MySQL，所有10个场景必须成功；EPUB、静态网页与完整实验ZIP由同一版本生成。实验ZIP在解压后的独立目录再次运行真实四实例实验。最终交付证据见DELIVERY.md。

阅读器默认浅色，保留优化深色、字号调整、搜索、目录与移动端无JavaScript阅读。源码包含原生SVG封面与共享样式，不分发第三方文档全文缓存。
