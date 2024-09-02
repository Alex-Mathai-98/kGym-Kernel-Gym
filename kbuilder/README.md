# kbuilder

## Objectives

- Run as a containerized app
- Receive build request
- Clone & checkout Linux commit automatically
- Build the kernel through `syz-build`
- Report & store relevant files into GCP object storage

## Documentation

### Environment Variables

- `KBDR_KBUILDER_RABBITMQ_CONN_URL`: Something like `amqp://username:password@host:port/<virtual_host>[?query-string]`
- `KBUILDER_KERNEL_WORK_DIR`: Something like `/root/work_dir`
- `KBUILDER_KERNEL_REPO_PATH`: Something like `/volume/repo` that contains the userspace image
- `KBUILDER_BACKPORT_COMMIT_JSON`: A path to a json file with backport commit information
- `GCS_BUCKET_NAME`: Name of the KBDr storage bucket
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the credential

### Backport Info JSON Example

```json
[
    {
        "fix_hash": "1d489151e9f9d1647110277ff77282fe4d96d09b",
        "fix_title": "objtool: Don't fail on missing symbol table"
    },
    {
        "fix_hash": "52a9dab6d892763b2a8334a568bd4e2c1a6fde66",
        "fix_title": "libsubcmd: Fix use-after-free for realloc(..., 0)"
    },
    {
        "fix_hash": "0711f0d7050b9e07c44bc159bbc64ac0a1022c7f",
        "fix_title": "pid: take a reference when initializing `cad_pid"
    },
    {
        "guilty_hash": "db2b0c5d7b6f19b3c2cab08c531b65342eb5252b",
        "fix_hash": "82880283d7fcd0a1d20964a56d6d1a5cc0df0713",
        "fix_title": "objtool: Fix truncated string warning"
    }
]
```

### Request Format

Worker argument example:

```json
{
    "kernel-git-url": "",
    "kernel-commit-id": "",
    "kernel-config": "",
    "userspace-image-name": "<Must be RAW disk>",
    "kernel-arch": "",
    "kernel-cmdline": "",
    // OPTIONAL: bug-metadata
    "bug-metadata": {
        "bug-id": "",
        "clean-crash-traces": []
    }
}
```

Worker result example: (all URLs are `Authenticated URL`)

```json
{
    "result": "success|failure",
    "message": "",
    "kernel-image-url": "",
    "vm-image-url": "",
    "kernel-config-url": "",
    "kernel-compile-commands-url": "",
    "ssh-private-key": "----- BEGIN RSA PRIVATE KEY ----", // if applicable;
    "final-kernel-config": "the final config file that was used in the build",
    "vmlinux-url": ""
}
```
