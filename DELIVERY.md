# 交付记录

状态：完成。作者Aias00，个人版权保留。

- [在线阅读](https://aias00.github.io/mysql-recovery-book/)
- [EPUB](https://aias00.github.io/mysql-recovery-book/downloads/mysql-recovery-book.epub)
- [Release v1.0.0](https://github.com/Aias00/mysql-recovery-book/releases/tag/v1.0.0)
- [完整成功CI 39598252259](https://github.com/Aias00/mysql-recovery-book/actions/runs/39598252259)
- 产品源码：`c0681a952fe762a0abf17e07348ebee029b692ef`

正文18章、排除代码后25315中文汉字，前言、3个原创附录及生成代码附录，共23阅读单元/4附录。独立全文审稿见[research/independent-review.json](research/independent-review.json)，公开交付核对见[research/publication-audit.json](research/publication-audit.json)。

## 实际实验

MySQL8.4.11；镜像`mysql@sha256:0f51e63e537a1f176423fa03ef559aabe6fa4372a53160a44bc7e75da7d15364`。独立mysqlbinlog8.4.11来自官方RPM，下载SHA-256为`2f1e8317c557363dd1554b29a9f6d69403802dc623fe72d9995f20f542771bb1`。普通业务账号ledger_app只有ledger.* SELECT/INSERT/UPDATE/DELETE，无SUPER、CONNECTION_ADMIN或全局管理权限。root只负责角色、备份和管理核对。

同一CI中源码与独立ZIP各重新创建四个真实实例，各10个场景全部PASS，没有跳过。包括GTID建立、并发一致快照、干净基线恢复、真实缺失必需归档负例、事务边界PITR、误删同步、应用暂停追平、旧主仍运行时拒绝提升、隔离后真实异步丢失、返回旧主断网只读。源码报告见[book/validation.json](book/validation.json)，两份原始报告可从该CI的mysql-recovery-runtime artifact下载。

本次导出源计数3→6，恢复快照4笔订单，写入器最终121笔。PITR从mysql-bin.000004的198回放到1253，只读归档挂载且无网络工具容器执行，源已停止。恢复123笔订单、余额99740、分录和-260，与目标完整有序行/摘要一致；误删和订单3001被排除。实际归档7226字节，SHA-256 `c5a68925f2c57a8293d37838636791592066bd22ff87918008bfa939877ca9ce`。

提升前副本与返回旧主均由ledger_app真实写入并得到ERROR1290，只读拒绝无副作用。提升同时关闭read_only与super_read_only并检查0/0，再由ledger_app提交和查询新主订单6001。订单5001是旧主已确认而未复制的真实丢失事务；实际RPO缺失1笔，观测窗口0.049秒，手工RTO 10.624秒。RTO从发起停止旧主到新主业务提交及完整数据核对，不含故障发现、路由、DNS或客户端重试。两次docker stop均先给10秒宽限，实际退出码137，报告保留该事实；未把它称为优雅退出或断电持久性测试。

## 公开产物一致性

Release资产直接来自成功CI的book-downloads，与Pages部署使用同次工件。随后匿名GET下载Pages与Release EPUB，三份字节完全一致：97994 bytes，SHA-256 `c794fbfa88b1b9bb775e80ce33723a050e7b11ff2e05ea2462a5ae41dd7830a0`。

公开23篇章节全文与原稿/Pandoc独立渲染内容一致，完整Markdown一致，公开ZIP与CI一致且实验代码与源码一致，公开validation.json与CI一致。对实际公开下载EPUB运行EPUBCheck5.4.0：0fatal/0error/0warning。

公开阅读器全部23章在320/390px与无JavaScript情况下无横向溢出，目录翻页、浅色默认、深色切换与共享主题、搜索、字号持久化、禁用storage及下载均通过Playwright。390px深色截图已人工查看。

## 清楚的边界

单机私有Docker bridge、教学账本、受控手工切换；无自动HA、生产代理改路由、跨地域RPO/RTO、物理备份或故障磁盘持久性证明。异步丢失被真实观测，未宣称零丢失。返回旧主保留差异且不自动重入。所有清理只针对本次随机命名资源，不执行全局prune。

本记录与canonical运行报告通过[skip ci]提交回填，不重建或替换既有发布资产。文档路径不参与产品构建触发。后续产品变更应发布新补丁版本。
