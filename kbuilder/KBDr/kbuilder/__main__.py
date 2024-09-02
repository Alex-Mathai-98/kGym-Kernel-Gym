# __main__.py
import os
from .builder import consume_kbuilder, kbuilder_argument_schema
from KBDr.kworker import WorkerContext

if __name__ == '__main__':
    ctx = WorkerContext(
        'kbuilder',
        os.environ['KBDR_KBUILDER_RABBITMQ_CONN_URL'],
        consume_kbuilder,
        kbuilder_argument_schema
    )
    ctx.run()
