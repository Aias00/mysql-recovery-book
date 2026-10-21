# MySQL 恢复实验

需要 linux/amd64、Python 3.12+、Docker Engine、可下载固定官方 MySQL 镜像，约 2 GB 可用内存与 3 GB 磁盘。工具RPM固定为x86_64，ARM原生环境未验证；本书正式证据来自 Ubuntu 24.04 GitHub Actions，不把不同平台结果混为一谈。

```sh
python3 lab/run.py --evidence evidence/runtime.json
```

程序创建带随机前缀的私有 bridge network 和四个实例，端口不发布到宿主机，使用教学专用口令，完成后只删除本次记录的容器（含匿名卷）及网络。不会执行 Docker prune。遇异常不跳过测试，返回非零，证据 status 为 FAIL；进程被强杀则需按本次随机前缀手工清理其资源，不能清理其他项目。

10个场景必须全部 PASS：GTID复制建立、写入期间的一致快照、干净基线恢复、事务边界PITR、缺失日志不可达到目标、误删同样复制、应用暂停再追平、未隔离拒绝提升、隔离后手工提升并观测已确认事务丢失、返回旧主断网且只读。

业务写入由ledger_app执行，仅具有ledger.*的SELECT/INSERT/UPDATE/DELETE，没有SUPER或CONNECTION_ADMIN。提升显式关闭super_read_only和read_only并检查0/0，再用该普通业务账号提交与查询。角色管理、备份和核对使用root。

事务业务不变量：账户余额=100000+分录delta之和；订单与分录逐行一一对应；分录金额等于订单金额相反数。恢复目标还比较全部有序订单、余额和分录总和的SHA-256，不能仅用行数或线程状态判定成功。

RTO仅计本次docker stop发起到新主成功提交并查询确认的手工流程，排除故障发现、路由、DNS与客户端重试。RPO报告实际缺失事务ID和数量；观察窗口是停止复制后相邻客户端观测间隔，不是线上RPO保证。

使用的逻辑备份参数为 `--single-transaction --source-data=2 --set-gtid-purged=OFF --databases ledger`，实验只针对InnoDB事务表且没有并发DDL。恢复目的不是直接加入原复制拓扑，不能照搬此GTID选项到生产副本初始化。回放前FLUSH封口并复制真实日志到任务私有归档，记录字节与hash，停止源实例后用无网络工具容器只读挂载归档。缺失日志负例临时移走实际必需文件并验证基线未变化。回放使用同一实际binlog文件中的开始位置与误删事务之前的提交结束位置，生产跨文件日志需逐文件验证连续性。

每次运行均重新拉起干净实例，固定镜像digest，报告实际VERSION和变量。不包含自动选主、代理改路由、物理备份、跨地域容灾、故障磁盘持久性或生产密钥管理。
