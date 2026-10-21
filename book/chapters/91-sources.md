# 附录B：一手来源与版本边界

本书以Oracle发布的MySQL 8.4 Reference Manual为主要语义依据。以下条目在2026年10月21日真实下载，文件字节数与SHA-256保存在下载区sources.json以及仓库research/sources.md。全文缓存只用于核查，不随书或实验包公开分发。下面是作者自己的归纳，不是复制官方正文。

1. [Using mysqldump for Backups](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/using-mysqldump.html)：逻辑备份与SQL恢复的基本路径。
2. [mysqldump](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/mysqldump.html)：single-transaction、source-data、set-gtid-purged等选项及限制。
3. [Point-in-Time Recovery](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/point-in-time-recovery.html)：完整备份与连续日志组成恢复链路。
4. [Recovery Using Event Positions](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/point-in-time-recovery-positions.html)：用事件位置确定恢复区间。
5. [Replication with GTIDs](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-gtids.html)：事务身份、执行集合与自动定位。
6. [Setting Up Replication Using GTIDs](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-gtids-howto.html)：实例与初始化前提。
7. [Replication Threads](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-threads.html)：接收和应用的职责差异。
8. [Switching Sources During Failover](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/replication-solutions-switch.html)：切换过程与源选择注意事项。
9. [mysqlbinlog](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/mysqlbinlog.html)：事件解析、位置参数与可执行回放。
10. [SHOW REPLICA STATUS](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/show-replica-status.html)：线程、错误与延迟字段的含义。
11. [Backup and Recovery Types](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/backup-types.html)：备份分类所表达的不同维度。

实际数据库是固定官方镜像中的8.4.11，工具mysqlbinlog来自Oracle固定8.4.11客户端RPM，摘要见实验代码与validation.json。在线手册可能更新，本书以所获取版本和真实实验交叉核查。一次实验没有覆盖的配置或产品能力，会明确作为扩展讨论，不用官方文档存在来代替实际运行证据。
