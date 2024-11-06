# syzkaller.py
import asyncio.subprocess as asp

async def prepare_syzkaller(checkout_name: str, rollback: bool) -> tuple[bool, str, str]:
    # not necessary to rollback if it's already preparing kgym-latest;
    rollback = rollback and (checkout_name != 'kgym-latest')

    syzkaller_repo = '/root/syzkaller'
    # make clean;
    proc = await asp.create_subprocess_exec(
        'git', 'clean', '-fxd', stdin=asp.DEVNULL, stderr=asp.DEVNULL,
        stdout=asp.DEVNULL, cwd=syzkaller_repo
    )
    code = await proc.wait()
    if code != 0:
        return False, 'Failed to make clean the syzkaller folder', ''
    # git pull;
    proc = await asp.create_subprocess_exec(
        'git', 'pull', 'origin', 'kgym-latest', stdin=asp.DEVNULL, stderr=asp.DEVNULL,
        stdout=asp.DEVNULL, cwd=syzkaller_repo
    )
    code = await proc.wait()
    if code != 0:
        return False, 'Failed to pull the latest syzkaller', ''
    # git checkout {checkout_name};
    proc = await asp.create_subprocess_exec(
        'git', 'checkout', checkout_name, stdin=asp.DEVNULL, stderr=asp.DEVNULL,
        stdout=asp.DEVNULL, cwd=syzkaller_repo
    )
    code = await proc.wait()
    if code != 0:
        return False, f'Failed to checkout syzkaller:{checkout_name}', ''
    # make target;
    proc = await asp.create_subprocess_exec(
        'make', 'target', '-j4', stdin=asp.DEVNULL, stderr=asp.DEVNULL,
        stdout=asp.DEVNULL, cwd=syzkaller_repo
    )
    code = await proc.wait()
    if code == 0:
        proc = await asp.create_subprocess_exec(
            'git', 'rev-parse', 'HEAD', stdin=asp.DEVNULL, stderr=asp.DEVNULL,
            stdout=asp.PIPE, cwd=syzkaller_repo
        )
        commit_id, _ = await proc.communicate()
        return True, '', commit_id.decode('utf-8').strip()
    if not rollback:
        return False, f'Failed to build syzkaller:{checkout_name}', ''
    # rollback;
    return await prepare_syzkaller('kgym-latest', False)
