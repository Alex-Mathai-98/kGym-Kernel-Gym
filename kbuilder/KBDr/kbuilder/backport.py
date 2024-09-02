# backport.py
import os, json
import asyncio.subprocess as asp
import aiofiles
from KBDr.kworker import run_async

commit_prefixes = [
    'UPSTREAM:',
    'CHROMIUM:',
    'FROMLIST:',
    'BACKPORT:',
    'FROMGIT:',
    'net-backports:'
]

def canonicalize_commit_title(title: str):
    for prefix in commit_prefixes:
        if title.find(prefix) == 0:
            return (title[len(prefix):]).strip()
    return title.strip()

async def get_commit_id_by_message(clone_dir: str, message: str):
    proc = await asp.create_subprocess_exec(
        'git',
        'log',
        '-F',
        '--grep',
        message,
        stdout=asp.PIPE,
        stdin=asp.DEVNULL,
        stderr=asp.PIPE,
        cwd=clone_dir)
    out = (await proc.communicate())[0]
    out = out.decode(encoding='utf-8')
    if len(out) != 0:
        return out.split('\n', maxsplit=1)[0].split(' ')[1]
    else:
        return None

async def check_ancestor_by_commit_id(clone_dir: str, ancestor_commit_id: str):
    code = await ((await asp.create_subprocess_exec(
        'git',
        'merge-base',
        '--is-ancestor',
        ancestor_commit_id,
        'HEAD',
        stdout=asp.DEVNULL,
        stdin=asp.DEVNULL,
        stderr=asp.DEVNULL,
        cwd=clone_dir)).wait())
    return code == 0

async def apply_fix_backports(clone_dir: str):
    async with aiofiles.open(
        os.environ['KBUILDER_BACKPORT_COMMIT_JSON'],
        'r',
        encoding='utf-8') as fp:
        commits = json.loads(await fp.read())
    for commit in commits:
        if 'guilty_hash' in commit:
            if not await check_ancestor_by_commit_id(clone_dir, commit['guilty_hash']):
                # not contains;
                continue
        fix_commit = await get_commit_id_by_message(clone_dir, canonicalize_commit_title(commit['fix_title']))
        if isinstance(fix_commit, str):
            # fixed;
            continue
        cherry_pick_cmdlet = ['cherry-pick', '--no-commit']
        cherry_pick_cmdlet.append('--strategy-option')
        if commit.get('force_merge', False):
            cherry_pick_cmdlet.append('theirs')
        else:
            cherry_pick_cmdlet.append('ours')
        if 'mainline' in commit:
            assert commit['mainline'] > 0
            cherry_pick_cmdlet.append('-m')
            cherry_pick_cmdlet.append(str(commit['mainline']))
        cherry_pick_cmdlet.append(commit['fix_hash'])
        proc = await asp.create_subprocess_exec('git', *cherry_pick_cmdlet, cwd=clone_dir)
        await proc.wait()
