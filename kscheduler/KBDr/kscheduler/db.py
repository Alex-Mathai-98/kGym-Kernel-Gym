# db.py
import os, traceback, datetime, json, aiosqlite
from .utils import ISOTimeDefaultStart, ISOTimeDefaultEnd
from .utils import paginated_response, int2job_id, job_id2int

db_conn: aiosqlite.Connection = None

async def connect_db():
    """ Connect to the SQLite Database """
    try:
        global db_conn
        db_conn = await aiosqlite.connect(os.environ['KBDR_SCHEDULER_DB_STR'])
    except:
        print(f'[kscheduler] Error when connecting to SQLite, quit: {traceback.format_exc()}')
        quit()
    # database initialization;
    await init_db()

async def close_db():
    """ Dispose the DB connection """
    await db_conn.commit()
    await db_conn.close()

async def init_db():
    async with db_conn.cursor() as cur:
        # check if db has table `jobs`;
        await cur.execute(
            'SELECT name FROM sqlite_master WHERE type=? AND name=?;', ('table', 'jobs'))
        result = await cur.fetchall()
        # if it's necessary to build the table structures;
        if len(result) == 0:
            await cur.executescript('\n'.join((
                "CREATE TABLE jobs (",
                "`job-id` INTEGER PRIMARY KEY AUTOINCREMENT,",
                "`created-time` TEXT,",
                "`job-workers` TEXT,",
                "`current-worker` INT,",
                "`status` TEXT,",
                "`worker-results` TEXT,",
                "`worker-arguments` TEXT,",
                "`modified-time` TEXT,",
                "`current-worker-hostname` TEXT",
                ");"
            )))
            await cur.executescript('\n'.join((
                "CREATE TABLE job_kv (",
                "`job-id` INTEGER,",
                "`key` TEXT,",
                "`value` TEXT,",
                # the constraint for ON CONFLICT clauses;
                "CONSTRAINT mkey PRIMARY KEY(`job-id`, `key`)",
                ");"
            )))
            await cur.executescript('\n'.join((
                "CREATE TABLE job_log (",
                "`job-id` INTEGER,",
                "`log-time` TEXT,",
                "`worker` TEXT,",
                "`worker-hostname` TEXT,",
                "`log` TEXT",
                ");"
            )))
            await cur.executescript('\n'.join((
                "CREATE TABLE sys_log (",
                "`log-time` TEXT,",
                "`worker` TEXT,",
                "`worker-hostname` TEXT,",
                "`log` TEXT",
                ");"
            )))

        # Smart Worker Update: upgrade the database here for smart workers;
        await cur.execute(
            "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('jobs') \
            WHERE name='current-worker-hostname';"
        )
        result = await cur.fetchall()
        if result[0][0] == 0:
            # upgrade;
            await cur.execute('ALTER TABLE jobs ADD `current-worker-hostname` TEXT;')
            await cur.execute('UPDATE jobs SET `current-worker-hostname`=?;', ('', ))

        # change in_progress status to aborted, change worker focus to null;
        await cur.execute(
            "UPDATE jobs SET `status`=?, `current-worker-hostname`=? \
            WHERE `status`=? OR `status`=?;", ('aborted', '', 'in_progress', 'pending'))

def parse_job_ctx(tup: tuple):
    """ Parse the job context from database """
    return {
        'job-id': int2job_id(tup[0]),
        'created-time': tup[1],
        'job-workers': json.loads(tup[2]),
        'current-worker': tup[3],
        'status': tup[4],
        'worker-results': json.loads(tup[5]),
        'worker-arguments': json.loads(tup[6]),
        'modified-time': tup[7],
        'current-worker-hostname': tup[8]
    }

def parse_job_ctx_digest(tup: tuple):
    """ Parse the job digest from database """
    return {
        'job-id': int2job_id(tup[0]),
        'created-time': tup[1],
        'job-workers': json.loads(tup[2]),
        'current-worker': tup[3],
        'status': tup[4],
        'modified-time': tup[5],
        'current-worker-hostname': tup[6]
    }

def parse_sys_log(tup: tuple):
    """ Parse the system log from database """
    return {
        'log-time': tup[0],
        'worker': tup[1],
        'worker-hostname': tup[2],
        'log': tup[3]
    }

def parse_job_log(tup: tuple):
    """ Parse the job log from database """
    return {
        'job-id': int2job_id(tup[0]),
        'log-time': tup[1],
        'worker': tup[2],
        'worker-hostname': tup[3],
        'log': tup[4]
    }

async def insert_job_log(log: dict):
    """ Insert a new job log to DB """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO job_log (`job-id`, `log-time`, `worker`, \
            `worker-hostname`, `log`) VALUES(?, ?, ?, ?, ?);",
            (job_id2int(log['job-id']),
            log['log-time'],
            log['worker'],
            log['worker-hostname'],
            log['log'])
        )

async def insert_sys_log(log: dict):
    """ Insert a new system log to DB """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO sys_log (`log-time`, `worker`, \
            `worker-hostname`, `log`) VALUES(?, ?, ?, ?);",
            (log['log-time'], log['worker'], log['worker-hostname'], log['log']))

async def get_job_kv_keys(job_id: str):
    """ Return a list of string keys """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT `key` FROM job_kv \
            WHERE `job-id` = ?;",
            (job_id2int(job_id), )
        )
        result = await cur.fetchall()
        return list(map(lambda x: x[0], result))

async def get_job_kv_value(job_id: str, key: str):
    """ Return the value of the corresponding key, if not found return None """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT `value` FROM job_kv \
            WHERE `job-id` = ? AND `key` = ?;",
            (job_id2int(job_id), key)
        )
        result = await cur.fetchall()
        if len(result) == 0:
            return None
        else:
            return result[0][0]

async def get_key_entries(key: str):
    """ Return all kv entries by the given key """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT `job-id`, `key`, `value` FROM job_kv WHERE `key`=?;",
            (key, )
        )
        result = await cur.fetchall()
        return list(map(lambda row: {'job-id': row[0], 'key': row[1], 'value': row[2]}, result))

async def update_job_kv_value(job_id: str, kv: dict[str, str]):
    """ Update the KV store with a dictionary array """
    async with db_conn.cursor() as cur:
        jid = job_id2int(job_id)
        await cur.executemany(
            "INSERT INTO job_kv(`job-id`, `key`, `value`) VALUES(?, ?, ?) \
            ON CONFLICT(`job-id`, `key`) DO \
            UPDATE SET `value`=excluded.`value`;",
            tuple(map(lambda pair: (jid, pair[0], pair[1]), kv.items()))
        )

async def get_job_kv_entries(job_id: str):
    """ Return the dict of the job's KV store """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT `key`, `value` FROM job_kv \
            WHERE `job-id` = ?;",
            (job_id2int(job_id), )
        )
        result = await cur.fetchall()
        ret = dict()
        for row in result:
            ret[row[0]] = row[1]
        return ret

async def insert_job(ctx: dict):
    """ Insert a new job with the given context, return auto-incremented ID """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO jobs \
            (`job-id`, `created-time`, `job-workers`, \
            `current-worker`, `status`, `worker-results`, \
            `worker-arguments`, `modified-time`, `current-worker-hostname`) \
            VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?) \
            RETURNING `job-id`;",
            (ctx['created-time'], json.dumps(ctx['job-workers']),
            ctx['current-worker'], ctx['status'], json.dumps(ctx['worker-results']),
            json.dumps(ctx['worker-arguments']), ctx['created-time'], ''))
        job_id = (await cur.fetchall())[0][0]
    await update_job_kv_value(int2job_id(job_id), ctx['kv'])
    return int2job_id(job_id)

async def reset_job(ctx: dict):
    """ Activate a job with the updated context of the job """
    async with db_conn.cursor() as cur:
        ts = datetime.datetime.utcnow().isoformat()

        await cur.execute(
            "UPDATE jobs SET `current-worker`=?, `status`=?, `job-workers`=?, `worker-results`=?, \
            `worker-arguments`=?, `modified-time`=? WHERE `job-id` = ? AND `modified-time` < ? AND \
            (`status` = ? OR `status` = ?);",
            (ctx['current-worker'], ctx['status'], json.dumps(ctx['job-workers']),
            json.dumps(ctx['worker-results']), json.dumps(ctx['worker-arguments']), ts,
            job_id2int(ctx['job-id']), ts, 'aborted', 'finished')
        )

        if cur.rowcount == 1:
            await update_job_kv_value(ctx['job-id'], ctx['kv'])
            return True
        else:
            return False

async def append_job_result(job_id: str, worker_hostname: str, success: bool, result_payload: dict):
    async with db_conn.cursor() as cur:
        ts = datetime.datetime.utcnow().isoformat()
        # read the context and do modification;
        # update conditionally with result back;
        job_ctx = await get_job(job_id)
        job_ctx['worker-results'].append(result_payload)
        if success:
            job_ctx['current-worker'] += 1
        n_workers = len(job_ctx['job-workers'])
        job_ctx['status'] = 'waiting' if job_ctx['current-worker'] < n_workers else 'finished'

        await cur.execute(
            "UPDATE jobs SET `current-worker-hostname`=?, `current-worker`=?, \
            `status`=?, `worker-results`=?, `modified-time`=? \
            WHERE `current-worker-hostname` = ? AND `job-id` = ? AND \
            `status` = ? AND `modified-time` < ?;",
            ('', job_ctx['current-worker'], job_ctx['status'],
            json.dumps(job_ctx['worker-results']), ts, worker_hostname,
            job_id2int(job_id), 'in_progress', ts)
        )

        # check if updated;
        if cur.rowcount == 1:
            # next worker
            return job_ctx['job-workers'][job_ctx['current-worker']]

async def focus_job(job_id: str, worker_hostname: str):
    async with db_conn.cursor() as cur:
        ts = datetime.datetime.utcnow().isoformat()

        await cur.execute(
            "UPDATE jobs SET `status`=?, `current-worker-hostname`=?, `modified-time`=? \
            WHERE `job-id` = ? AND `current-worker-hostname` = ? AND \
            (`status` = ? OR `status` = ?) AND `modified-time` < ?;",
            ('in_progress', worker_hostname, ts, job_id2int(job_id),
            '', 'waiting', 'pending', ts)
        )

        return cur.rowcount == 1

async def abort_job(job_id: str):
    async with db_conn.cursor() as cur:
        ts = datetime.datetime.utcnow().isoformat()

        await cur.execute(
            "SELECT `status`, `current-worker-hostname`, `modified-time` FROM jobs \
            WHERE `job-id` = ?;",
            (job_id2int(job_id), )
        )
        result = await cur.fetchall()

        await cur.execute(
            "UPDATE jobs SET `status`=?, `current-worker-hostname`=?, `modified-time`=? \
            WHERE `job-id` = ? AND (`status` = ? OR `status` = ? OR `status` = ?) \
            AND `modified-time` < ?;",
            ('aborted', '', ts, job_id2int(job_id), 'waiting', 'pending', 'in_progress', ts)
        )

        if cur.rowcount == 1:
            return result[0][1]
        else:
            return None

async def get_job_log(
        job_id: str,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of job log """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM job_log \
            WHERE `job-id` = ?;",
            (job_id2int(job_id), )
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `job-id`, `log-time`, `worker`, `worker-hostname`, `log` FROM job_log \
            WHERE `job-id` = ? \
            ORDER BY `log-time` DESC \
            LIMIT ? OFFSET ?;",
            (job_id2int(job_id), limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_job_log, result)), start, limit)

async def get_job_log_display(
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of job log display """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM job_log \
            WHERE `log-time` >= ? AND `log-time` <= ?;",
            (start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `job-id`, `log-time`, `worker`, `worker-hostname`, `log` FROM job_log \
            WHERE `log-time` >= ? AND `log-time` <= ? \
            ORDER BY `log-time` DESC \
            LIMIT ? OFFSET ?;",
            (start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_job_log, result)), start, limit)

async def get_sys_log_by_worker(
        worker: str,
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of system log from given worker """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM sys_log \
            WHERE `worker` = ? AND `log-time` >= ? AND `log-time` <= ?;",
            (worker, start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `log-time`, `worker`, `worker-hostname`, `log` FROM sys_log \
            WHERE `worker` = ? AND `log-time` >= ? AND `log-time` <= ? \
            ORDER BY `log-time` DESC \
            LIMIT ? OFFSET ?;",
            (worker, start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_sys_log, result)), start, limit)

async def get_sys_log_by_worker_hostname(
        worker_hostname: str,
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of system log from given worker hostname """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM sys_log \
            WHERE `worker_hostname` = ? AND `log-time` >= ? AND `log-time` <= ?;",
            (worker_hostname, start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `log-time`, `worker`, `worker-hostname`, `log` FROM sys_log \
            WHERE `worker_hostname` = ? AND `log-time` >= ? AND `log-time` <= ? \
            ORDER BY `log-time` DESC \
            LIMIT ? OFFSET ?;",
            (worker_hostname, start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_sys_log, result)), start, limit)

async def get_sys_log_display(
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of system log """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM sys_log \
            WHERE `log-time` >= ? AND `log-time` <= ?;",
            (start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `log-time`, `worker`, `worker-hostname`, `log` FROM sys_log \
            WHERE `log-time` >= ? AND `log-time` <= ? \
            ORDER BY `log-time` DESC \
            LIMIT ? OFFSET ?;",
            (start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_sys_log, result)), start, limit)

async def get_job(job_id: str):
    """ Return the job context """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT \
            `job-id`, \
            `created-time`, \
            `job-workers`, \
            `current-worker`, \
            `status`, \
            `worker-results`, \
            `worker-arguments`, \
            `modified-time`, \
            `current-worker-hostname` \
            FROM jobs WHERE `job-id`=?;",
            (job_id2int(job_id), )
        )
        result = await cur.fetchone()
    if isinstance(result, tuple):
        ctx = parse_job_ctx(result)
        ctx['kv'] = await get_job_kv_entries(job_id)
        return ctx

async def get_jobs_by_created_time(
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of job digests sorted by created time """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM jobs \
            WHERE `created-time` >= ? AND `created-time` <= ?;",
            (start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `job-id`, `created-time`, `job-workers`, `current-worker`, \
            `status`, `modified-time`, `current-worker-hostname` FROM jobs \
            WHERE `created-time` >= ? AND `created-time` <= ? \
            ORDER BY `created-time` DESC \
            LIMIT ? OFFSET ?;",
            (start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_job_ctx_digest, result)), start, limit)

async def get_jobs_by_modified_time(
        start_time: str=ISOTimeDefaultStart,
        end_time: str=ISOTimeDefaultEnd,
        start: int = 0,
        limit: int = 20):
    """ Return a paginated result of job digests sorted by modified time """
    async with db_conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM jobs \
            WHERE `modified-time` >= ? AND `modified-time` <= ?;",
            (start_time, end_time)
        )
        count = (await cur.fetchall())[0][0]
        await cur.execute(
            "SELECT `job-id`, `created-time`, `job-workers`, `current-worker`, \
            `status`, `modified-time`, `current-worker-hostname` FROM jobs \
            WHERE `modified-time` >= ? AND `modified-time` <= ? \
            ORDER BY `modified-time` DESC \
            LIMIT ? OFFSET ?;",
            (start_time, end_time, limit, start)
        )
        result = await cur.fetchall()
        return paginated_response(count, list(map(parse_job_ctx_digest, result)), start, limit)
