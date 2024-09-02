# manager.py
import json, os, shutil, signal, asyncio
from functools import reduce
from stat import S_IRUSR, S_IWUSR
import asyncio.subprocess as asp
import aiofiles
from KBDr.kworker import run_async, JobProcessorContext
from .gcp import create_image_from_gcs, delete_image_in_gce
from .syzkaller import prepare_syzkaller
from google.cloud.storage import Client, transfer_manager, Blob
from .crash import collect_crashes

kvmmanager_argument_schema = {
    "type": "object",
    "properties": {
        "reproducer": {
            "type": "object",
            "properties": {
                "reproducer-type": {
                    "type": "string",
                    "enum": ["c", "log"]
                },
                "reproducer-text": { "type": "string" },
                "syzkaller-checkout": { "type": "string" },
                "syzkaller-rollback-to-latest": { "type": "boolean" },
                "nproc": { "type": "number" },
                "restart-time": { "type": "string" },
                "ninstance": { "type": "number" }
            },
            "required": [
                "reproducer-type",
                "reproducer-text",
                "syzkaller-checkout",
                "syzkaller-rollback-to-latest",
                "nproc",
                "restart-time",
                "ninstance"
            ]
        },
        "image": {
            "type": "object",
            "properties": {
                "image-url": { "type": "string" },
                "arch": {
                    "type": "string",
                    "enum": ["amd64", "386"]
                },
                "ssh-key": { "type": "string" },
                "vmlinux-url": { "type": "string" }
            },
            "required": ["image-url", "arch"]
        },
        "image-from-worker": { "type": "number" },
        "machine-type": {
            "type": "string",
            "pattern": "^(gce|local):([a-zA-Z][a-zA-Z0-9\\-]*)$"
        },
        "crash-collecting-policy": {
            "type": "string",
            # TODO: Support more crash collecting policies;
            "pattern": "^(random)$"
        }
    },
    "required": ["reproducer", "machine-type", "crash-collecting-policy"]
}

def is_image_creation_necessary(job_ctx: dict):
    workers = job_ctx['job-workers']
    cid = job_ctx['current-worker']
    args = job_ctx['worker-arguments']
    arg = args[cid]
    if 'image-from-worker' not in arg:
        return True
    kbid = arg['image-from-worker']
    for i in range(cid - 1, -1, -1):
        if workers[i] == 'kvmmanager':
            if 'image-from-worker' in args[i] and args[i]['image-from-worker'] == kbid:
                return False
            else:
                return True
        elif workers[i] == 'kbuilder':
            return True
    return True

def is_image_deletion_necessary(job_ctx: dict):
    workers = job_ctx['job-workers']
    cid = job_ctx['current-worker']
    args = job_ctx['worker-arguments']
    arg = args[cid]
    if 'image-from-worker' not in arg:
        return True
    kbid = arg['image-from-worker']
    for i in range(cid + 1, len(args)):
        if workers[i] == 'kvmmanager':
            if 'image-from-worker' in args[i] and args[i]['image-from-worker'] == kbid:
                return False
            else:
                return True
        elif workers[i] == 'kbuilder':
            return True
    return True

async def write_ssh_key(key: str):
    async with aiofiles.open('workdir/ssh-private-key.id', 'w', encoding='utf-8') as fp:
        await fp.write(key)
    ssh_key_path = '/root/workdir/ssh-private-key.id'
    await run_async(os.chmod, ssh_key_path, S_IRUSR | S_IWUSR)
    return ssh_key_path

async def on_cancellation(jpctx: JobProcessorContext):
    if jpctx.variables['proc'] is not None:
        proc: asp.Process = jpctx.variables['proc']
        proc.send_signal(signal.SIGINT)
        await jpctx.worker.report_job_log_async(
            jpctx.job_ctx['job-id'],
            'Sent SIGINT to syz-crush for job cancellation'
        )
        await proc.wait()

async def cleanup_workdir():
    await asyncio.gather(
        run_async(shutil.rmtree, '/root/workdir', True),
        run_async(shutil.rmtree, '/root/crashes', True)
    )
    await asyncio.gather(
        run_async(os.makedirs, '/root/workdir', exist_ok=True),
        run_async(os.makedirs, '/root/crashes', exist_ok=True)
    )

async def detect_image_problem():
    cnt = 0
    async with aiofiles.open(os.path.join('/root/crashes/syz-crush.log'), 'r') as fp:
        while ln := await fp.readline():
            if 'failed to set up instance' in ln:
                cnt += 1
    return cnt

async def consume_kvmmanager(
    jpctx: JobProcessorContext,
    job_ctx: dict
):
    jpctx.register_cleanup_handler(on_cancellation)

    # Useful variables;
    job_id = job_ctx['job-id']
    argument = job_ctx['worker-arguments'][job_ctx['current-worker']]
    ninstances = argument['reproducer']['ninstance']

    # Clean up the work directories;
    await cleanup_workdir()
    await jpctx.worker.report_job_log_async(job_id, 'Workdir cleaned')

    # GCS;
    gcs_client = Client()
    bucket = gcs_client.bucket(os.environ['GCS_BUCKET_NAME'])
    # Image names;
    image_name = f'job-{job_ctx["job-id"]}'
    image_url = ''
    arch = ''
    vmlinux_path = ''
    ssh_key_path = ''
    if 'image-from-worker' in argument:
        wid = argument['image-from-worker']
        # sanity check;
        if wid < 0 or wid >= len(job_ctx['worker-results']):
            msg_str = 'Invalid \'image-from-worker\' ID: out of bound'
            await jpctx.worker.report_job_log_async(job_id, msg_str)
            return False, { 'result': 'failure', 'message': msg_str }
        if job_ctx['job-workers'][wid] != 'kbuilder':
            msg_str = 'Invalid \'image-from-worker\' ID: not kbuilder'
            await jpctx.worker.report_job_log_async(job_id, msg_str)
            return False, { 'result': 'failure', 'message': msg_str }
        # read stuff;
        image_url = job_ctx['worker-results'][wid]['vm-image-url']
        arch = job_ctx['worker-arguments'][wid]['kernel-arch']
        # download vmlinux;
        vmlinux = await run_async(
            bucket.get_blob, f'jobs/{job_ctx["job-id"]}/{wid}_kbuilder/vmlinux')
        if isinstance(vmlinux, Blob):
            await run_async(vmlinux.download_to_filename, '/root/workdir/vmlinux')
            vmlinux_path = '/root/workdir'
        if 'ssh-private-key' in job_ctx['worker-results'][wid]:
            ssh_key_path = await write_ssh_key(job_ctx['worker-results'][wid]['ssh-private-key'])
    elif 'image' in argument:
        image_url = argument['image']['image-url']
        arch = argument['image']['arch']
        if 'ssh-key' in argument['image']:
            ssh_key_path = await write_ssh_key(argument['image']['ssh-key'])
        if 'vmlinux-url' in argument['image']:
            vmlinux_gcs_url = argument['image']['vmlinux-url'].split(
                f"https://storage.cloud.google.com/{os.environ['GCS_BUCKET_NAME']}/")[1]
            vmlinux = await run_async(
                bucket.get_blob, vmlinux_gcs_url)
            if isinstance(vmlinux, Blob):
                await run_async(vmlinux.download_to_filename, '/root/workdir/vmlinux')
                vmlinux_path = '/root/workdir'
    else:
        await jpctx.worker.report_job_log_async(job_id, 'No image provided')
        return False, { 'result': 'failure', 'message': 'No image provided' }

    # if no kvmmanager between the latest kbuilder and myself;
    if is_image_creation_necessary(job_ctx):
        await create_image_from_gcs(image_url, image_name)
        await jpctx.worker.report_job_log_async(job_id, f'Made a GCE image: {image_name}')
    else:
        await jpctx.worker.report_job_log_async(job_id, f'Used the old GCE image: {image_name}')

    # make cfg;
    provider, vm_type = argument['machine-type'].split(':', maxsplit=1)
    # TODO: QEMU provider;
    cfg = {
        "name": f"linux-gce-{jpctx.worker.worker_hostname}",
        "target": f'linux/{arch}',
        "workdir": "/root/workdir",
        "syzkaller": "/root/syzkaller",
        "http": ":10000",
        "ssh_user": "root",
        "procs": argument['reproducer']['nproc'],
        "type": "gce",
        "vm": {
            "count": ninstances,
            "machine_type": vm_type,
            "gce_image": image_name
        }
    }
    if vmlinux_path != '':
        cfg['kernel_obj'] = vmlinux_path
    if ssh_key_path != '':
        cfg['sshkey'] = ssh_key_path
    cfg_fname = './gce.cfg'
    async with aiofiles.open(cfg_fname, 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(cfg))

    # repro;
    repro_name = {
        'log': 'execution.log',
        'c': 'creprog.c'
    }[argument['reproducer']['reproducer-type']]
    async with aiofiles.open(f'./{repro_name}', 'w', encoding='utf-8') as fp:
        await fp.write(argument['reproducer']['reproducer-text'])

    # compose the answer;
    ret_dict = {
        'result': 'success',
        'final-syzkaller-checkout': '',
        'message': '',
        'image-ability': 'normal'
    }

    await jpctx.worker.report_job_log_async(job_id, 'Preparing syzkaller suite')
    syz_res = await prepare_syzkaller(
        argument['reproducer']['syzkaller-checkout'],
        argument['reproducer']['syzkaller-rollback-to-latest']
    )

    ret_dict['final-syzkaller-checkout'] = syz_res[2]

    if not syz_res[0]:
        ret_dict['result'] = 'failure'
        ret_dict['message'] = syz_res[1]
        del ret_dict['image-ability']
        return False, ret_dict

    # invoke syz-crush;
    await jpctx.worker.report_job_log_async(job_id, 'Invoking syz-crush')
    jpctx.variables['proc'] = await asp.create_subprocess_exec(
        '/usr/local/bin/syz-crush',
        '-config', cfg_fname,
        '-restart_time', argument['reproducer']['restart-time'],
        '-infinite=false',
        repro_name, cwd='/root',
        stdout=await run_async(open, '/root/crashes/syz-crush.log', 'w', encoding='utf-8'),
        stderr=asp.STDOUT,
        stdin=asp.DEVNULL
    )
    proc = jpctx.variables['proc']
    await proc.wait()
    jpctx.variables['proc'] = None
    await jpctx.worker.report_job_log_async(job_id, 'syz-crush executed')

    # cleanup the image;
    if is_image_deletion_necessary(job_ctx):
        await delete_image_in_gce(image_name)
        await jpctx.worker.report_job_log_async(job_id, 'Image deletion is done')

    # collect stuff;
    # /root/crashes/<id>/ description, log$i, report$i, reproducer$i, tag$i;
    dirs = await run_async(os.listdir, '/root/crashes')
    if 'syz-crush.log' in dirs:
        dirs.remove('syz-crush.log')
    crash_files = []
    results = []

    # upload the syz-crush.log whatsoever;
    results += await run_async(transfer_manager.upload_many_from_filenames,
            bucket, filenames=['syz-crush.log'], source_directory='/root/crashes',
            blob_name_prefix=f'jobs/{job_ctx["job-id"]}/{job_ctx["current-worker"]}_kvmmanager/')
    crash_files.append('syz-crush.log')

    # detect the image problem;
    failed_to_setup_cnt = await detect_image_problem()
    # no crash detection only if all instances reveals broken images;
    if failed_to_setup_cnt == ninstances:
        ret_dict['image-ability'], ret_dict['message'] = 'error', 'Failed to set up instance'
        return True, ret_dict

    # crash collection;
    picked_id, crash_titles, upload_groups, n_crashes = await collect_crashes(
        argument['crash-collecting-policy'],
        dirs
    )

    # folders;
    upload_files = []
    for idx, grp in enumerate(upload_groups):
        for fname in grp:
            upload_files.append(os.path.join(str(idx), fname))
    crash_files += upload_files

    if picked_id == -1:
        ret_dict['image-ability'] = 'normal'
        ret_dict['message'] = 'No crash reproduced'
    else:
        crash_description = crash_titles[picked_id]
        is_special = crash_description in (
            'no output from test machine',
            'lost connection to test machine',
            'test machine is not executing programs'
        )

        if not is_special or n_crashes == ninstances - failed_to_setup_cnt:
            # all crashed;
            ret_dict['crash-description'] = crash_description
            ret_dict['picked-crash-id'] = picked_id
            # handle special crashes
            if is_special:
                ret_dict['message'] = 'Special crashes'
                ret_dict['image-ability'] = 'warning'
            else:
                ret_dict['message'] = 'Crashes'
        else:
            # there's a not reproduced data point;
            ret_dict['image-ability'] = 'normal'
            ret_dict['message'] = 'No crash reproduced'

        # upload root;
        crash_files += upload_groups[picked_id]
        results += await run_async(
            transfer_manager.upload_many_from_filenames,
            bucket, filenames=upload_groups[picked_id],
            source_directory=f'/root/crashes/{picked_id}',
            blob_name_prefix=f'jobs/{job_ctx["job-id"]}/{job_ctx["current-worker"]}_kvmmanager/'
        )

        # upload folder files;
        results += await run_async(
            transfer_manager.upload_many_from_filenames,
            bucket, filenames=upload_files, source_directory='/root/crashes',
            blob_name_prefix=f'jobs/{job_ctx["job-id"]}/{job_ctx["current-worker"]}_kvmmanager/'
        )
    # report;
    for name, result in zip(crash_files, results):
        if isinstance(result, Exception):
            await jpctx.worker.report_job_log_async(job_id, f'Failed to upload crash resource: {name}')
        else:
            await jpctx.worker.report_job_log_async(job_id, f'Successfully uploaded crash resource: {name}')
    return True, ret_dict
