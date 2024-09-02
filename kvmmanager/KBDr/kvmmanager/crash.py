# crash.py
import os, aiofiles, asyncio, shutil, random
from functools import reduce
from KBDr.kworker import run_async

async def collect_crash(idx: int, crash_id: str):
    # move the folder;
    crash_dir = os.path.join('/root/crashes', crash_id)
    new_crash_dir = os.path.join('/root/crashes', str(idx))
    await run_async(shutil.move, crash_dir, new_crash_dir)
    crash_dir = new_crash_dir
    # lisdir the crash dir;
    crash_files = await run_async(os.listdir, crash_dir)
    crash_files.remove('description')
    # description;
    async with aiofiles.open(os.path.join(crash_dir, 'description'), 'r', encoding='utf-8') as fp:
        crash_description = await fp.read()
    crash_description = crash_description.strip()
    num_of_logs = -1
    for fname in crash_files:
        if 'log' in fname:
            num_of_logs = max(num_of_logs, int(fname.split('log', maxsplit=1)[1]))
    num_of_logs += 1
    return crash_description, crash_files, num_of_logs

async def pick_crash_random(crash_titles: list[str]) -> int:
    # Crash > No Crash > Lost Connection > No Output from VM;
    if len(crash_titles) == 0:
        return -1
    # get the regular crashes;
    crashes = set(crash_titles)
    lost_conn = 'lost connection to test machine' in crashes
    no_output = 'no output from test machine' in crashes
    test_mach = 'test machine is not executing programs' in crashes
    if lost_conn:
        crashes.remove('lost connection to test machine')
    if no_output:
        crashes.remove('no output from test machine')
    if test_mach:
        crashes.remove('test machine is not executing programs')
    if len(crashes) > 0:
        return crash_titles.index(random.choice(list(crashes)))
    # special crashes;
    if lost_conn:
        return crash_titles.index('lost connection to test machine')
    if no_output:
        return crash_titles.index('no output from test machine')
    if test_mach:
        return crash_titles.index('test machine is not executing programs')
    return -1

async def collect_crashes(strategy: str, crash_dirs: list[str]) -> tuple[int, list[str], list[list[str]], int]:
    crashes = await asyncio.gather(*[
        collect_crash(idx, cid) for (idx, cid) in zip(range(len(crash_dirs)), crash_dirs)
    ])
    crash_descriptions = reduce(lambda acc, crash: (acc + [crash[0]]), crashes, [])
    file_groups_to_upload = reduce(lambda acc, crash: (acc + [crash[1]]), crashes, [])
    n_crashes = reduce(lambda acc, crash: (acc + crash[2]), crashes, 0)
    crash_picked = await {
        'random': pick_crash_random
    }[strategy](crash_descriptions)
    return crash_picked, crash_descriptions, file_groups_to_upload, n_crashes
