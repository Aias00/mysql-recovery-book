# 一手来源核查

全文缓存只用于作者核查，已忽略，不随书发行。以下为原创释义及实际下载SHA-256。

## R01 Using mysqldump for Backups

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/using-mysqldump.html

获取：2026-10-21；9217 bytes；SHA-256 `b709140fa3f7698adf0393ec572a1768ceb6bae6d8223f40f66a4944aa598019`。

释义：逻辑备份恢复需执行SQL；一致性、账户与恢复目标需要单独验证。

## R02 mysqldump — A Database Backup Program

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/mysqldump.html

获取：2026-10-21；247941 bytes；SHA-256 `8851ec12f70deeabda71289b50b867a2929ce0b68d3b3b5bdd81787cdffa3dfa`。

释义：single-transaction限事务表快照，source-data记录复制坐标，DDL并发有额外限制。

## R03 Point-in-Time Recovery Using Binary Log

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/point-in-time-recovery.html

获取：2026-10-21；5060 bytes；SHA-256 `7b4d9a6f018d0119089e344946df2c84dd65ace396ede4baa782ea40696fbc8e`。

释义：完整备份之后用二进制日志进行时间点恢复，必须具备连续日志。

## R04 Point-in-Time Recovery Using Event Positions

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/point-in-time-recovery-positions.html

获取：2026-10-21；14362 bytes；SHA-256 `4e6a691730d0ec03cc736581553790e01d2993d6a0fdb3a9236a0df0fcfe3a8f`。

释义：以事件位置标识恢复范围，先检查事件再选择排除边界。

## R05 Replication with Global Transaction Identifiers

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-gtids.html

获取：2026-10-21；9522 bytes；SHA-256 `cfcc065db9a6621ff943e87a1ac1fa7dea2c4799077f64b8a6398c216acde633`。

释义：GTID识别已提交事务，自动定位并不证明业务数据相等。

## R06 Setting Up Replication Using GTIDs

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-gtids-howto.html

获取：2026-10-21；16415 bytes；SHA-256 `ff71338a2b0845b3bb3d9ee2c15ce696a80ffbf80df2fa0ef8699046d5af3688`。

释义：实例身份、GTID配置、账户、源配置与一致初始数据是建立复制的条件。

## R07 Replication Threads

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-threads.html

获取：2026-10-21；8041 bytes；SHA-256 `90f7b3ecea73b749f1d433df870aeef1c116118512dc23f5c9dfe2a172b80f3f`。

释义：接收与应用线程进度不同，接收日志不等于事务已执行。

## R08 Switching Sources During Failover

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-solutions-switch.html

获取：2026-10-21；15599 bytes；SHA-256 `ed0d10e835c28e2eff2b18719201f9febf1cb25defd6ea05c5a55aa3ff26a488`。

释义：切换需要选择副本、处理位置与数据差异，防止旧源继续提供写入。

## R09 mysqlbinlog — Utility for Processing Binary Log Files

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/mysqlbinlog.html

获取：2026-10-21；165246 bytes；SHA-256 `c07e3150d9cd3790ed8dd0137d59a9f536b2ecfeeae5d2aec891ce95d615a1f5`。

释义：回放使用可执行输出，位置与GTID选项需结合服务器状态分析。

## R10 SHOW REPLICA STATUS Statement

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/show-replica-status.html

获取：2026-10-21；51993 bytes；SHA-256 `f67613deee8956092ddf13b5d003f7d8acd3660fc39b19a3e6e1ea6e0917db32`。

释义：延迟和线程状态有解释条件，不是业务恢复成功的充分条件。

## R11 Backup and Recovery Types

https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/backup-types.html

获取：2026-10-21；19704 bytes；SHA-256 `250b4296a31e6a67bacc79b81ef7bcaf04df88621d4ab0ae84977b692f83137b`。

释义：逻辑/物理、完整/增量和在线/离线描述不同维度。
