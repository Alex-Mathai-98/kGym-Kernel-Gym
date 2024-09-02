# builder.py
import asyncio.subprocess as asp
import aiofiles
from KBDr.kworker import JobProcessorContext, run_async
import os, json, shutil
from typing import Tuple
from google.cloud.storage import Client, transfer_manager, Blob
from .bug_metadata import generate_bug_metedata
from .repo import get_local_repo, get_userspace_image
from .backport import apply_fix_backports

kbuilder_argument_schema = {
    "type": "object",
    "properties": {
        "kernel-git-url": { "type": "string" },
        "kernel-commit-id": { "type": "string" },
        "kernel-config": { "type": "string" },
        "userspace-image-name": { "type": "string" },
        "kernel-arch": { "type": "string" },
        "kernel-cmdline": { "type": "string" },
        "compiler": { "type": "string" },
        "linker": { "type": "string" },
        "bug-metadata": {
            "type": "object",
            "properties": {
                "bug-id": { "type": "string" },
                "clean-crash-traces": { "type": "array" }
            },
            "required": [ "bug-id", "clean-crash-traces" ]
        },
        "patch": { "type": "string" }
    },
    "required": [
        "kernel-git-url", "kernel-commit-id", "kernel-config", "userspace-image-name", "kernel-arch"
    ]
}

async def prepare_clone(
    git_url: str,
    repo_dir: str,
    clone_dir: str,
    argument: dict) -> Tuple[bool, str]:
    await run_async(os.makedirs, clone_dir, exist_ok=True)
    local_repo = await get_local_repo(git_url)
    if not isinstance(local_repo, str):
        return False, 'Failed to clone the remote repo'
    cached_remote = os.path.abspath(os.path.join(repo_dir, local_repo))
    # clone repo;
    code = await ((await asp.create_subprocess_exec(
        'git',
        'clone',
        cached_remote,
        '.',
        cwd=clone_dir,
        stdin=asp.DEVNULL,
        stderr=asp.DEVNULL)).wait())
    if code != 0:
        return False, 'Failed to clone the local repo'
    # set the remote url;
    code = await ((await asp.create_subprocess_exec(
        'git',
        'remote',
        'set-url',
        'origin',
        argument['kernel-git-url'],
        cwd=clone_dir,
        stdin=asp.DEVNULL,
        stderr=asp.DEVNULL)).wait())
    if code != 0:
        return False, 'Failed to set the remote'
    # checkout;
    code = await ((await asp.create_subprocess_exec(
        'git',
        'checkout',
        argument['kernel-commit-id'],
        cwd=clone_dir,
        stdin=asp.DEVNULL,
        stdout=asp.DEVNULL,
        stderr=asp.DEVNULL)).wait())
    if code != 0:
        # try fetch the orphan;
        # git fetch origin <commit-id>:refs/remotes/origin/orphaned-commit
        code = await ((await asp.create_subprocess_exec(
            'git',
            'fetch',
            'origin',
            f'{argument["kernel-commit-id"]}:refs/remotes/origin/orphaned-commit',
            cwd=clone_dir,
            stdin=asp.DEVNULL,
            stdout=asp.DEVNULL,
            stderr=asp.DEVNULL)).wait())
        if code != 0:
            return False, 'Failed to fetch the commit as if it\'s dangling commit'
        code = await ((await asp.create_subprocess_exec(
            'git',
            'checkout',
            argument["kernel-commit-id"],
            cwd=clone_dir,
            stdin=asp.DEVNULL,
            stdout=asp.DEVNULL,
            stderr=asp.DEVNULL)).wait())
        if code != 0:
            return False, 'Fetched the dangling commit but failed to checkout'
    # apply cherrypick commits;
    await apply_fix_backports(clone_dir)
    return True, ''

async def get_compile_commands(clone_dir: str):
    if os.path.exists(os.path.join(clone_dir, 'scripts/clang-tools/gen_compile_commands.py')):
        code = await ((await asp.create_subprocess_exec(
            'python3',
            'scripts/clang-tools/gen_compile_commands.py',
            cwd=clone_dir)).wait())
    elif os.path.exists(os.path.join(clone_dir, 'scripts/gen_compile_commands.py')):
        code = await ((await asp.create_subprocess_exec(
            'python3',
            'scripts/gen_compile_commands.py',
            cwd=clone_dir)).wait())
    else:
        return
    json_path = os.path.join(clone_dir, 'compile_commands.json')
    if code == 0 and os.path.exists(json_path):
        async with aiofiles.open(json_path, encoding='utf-8') as fp:
            cmds = json.loads(await fp.read())
            return cmds

async def apply_patch(patch: str, clone_dir: str) -> bool:
    proc = await asp.create_subprocess_exec(
        "git",
        "apply",
        stdin=asp.PIPE,
        cwd=clone_dir
    )
    await proc.communicate(patch.encode('utf-8'))
    return (await proc.wait()) == 0

async def on_cancellation(jpctx: JobProcessorContext):
    work_dir = os.environ['KBUILDER_KERNEL_WORK_DIR']
    if await run_async(os.path.exists, work_dir):
        await run_async(shutil.rmtree, work_dir, ignore_errors=True)

async def consume_kbuilder(
    jpctx: JobProcessorContext,
    job_ctx: dict):
    jpctx.register_cleanup_handler(on_cancellation)
    task_result = {
        'result': 'failure',
        'message': ''
    }
    argument: dict = job_ctx['worker-arguments'][job_ctx['current-worker']]
    # get the repo checkout;
    work_dir = os.environ['KBUILDER_KERNEL_WORK_DIR']
    # GCP client;
    storage_client = Client()
    bucket_name = os.environ['GCS_BUCKET_NAME']
    bucket = storage_client.bucket(bucket_name)
    job_storage_prefix = f'jobs/{job_ctx["job-id"]}/{job_ctx["current-worker"]}_kbuilder/'
    job_storage_url_prefix = f'https://storage.cloud.google.com/{bucket_name}/{job_storage_prefix}'
    if await run_async(os.path.exists, work_dir):
        await run_async(shutil.rmtree, work_dir, ignore_errors=True)
    # create directories;
    await run_async(os.makedirs, work_dir)
    clone_dir = os.path.join(work_dir, 'linux')
    await run_async(os.makedirs, clone_dir)
    userspace_img, ssh_key = await get_userspace_image(argument['userspace-image-name'])
    # clone repo;
    await jpctx.worker.report_job_log_async(job_ctx['job-id'], 'Getting the kernel checkout')
    status, message = await prepare_clone(
        argument['kernel-git-url'],
        os.environ['KBUILDER_KERNEL_REPO_PATH'],
        clone_dir,
        argument)
    if not status:
        task_result['message'] = message
        await jpctx.worker.report_job_log_async(job_ctx['job-id'], task_result['message'])
        return False, task_result
    else:
        await jpctx.worker.report_job_log_async(
            job_ctx['job-id'],
            'Successfully obtained the kernel checkout')
    # save the config;
    async with aiofiles.open(os.path.join(work_dir, 'config'), 'w', encoding='utf-8') as fp:
        await fp.write(argument['kernel-config'])
    # apply patch;
    if 'patch' in argument and argument['patch'] != '':
        if not (await apply_patch(argument['patch'], clone_dir)):
            await jpctx.worker.report_job_log_async(
                job_ctx['job-id'],
                'Unsuccessful patch application'
            )
            task_result['message'] = 'Patch is not applicable'
            return False, task_result
        else:
            await jpctx.worker.report_job_log_async(
                job_ctx['job-id'],
                'Successful patch application'
            )
    # call syz-build;
    await jpctx.worker.report_job_log_async(job_ctx['job-id'], 'Invoking syz-build')
    proc = await asp.create_subprocess_exec(
        'sudo',
        '/usr/local/bin/syz-build',
        '-os', 'linux',
        '-arch', argument['kernel-arch'],
        '-config', 'config',
        '-vm', 'gce',
        '-kernel_src', clone_dir,
        '-compiler', argument.get('compiler', 'clang'),
        '-linker', argument.get('linker', 'ld.lld'),
        '-cmdline', argument.get('kernel-cmdline', ''),
        '-userspace', userspace_img,
        cwd=work_dir, stdout=asp.PIPE, stderr=asp.PIPE, stdin=asp.DEVNULL)
    out, err = await proc.communicate()
    code = proc.returncode
    await jpctx.worker.report_job_log_async(job_ctx['job-id'], 'Syz-build Error Log:\n' + err.decode())
    if code != 0:
        task_result['message'] = 'Failed to build'
        await jpctx.worker.report_job_log_async(job_ctx['job-id'], task_result['message'])
        return False, task_result
    # result message;
    task_result = {
        'result': 'success'
    }
    # compile commands;
    cmd = await get_compile_commands(clone_dir)
    if (argument.get('compiler', 'clang') != 'clang') or (not isinstance(cmd, list)):
        await jpctx.worker.report_job_log_async(
            job_ctx['job-id'],
            'No compile_command.json, metadata skipped')
    elif 'bug-metadata' in argument:
        # metadata;
        meta_dir = os.path.join(work_dir, 'meta')
        os.makedirs(meta_dir)
        await jpctx.worker.report_job_log_async(job_ctx['job-id'], 'Generating metadata')
        metadata_files = await run_async(
            generate_bug_metedata,
            argument['bug-metadata'],
            cmd, clone_dir, meta_dir)
        results = await run_async(
            transfer_manager.upload_many_from_filenames,
            bucket, metadata_files, source_directory=meta_dir,
            blob_name_prefix=job_storage_prefix + 'metadata/')
        for name, result in zip(metadata_files, results):
            if isinstance(result, Exception):
                await jpctx.worker.report_job_log_async(job_ctx['job-id'], f'Failed to upload {name}')
            else:
                await jpctx.worker.report_job_log_async(job_ctx['job-id'], f'Successfully uploaded {name}')
        # upload;
        results = await run_async(
            transfer_manager.upload_many_from_filenames,
            bucket, ['compile_commands.json'], source_directory=clone_dir,
            blob_name_prefix=job_storage_prefix)
        if isinstance(results[0], Exception):
            await jpctx.worker.report_job_log_async(
                job_ctx['job-id'],
                'Failed to upload compile_commands.json')
        else:
            task_result['kernel-compile-commands-url'] = job_storage_url_prefix + 'compile_commands.json'
            await jpctx.worker.report_job_log_async(
                job_ctx['job-id'],
                'Successfully uploaded compile_commands.json')
    upload_list = []
    key_list = []
    # - kernel image;
    if os.path.exists(os.path.join(work_dir, 'kernel')):
        upload_list.append('kernel')
        key_list.append('kernel-image-url')
    else:
        task_result = {
            'result': 'failure',
            'message': 'No kernel after build'
        }
        results = await jpctx.worker.report_job_log_async(job_ctx['job-id'], task_result['message'])
        return False, task_result
    # - kernel config;
    if os.path.exists(os.path.join(work_dir, 'kernel.config')):
        upload_list.append('kernel.config')
        key_list.append('kernel-config-url')
    # - gce image;
    if argument['userspace-image-name'] != '' and os.path.exists(os.path.join(work_dir, 'image')):
        # tar and gzip;
        await run_async(
            shutil.move,
            os.path.join(work_dir, 'image'),
            os.path.join(work_dir, 'disk.raw'))
        code = await ((await asp.create_subprocess_exec(
            'tar',
            '-czf',
            'image.tar.gz',
            'disk.raw',
            cwd=work_dir,
            stdout=asp.DEVNULL,
            stderr=asp.DEVNULL)).wait())
        upload_list.append('image.tar.gz')
        key_list.append('vm-image-url')
    await jpctx.worker.report_job_log_async(job_ctx['job-id'], 'Start to upload files')
    results = await run_async(
        transfer_manager.upload_many_from_filenames,
        bucket, upload_list, source_directory=work_dir,
        blob_name_prefix=job_storage_prefix)
    # vmlinux at "obj", "vmlinux";
    upload_list.append('vmlinux')
    key_list.append('vmlinux-url')
    results.append(
        await run_async(
            transfer_manager.upload_many_from_filenames,
            bucket, ['vmlinux'], source_directory=os.path.join(work_dir, 'obj'),
            blob_name_prefix=job_storage_prefix))
    for name, result, key in zip(upload_list, results, key_list):
        if isinstance(result, Exception):
            await jpctx.worker.report_job_log_async(job_ctx['job-id'], f'Failed to upload {name}')
        else:
            task_result[key] = job_storage_url_prefix + name
            await jpctx.worker.report_job_log_async(job_ctx['job-id'], f'Successfully uploaded {name}')
    task_result['message'] = 'Everything OK'
    if isinstance(ssh_key, str):
        task_result['ssh-private-key'] = ssh_key
    async with aiofiles.open(os.path.join(work_dir, 'kernel.config'), 'r', encoding='utf-8') as fp:
        task_result['final-kernel-config'] = await fp.read()
    return True, task_result
