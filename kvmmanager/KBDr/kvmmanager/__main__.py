import os
from .manager import consume_kvmmanager, kvmmanager_argument_schema
from KBDr.kworker import WorkerContext

if __name__ == '__main__':
    ctx = WorkerContext(
        'kvmmanager',
        os.environ['KBDR_VMMANAGER_RABBITMQ_CONN_URL'],
        consume_kvmmanager,
        kvmmanager_argument_schema
    )
    ctx.run()
