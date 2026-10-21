#!/usr/bin/env python3
"""Real, isolated MySQL recovery exercises. Requires Docker; never skips tests."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time

IMAGE = 'mysql@sha256:0f51e63e537a1f176423fa03ef559aabe6fa4372a53160a44bc7e75da7d15364'
PASSWORD = 'recovery-lab-only'


def call(args, data=None, check=True, timeout=180):
    p = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f'{args[0:3]} failed ({p.returncode}): {p.stderr.decode(errors="replace")[-3000:]}')
    return p


class Lab:
    def __init__(self, output):
        self.prefix = 'mysql-recovery-' + secrets.token_hex(6)
        self.network = self.prefix + '-net'
        self.names = []
        self.tmp = tempfile.TemporaryDirectory(prefix=self.prefix)
        self.report = {'status': 'RUNNING', 'image': IMAGE, 'scenarios': [], 'scope':
            'Isolated Linux Docker bridge; teaching data; manual failover; no production routing, automatic HA or cross-region claim.'}
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def sql(self, name, query, check=True):
        return call(['docker', 'exec', '-e', 'MYSQL_PWD=' + PASSWORD, self.prefix + '-' + name,
                     'mysql', '-uroot', '--batch', '--raw', '--skip-column-names', '-e', query],
                    check=check).stdout.decode().strip()

    def feed(self, name, data):
        return call(['docker', 'exec', '-i', '-e', 'MYSQL_PWD=' + PASSWORD, self.prefix + '-' + name,
                     'mysql', '-uroot', '--binary-mode'], data=data)

    def check(self, name, **values):
        self.report['scenarios'].append({'name': name, 'status': 'PASS', **values})
        print('PASS', name, flush=True)

    def start(self, name, server_id):
        full = self.prefix + '-' + name
        call(['docker', 'run', '-d', '--name', full, '--network', self.network,
              '--network-alias', name, '--label', 'aias.mysql-recovery=' + self.prefix,
              '-e', 'MYSQL_ROOT_PASSWORD=' + PASSWORD, '-e', 'MYSQL_ROOT_HOST=%', IMAGE,
              '--server-id=' + str(server_id), '--log-bin=mysql-bin', '--gtid-mode=ON',
              '--enforce-gtid-consistency=ON', '--binlog-row-image=FULL',
              '--innodb-buffer-pool-size=64M', '--performance-schema=OFF'])
        self.names.append(name)
        for _ in range(100):
            try:
                if self.sql(name, 'SELECT 1') == '1':
                    return
            except RuntimeError:
                pass
            time.sleep(1)
        raise RuntimeError('MySQL readiness timed out: ' + name)

    def state(self, name):
        rows = self.sql(name, 'SELECT id,amount,tag FROM ledger.orders ORDER BY id;').splitlines()
        account = int(self.sql(name, 'SELECT balance FROM ledger.accounts WHERE id=1'))
        delta = int(self.sql(name, 'SELECT COALESCE(SUM(delta),0) FROM ledger.entries'))
        entry_count = int(self.sql(name, 'SELECT COUNT(*) FROM ledger.entries'))
        orphan = int(self.sql(name, 'SELECT COUNT(*) FROM ledger.entries e LEFT JOIN ledger.orders o ON e.order_id=o.id WHERE o.id IS NULL OR e.delta<>-o.amount'))
        assert account == 100000 + delta, (name, account, delta)
        assert entry_count == len(rows) and orphan == 0, (name, entry_count, rows, orphan)
        canonical = '\n'.join(rows) + f'\nbalance={account}\ndelta={delta}'
        return {'orders': len(rows), 'balance': account, 'entry_sum': delta,
                'sha256': hashlib.sha256(canonical.encode()).hexdigest(), 'rows': rows}

    @staticmethod
    def order(ident, tag, amount=1):
        assert re.fullmatch('[a-z0-9-]+', tag)
        return (f"START TRANSACTION; INSERT INTO ledger.orders VALUES({ident},{amount},'{tag}'); "
                f"INSERT INTO ledger.entries VALUES({ident},{ident},-{amount}); "
                f"UPDATE ledger.accounts SET balance=balance-{amount} WHERE id=1; COMMIT;")

    def dump(self):
        p = call(['docker', 'exec', '-e', 'MYSQL_PWD=' + PASSWORD, self.prefix + '-source',
                  'mysqldump', '-uroot', '--single-transaction', '--source-data=2',
                  '--set-gtid-purged=OFF', '--routines', '--triggers', '--events', '--hex-blob',
                  '--databases', 'ledger'])
        return p.stdout

    def wait_replica(self):
        gtid = self.sql('source', 'SELECT @@GLOBAL.gtid_executed')
        assert self.sql('replica', f"SELECT WAIT_FOR_EXECUTED_GTID_SET('{gtid}',30)") == '0'
        assert self.state('source') == self.state('replica')
        return gtid

    def promote(self):
        running = call(['docker', 'inspect', '--format', '{{.State.Running}}', self.prefix + '-source']).stdout.strip()
        if running != b'false':
            raise RuntimeError('FENCE_REQUIRED: old primary remains running; promotion refused')
        self.sql('replica', 'STOP REPLICA; RESET REPLICA ALL; SET GLOBAL super_read_only=OFF;')

    def run(self):
        call(['docker', 'network', 'create', '--label', 'aias.mysql-recovery=' + self.prefix, self.network])
        for i, name in enumerate(['source', 'replica', 'restore', 'pitr'], 11):
            self.start(name, i)
        self.report['mysql_version'] = self.sql('source', 'SELECT VERSION()')
        self.report['server_variables'] = self.sql('source', 'SELECT @@gtid_mode,@@enforce_gtid_consistency,@@binlog_format,@@binlog_row_image,@@sync_binlog,@@innodb_flush_log_at_trx_commit')
        self.report['image_inspect'] = json.loads(call(['docker', 'image', 'inspect', IMAGE, '--format', '{{json .RepoDigests}}']).stdout)
        self.sql('source', "CREATE USER 'repl'@'%' IDENTIFIED BY 'replica-lab-only'; GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';")
        self.sql('replica', "CHANGE REPLICATION SOURCE TO SOURCE_HOST='source',SOURCE_USER='repl',SOURCE_PASSWORD='replica-lab-only',SOURCE_AUTO_POSITION=1,GET_SOURCE_PUBLIC_KEY=1; START REPLICA; SET GLOBAL super_read_only=ON;")
        self.sql('source', '''CREATE DATABASE ledger; USE ledger;
            CREATE TABLE accounts(id INT PRIMARY KEY,balance BIGINT NOT NULL) ENGINE=InnoDB;
            CREATE TABLE orders(id INT PRIMARY KEY,amount INT NOT NULL,tag VARCHAR(40) NOT NULL) ENGINE=InnoDB;
            CREATE TABLE entries(id INT PRIMARY KEY,order_id INT UNIQUE NOT NULL,delta INT NOT NULL) ENGINE=InnoDB;
            CREATE TABLE padding(id INT PRIMARY KEY,payload LONGTEXT NOT NULL) ENGINE=InnoDB;
            INSERT INTO accounts VALUES(1,100000);''')
        self.sql('source', self.order(1, 'opening-order', 100))
        # Slow enough for real dump/commit overlap, but padding is never a business invariant.
        self.sql('source', "SET SESSION cte_max_recursion_depth=3000; INSERT INTO ledger.padding WITH RECURSIVE seq AS (SELECT 1 n UNION ALL SELECT n+1 FROM seq WHERE n<2000) SELECT n,REPEAT('x',8192) FROM seq;")
        self.wait_replica()
        self.check('replication-bootstrap', source_equals_replica=True)
        writer_sql = ''.join(self.order(i, 'backup-concurrent') + ' DO SLEEP(0.08);' for i in range(2, 122))
        writer = subprocess.Popen(['docker', 'exec', '-i', '-e', 'MYSQL_PWD=' + PASSWORD,
                                  self.prefix + '-source', 'mysql', '-uroot'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        writer.stdin.write(writer_sql.encode()); writer.stdin.close(); writer.stdin = None
        deadline = time.monotonic() + 15
        while int(self.sql('source', 'SELECT COUNT(*) FROM ledger.orders')) < 2:
            assert time.monotonic() < deadline
            time.sleep(.03)
        before = int(self.sql('source', 'SELECT COUNT(*) FROM ledger.orders'))
        dump_started = time.monotonic()
        snapshot = self.dump()
        dump_seconds = time.monotonic() - dump_started
        after = int(self.sql('source', 'SELECT COUNT(*) FROM ledger.orders'))
        writer_out, writer_err = writer.communicate(timeout=40)
        assert writer.returncode == 0, writer_err.decode()
        source_final = self.state('source')
        assert after > before, ('No observed commits during actual dump', before, after)
        self.feed('restore', snapshot)
        restored = self.state('restore')
        assert before <= restored['orders'] <= after < source_final['orders'], (before, restored, after)
        self.check('consistent-snapshot-under-writes', source_count_before=before,
                   source_count_after=after, restored=restored, final_source_orders=source_final['orders'],
                   dump_seconds=round(dump_seconds, 4), dump_sha256=hashlib.sha256(snapshot).hexdigest())
        # A second quiet baseline makes the exact recovery target independently unambiguous.
        self.sql('source', 'FLUSH BINARY LOGS')
        baseline = self.dump()
        pos = re.search(rb"SOURCE_LOG_FILE='([^']+)', SOURCE_LOG_POS=(\d+)", baseline)
        assert pos, 'No source coordinates in dump'
        filename, startpos = pos[1].decode(), int(pos[2])
        self.feed('pitr', baseline)
        assert self.state('pitr') == source_final
        self.check('clean-baseline-restore', baseline=source_final, binlog=filename, start_position=startpos)
        self.sql('source', self.order(2001, 'keep-before-delete', 17))
        self.sql('source', self.order(2002, 'keep-second', 23))
        target = self.state('source')
        status = self.sql('source', 'SHOW BINARY LOG STATUS').split('\t')
        assert status[0] == filename
        stoppos = int(status[1])
        target_gtid = self.sql('source', 'SELECT @@GLOBAL.gtid_executed')
        # This unwanted transaction is valid SQL and replicates: replication is not a backup.
        self.sql('source', 'START TRANSACTION; DELETE FROM ledger.entries; DELETE FROM ledger.orders; UPDATE ledger.accounts SET balance=100000 WHERE id=1; COMMIT;')
        deleted = self.state('source')
        assert deleted['orders'] == 0
        self.sql('source', self.order(3001, 'after-delete', 7))
        replay = call(['docker', 'exec', self.prefix + '-source', 'mysqlbinlog',
                       '--start-position=' + str(startpos), '--stop-position=' + str(stoppos),
                       '/var/lib/mysql/' + filename]).stdout
        self.feed('pitr', replay)
        assert self.state('pitr') == target
        assert not self.sql('pitr', 'SELECT id FROM ledger.orders WHERE id=3001')
        self.check('transaction-boundary-pitr', start_position=startpos, stop_position=stoppos,
                   binlog=filename, expected=target, actual=self.state('pitr'), excluded=['delete-transaction','after-delete'],
                   target_source_gtid=target_gtid, replay_sha256=hashlib.sha256(replay).hexdigest())
        missing = call(['docker', 'exec', self.prefix + '-source', 'mysqlbinlog',
                        '/var/lib/mysql/not-archived.999999'], check=False)
        assert missing.returncode != 0
        assert restored['sha256'] != target['sha256']
        self.check('missing-log-cannot-reach-target', mysqlbinlog_exit=missing.returncode,
                   snapshot_differs_from_target=True)
        self.wait_replica()
        assert self.state('replica')['orders'] == 1  # it received the accidental deletion too
        self.check('accidental-delete-replicates', replica_orders=1, recovered_pitr_orders=target['orders'])
        self.sql('replica', 'STOP REPLICA SQL_THREAD')
        applied = self.state('replica')
        self.sql('source', self.order(4001, 'delayed-apply', 11))
        wanted = self.sql('source', 'SELECT @@GLOBAL.gtid_executed')
        assert self.state('replica') == applied
        assert self.sql('replica', f"SELECT GTID_SUBSET('{wanted}',@@GLOBAL.gtid_executed)") == '0'
        self.sql('replica', 'START REPLICA SQL_THREAD')
        self.wait_replica()
        self.check('pause-and-catch-up', during_pause=applied, after_resume=self.state('replica'))
        self.sql('replica', 'STOP REPLICA')
        failover_prefix = self.state('replica')
        prefix_time = time.monotonic()
        self.sql('source', self.order(5001, 'acknowledged-but-not-replicated', 13))
        source_ack_time = time.monotonic()
        source_before_failure = self.state('source')
        assert source_before_failure['orders'] == failover_prefix['orders'] + 1
        assert not self.sql('replica', 'SELECT id FROM ledger.orders WHERE id=5001')
        try:
            self.promote()
        except RuntimeError as error:
            assert 'FENCE_REQUIRED' in str(error)
        else:
            raise AssertionError('Unsafe promotion was accepted')
        denied = self.sql('replica', self.order(6000, 'must-reject'), check=False)
        assert denied == '' and self.state('replica') == failover_prefix
        assert self.sql('replica', 'SELECT @@GLOBAL.super_read_only') == '1'
        self.check('unfenced-promotion-refused', old_primary_running=True, replica_remains_read_only=True)
        failure_start = time.monotonic()
        call(['docker', 'stop', '--time', '10', self.prefix + '-source'])
        self.promote()
        self.sql('replica', self.order(6001, 'new-primary-only', 19))
        new_primary_ready = time.monotonic()
        promoted = self.state('replica')
        assert not self.sql('replica', 'SELECT id FROM ledger.orders WHERE id=5001')
        assert self.sql('replica', 'SELECT tag FROM ledger.orders WHERE id=6001') == 'new-primary-only'
        assert promoted['orders'] == failover_prefix['orders'] + 1
        expected_rows = failover_prefix['rows'] + ['6001\t19\tnew-primary-only']
        assert promoted['rows'] == expected_rows
        assert promoted['balance'] == failover_prefix['balance'] - 19
        self.check('fenced-manual-failover-with-observed-loss', source_before_failure=source_before_failure,
                   surviving_prefix=failover_prefix, promoted=promoted, lost_acknowledged_order_ids=[5001],
                   rpo_lost_transactions=1, observed_window_seconds=round(source_ack_time-prefix_time, 4),
                   manual_rto_seconds=round(new_primary_ready-failure_start, 4),
                   rto_boundary='docker-stop invocation to verified new-primary business commit; excludes detection/routing/client retry')
        # A returning old primary stays disconnected; fence its writes before any possible rejoin.
        call(['docker', 'network', 'disconnect', self.network, self.prefix + '-source'])
        call(['docker', 'start', self.prefix + '-source'])
        for _ in range(60):
            try:
                self.sql('source', 'SET GLOBAL super_read_only=ON')
                break
            except RuntimeError:
                time.sleep(1)
        else:
            raise RuntimeError('Returning source did not start')
        denied = self.sql('source', self.order(7001, 'old-primary-reject'), check=False)
        assert denied == ''
        assert not self.sql('source', 'SELECT id FROM ledger.orders WHERE id=7001')
        assert not self.sql('source', 'SELECT id FROM ledger.orders WHERE id=6001')
        networks = json.loads(call(['docker', 'inspect', '--format', '{{json .NetworkSettings.Networks}}', self.prefix + '-source']).stdout)
        assert not networks
        self.check('returning-old-primary-quarantined', networks=networks,
                   super_read_only=self.sql('source', 'SELECT @@GLOBAL.super_read_only'),
                   divergent_old_state=True, automatically_rejoined=False)
        self.report['status'] = 'PASS'
        self.report['scenario_count'] = len(self.report['scenarios'])
        assert self.report['scenario_count'] == 10

    def close(self):
        self.output.write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + '\n')
        for name in self.names:
            call(['docker', 'rm', '-f', '-v', self.prefix + '-' + name], check=False)
        call(['docker', 'network', 'rm', self.network], check=False)
        self.tmp.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', default='evidence/runtime.json')
    args = parser.parse_args()
    lab = Lab(args.evidence)
    try:
        lab.run()
    except BaseException as error:
        lab.report['status'] = 'FAIL'
        lab.report['error'] = str(error)
        for name in lab.names:
            logs = call(['docker', 'logs', '--tail', '40', lab.prefix + '-' + name], check=False)
            print(name, logs.stderr.decode(errors='replace')[-5000:])
        raise
    finally:
        lab.close()


if __name__ == '__main__':
    main()
