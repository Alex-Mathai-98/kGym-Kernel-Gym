# repo.py
import os, json, random, shutil, aiofiles
import asyncio.subprocess as asp
from typing import Tuple
from google.cloud.storage import Client, transfer_manager, Blob
from KBDr.kworker import run_async

repo_dir = os.environ['KBUILDER_KERNEL_REPO_PATH']

async def get_userspace_image(uimg_name: str) -> str:
    """ Pull the remote userspace image """
    await run_async(os.makedirs, os.path.join(repo_dir, 'userspace-images'), exist_ok=True)
    img_rel_path = os.path.join(repo_dir, 'userspace-images', uimg_name)
    ssh_key_rel_path = os.path.join(repo_dir, 'userspace-images', uimg_name + '.id')
    ssh_key = None
    storage_client = Client()
    bucket = storage_client.bucket(os.environ['GCS_BUCKET_NAME'])
    if not os.path.exists(img_rel_path):
        # pull the image from GCS;
        uimg_blob = bucket.get_blob(f'userspace-images/{uimg_name}')
        if not isinstance(uimg_blob, Blob):
            raise FileNotFoundError(f'Userspace image {uimg_name} doesn\' exist')
        await run_async(
            transfer_manager.download_chunks_concurrently,
            uimg_blob, img_rel_path)
    if not os.path.exists(ssh_key_rel_path):
        # find out if possible;
        key_obj = bucket.get_blob(f'userspace-images/{uimg_name}.id')
        if isinstance(key_obj, Blob):
            ssh_key_bytes: bytes = await run_async(key_obj.download_as_bytes)
            ssh_key = ssh_key_bytes.decode(encoding='utf-8', errors='replace')
            async with aiofiles.open(ssh_key_rel_path, 'w', encoding='utf-8') as fp:
                await fp.write(ssh_key)
    else:
        async with aiofiles.open(ssh_key_rel_path, 'r', encoding='utf-8') as fp:
            ssh_key = await fp.read()
    return os.path.abspath(img_rel_path), ssh_key

async def read_repo_metadata() -> Tuple[dict, set]:
    """ Read the repo metadata """
    repo_info = dict()
    # create when non-existing;
    if not os.path.exists(os.path.join(repo_dir, 'repo.json')):
        async with aiofiles.open(os.path.join(repo_dir, 'repo.json'), 'w', encoding='utf-8') as fp:
            await fp.write(json.dumps(dict()))
    # read info;
    async with aiofiles.open(os.path.join(repo_dir, 'repo.json'), 'r', encoding='utf-8') as fp:
        repo_info = json.loads(await fp.read())
    dirname = set()
    # for the purpose of uniqueness;
    for key in repo_info:
        dirname.add(repo_info[key])
    return repo_info, dirname

async def save_repo_metadata(repo_meta: dict):
    """ Save the repo metadata """
    async with aiofiles.open(os.path.join(repo_dir, 'repo.json'), 'w', encoding='utf-8') as fp:
        await fp.write(json.dumps(repo_meta))

def generate_random_dirname(dirname_set: set):
    def generate_dirname():
        ret = hex(random.randrange(0, 16 ** 8))[2:]
        ret = ('0' * (8 - len(ret))) + ret
        return ret
    key = generate_dirname()
    while key in dirname_set:
        key = generate_dirname()
    dirname_set.add(key)
    return key

async def get_local_repo(git_url: str):
    """ Get a fresh clone """
    url_to_repo, dirname_set = await read_repo_metadata()
    if git_url not in url_to_repo:
        key = generate_random_dirname(dirname_set)
        print(f'[kbuilder] Cloning from remote: {git_url}')
        # clone a bare repo;
        if os.path.exists(os.path.join(repo_dir, key)):
            await run_async(shutil.rmtree, os.path.join(repo_dir, key))
        code = await ((await asp.create_subprocess_exec(
            'git',
            'clone',
            '--bare',
            git_url,
            key,
            cwd=repo_dir,
            stdin=asp.DEVNULL,
            stdout=asp.DEVNULL,
            stderr=asp.DEVNULL)).wait())
        if code != 0:
            dirname_set.remove(key)
            return
        url_to_repo[git_url] = key
        await save_repo_metadata(url_to_repo)
        return key
    else:
        return url_to_repo[git_url]
