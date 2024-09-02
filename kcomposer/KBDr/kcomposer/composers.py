# composers.py
from typing import Tuple
from .models import open_bug
from .models import kbuilder_argument_from_bug, kbuilder_argument, kvmmanager_argument, reproducer_from_bug, reproducer

def compose_kernel_build(
    kernel_git_url: str,
    kernel_commit_id: str,
    kernel_config: str,
    userspace_img_name: str,
    arch: str,
    compiler: str='gcc',
    linker: str='ld',
    patch: str=''
) -> Tuple[list, list, dict[str, str]]:
    """
    Compose a kernel build job.
    Return the list of workers, their arguments and useful kv;

    Usage:
    ```python
    worker_list, arguments, labels = compose_kernel_build(...)
    session.create_job(
        worker_list,
        arguments,
        labels
    )
    ```
    """
    workers = ['kbuilder']
    arguments = [
        kbuilder_argument(
            kernel_git_url,
            kernel_commit_id,
            kernel_config,
            userspace_img_name,
            arch,
            compiler,
            linker,
            None,
            patch
        )
    ]
    kv = {
        'composed-by': 'kcomposer.compose_kernel_build',
        f'contains-kernel-commit-{kernel_commit_id}-at': '0'
    }
    return workers, arguments, kv

def compose_bug_reproduction(
    kernel_git_url: str,
    kernel_commit_id: str,
    kernel_config: str,
    userspace_img_name: str,
    arch: str,
    reproducer_type: str,
    reproducer_text: str,
    syzkaller_checkout: str='master',
    syzkaller_rollback: bool=True,
    compiler: str='gcc',
    linker: str='ld',
    patch: str='',
    nproc: int=8,
    ninstance: int=4,
    restart_time: int='10m',
    machine_type='gce:e2-standard-2'
) -> Tuple[list, list, dict[str, str]]:
    """
    Compose a bug reproduction job.
    Return the list of workers, their arguments and useful kv;

    Usage:
    ```python
    worker_list, arguments, labels = compose_bug_reproduction(...)
    session.create_job(
        worker_list,
        arguments,
        labels
    )
    ```
    """
    workers = ['kbuilder', 'kvmmanager']
    arguments = [
        kbuilder_argument(
            kernel_git_url,
            kernel_commit_id,
            kernel_config,
            userspace_img_name,
            arch,
            compiler,
            linker,
            None,
            patch
        ),
        kvmmanager_argument(
            reproducer(
                reproducer_type,
                reproducer_text,
                nproc, restart_time,
                syzkaller_checkout,
                syzkaller_rollback,
                ninstance
            ),
            machine_type,
            image_from_worker=0
        )
    ]
    kv = {
        'composed-by': 'kcomposer.compose_bug_reproduction',
        f'contains-kernel-commit-{kernel_commit_id}-at': '0'
    }
    return workers, arguments, kv

def compose_bug_reproduction_from_bug(
    bug_dir: str,
    bug_id: str,
    userspace_img_name: str,
    metadata: bool=False,
    compiler: str='gcc',
    linker: str='ld',
    patch: str='',
    nproc: int=8,
    ninstance: int=4,
    restart_time: str='10m',
    machine_type: str='gce:e2-standard-2',
    reproducer_preference: str='log'
) -> Tuple[list, list, dict[str, str]]:
    """
    Compose a bug reproduction job from a specified bug.
    Return the list of workers, their arguments and useful kv;

    Usage:
    ```python
    worker_list, arguments, labels = compose_bug_reproduction_from_bug(...)
    session.create_job(
        worker_list,
        arguments,
        labels
    )
    ```
    """
    bug = open_bug(bug_dir, bug_id)
    workers = ['kbuilder', 'kvmmanager']
    arguments = [
        kbuilder_argument_from_bug(
            bug,
            userspace_img_name,
            bug['crashes'][0],
            metadata,
            compiler,
            linker,
            patch
        ),
        kvmmanager_argument(
            reproducer_from_bug(bug, nproc, restart_time, ninstance, reproducer_preference),
            machine_type,
            image_from_worker=0
        )
    ]
    kv = {
        'composed-by': 'kcomposer.compose_bug_reproduction_from_bug',
        f'contains-kernel-commit-{arguments[0]["kernel-commit-id"]}-at': '0',
        f'contains-bug-kernel-{bug_id}-at': '0',
        'bug-reproduction-for': bug_id
    }
    return workers, arguments, kv

def compose_cross_reproduction_from_bug(
    bug_dir: str,
    kernel_bug_id: str,
    reproducer_bug_ids: list[str],
    uimg: str,
    metadata: bool=False,
    compiler: str='gcc',
    linker: str='ld',
    patch: str='',
    nproc: int=8,
    ninstance: int=4,
    restart_time: str='10m',
    machine_type: str='gce:e2-standard-2',
    reproducer_preference: str='log'
) -> Tuple[list, list, dict[str, str]]:
    """
    Compose a cross reproduction task, resulting in multiple jobs.
    Return a list of workers, list arguments and useful kv.

    Usage:
    ```python
    workers, argument, labels = compose_cross_reproduction_from_bug(...)
    session.create_job(
        workers,
        argument,
        labels
    )
    ```
    """
    kbug = open_bug(bug_dir, kernel_bug_id)
    ret: Tuple[list, list, dict] = (
        ['kbuilder'],
        [kbuilder_argument_from_bug(
            kbug,
            uimg,
            kbug['crashes'][0],
            metadata,
            compiler,
            linker,
            patch
        )],
        {
            'composed-by': 'kcomposer.compose_cross_reproduction_from_bug',
            f'contains-bug-kernel-{kernel_bug_id}-at': '0'
        }
    )
    ret[2][f'contains-kernel-commit-{ret[1][0]["kernel-commit-id"]}-at'] = '0'
    i = 1
    for repro_id in reproducer_bug_ids:
        repro_bug = open_bug(bug_dir, repro_id)
        ret[0].append('kvmmanager')
        ret[1].append(
            kvmmanager_argument(
                reproducer_from_bug(repro_bug, nproc, restart_time, ninstance, reproducer_preference),
                machine_type,
                image_from_worker=0
            )
        )
        ret[2][f'cross-reproduction-kbug-{kernel_bug_id}-rbug-{repro_id}'] = str(i)
        i += 1
    return ret
