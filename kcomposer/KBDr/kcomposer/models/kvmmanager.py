# kvmmanager.py

def image_from_existing_job(job_ctx: dict, kbuilder_id: int) -> tuple[str, str, str]:
    """
    Get image URL and architecture info from an existing job

    Parameters:
    - job_ctx (dict): The job context
    - kbuilder_id (int): The given kbuilder ID in the worker list

    Returns:
    - image_url (str): The image URL
    - arch (str): The architecture of the image
    """
    if (kbuilder_id in range(len(job_ctx['worker-results'])) and
        job_ctx['job-workers'][kbuilder_id] == 'kbuilder'):
        result_id = kbuilder_id
    elif kbuilder_id in (-1, -2):
        result_id = job_ctx['job-workers'][
            ::(-1 if kbuilder_id == -1 else 1)].index('kbuilder')
    else:
        raise ValueError(kbuilder_id, "Not in range")
    return job_ctx['worker-results'][result_id]['vm-image-url'], job_ctx['worker-arguments'][result_id]['kernel-arch'], job_ctx['worker-results'][result_id]['vmlinux-url']

def reproducer(
    reproducer_type: str,
    reproducer_text: str,
    nproc: int,
    restart_time: str,
    syzkaller_checkout: str,
    rollback: bool,
    ninstance: int
) -> dict:
    """
    Compose a reproducer object

    Parameters:
    - reproducer_type (str): The type of the reproducer, must be `c` or `log`
    - reproducer_text (str): The text content of the reproducer
    - nproc (int): The number of reproducer processes to be run
    - restart_time (str): The time to restart/shutdown, usually `5m`, `10m`
    - syzkaller_checkout (str): Which syzkaller checkout to use in the reproduction
    - rollback (str): Whether to rollback syzkaller to latest checkout when 
    it's failed to compile syzkaller
    
    Returns:
    - dict: Reproducer object
    """
    assert reproducer_type in ('c', 'log')
    return {
        'reproducer-type': reproducer_type,
        'reproducer-text': reproducer_text,
        'nproc': nproc,
        'restart-time': restart_time,
        'syzkaller-checkout': syzkaller_checkout,
        'syzkaller-rollback-to-latest': rollback,
        'ninstance': ninstance
    }

def reproducer_from_bug(
    bug: dict,
    nproc: int,
    restart_time: str,
    ninstance: int,
    preference: str='log',
    syzkaller_checkout: str='master',
    rollback: bool=True
) -> dict:
    """
    Compose a reproducer object from syz-dump bug dictionary

    Parameters:
    - bug (dict): The bug dict
    - nproc (int): The number of reproducer processes to be run
    - restart_time (str): The time to restart/shutdown, usually `5m`, `10m`
    - preference (str): Can be `log` or `c`. State your preference of reproducer
    to be extracted from the bug
    - syzkaller_checkout (str): Syzkaller checkout name; Will be overrided by
    bug info if using log reproducer
    - rollback (str): Whether to rollback syzkaller to latest checkout when 
    it's failed to compile syzkaller

    Returns:
    - dict: Reproducer object
    """
    for crash in bug['crashes']:
        if not ('c-reproducer-data' in crash or 'syz-reproducer-data' in crash):
            raise ValueError(bug['id'], 'No reproducer')
        if preference == 'log':
            return reproducer(
                'log' if 'syz-reproducer-data' in crash else 'c',
                crash.get('syz-reproducer-data', crash.get('c-reproducer-data', '')),
                nproc,
                restart_time,
                crash.get('syzkaller-commit', 'master'),
                rollback,
                ninstance
            )
        elif preference == 'c':
            return reproducer(
                'c' if 'c-reproducer-data' in crash else 'log',
                crash.get('c-reproducer-data', crash.get('syz-reproducer-data', '')),
                nproc,
                restart_time,
                syzkaller_checkout,
                rollback,
                ninstance
            )
        else:
            raise ValueError(preference, 'Invalid preferred type')
    raise ValueError(bug['id'], 'No valid crash can be used')

def kvmmanager_argument(
    reproducer: dict,
    machine_type: str,
    image_from_worker: int=-1,
    image_url: str="",
    arch: str="",
    ssh_key: str="",
    vmlinux_url: str="",
    crash_collecting_policy: str='random'
) -> dict:
    """
    Compose a kvmmanager argument,
    the image is provided by either `image_from_worker` or `image_url`

    Parameters:
    - reproducer (dict): Reproducer field, compose it with `reproducer_from_bug`
    - machine_type (str): In the format of `gce:model` or `qemu:model`,
    qemu emulation is not supported yet
    - image_from_worker (int): Tell kvmmanager to run reproducer on the kernel
    produced by which worker in the current job context
    - image_url (str): Provide the image URL in the Google API URL format,
    can be obatined with `image_from_existing_job`
    - arch (str): The architecture of the given kernel at `image_url`,
    can be obatined with `image_from_existing_job`

    Returns:
    - dict: kvmmanager argument
    """
    if image_from_worker != -1 and (image_url != "" or arch != ""):
        raise ValueError("Only one image can be given")
    ret = {
        'reproducer': reproducer,
        'machine-type': machine_type,
        'crash-collecting-policy': crash_collecting_policy
    }
    if image_from_worker != -1:
        ret['image-from-worker'] = image_from_worker
    elif image_url != "" and arch != "":
        ret['image'] = {
            'image-url': image_url,
            'arch': arch,
            'vmlinux-url': vmlinux_url
        }
        if ssh_key != "":
            ret['image']['ssh_key'] = ssh_key
    else:
        raise ValueError("One image argument is expected")
    return ret
