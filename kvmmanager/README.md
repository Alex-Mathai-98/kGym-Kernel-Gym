# kvmmanager

This module is a wrapper that calls syz-crush and collect report files.

## Environment Variables

- `GOOGLE_APPLICATION_CREDENTIALS`: providing the credential for syz-crush
- `KBDR_VMMANAGER_RABBITMQ_CONN_URL`: RabbitMQ URL
- `GCS_BUCKET_NAME`: bucket name

## Job Argument Format

```json
{
    "reproducer": {
        "reproducer-type": "c|log",
        "reproducer-text": "",
        "syzkaller-checkout": "which checkout to use",
        "syzkaller-rollback-to-latest": true, // whether to rollback;
        "nproc": "number of reproducer process",
        "restart-time": "5m",
        "ninstance": 4 // multi VM;
    },
    "image": {
        "image-url": "GCS URL to the image to be tested",
        "arch": "amd64|386",
        "vmlinux-url": ""
    },
    // or get image info from previous worker result;
    "image-from-worker": "<previous worker number>",
    "machine-type": "local:qemu|gce:e2-standard-2",
    "crash-collecting-policy": "random"
}
```

### Job Result Format:

```json
{
    "result": "success|failure",
    "message": "",
    "final-syzkaller-checkout": "",
    "image-ability": "normal|warning|error",
    // if there's no crash, then there'll be no description & picked crash ID;
    "crash-description": "",
    "picked-crash-id": 0
}
```
