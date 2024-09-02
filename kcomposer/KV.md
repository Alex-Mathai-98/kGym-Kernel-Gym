# Key-Value Conventions

- `composed-by`: str, composer's name, following the convention of `org.composer_name`

## Kernel Image

- `contains-bug-kernel-{kernel_bug_id}-at`: int, the worker number of the kbuilder that compiled the kernel from `kernel_bug_id`
- `contains-kernel-commit-{commit_id}-at`: int, the worker number of the kbuilder that compiled the kernel of `commit_id`
- `cross-reproduction-kbug-{kernel_bug_id}-rbug-{repro_id}`: int, the worker number of the kvmmanager that run reproducer from `repro_id` on `kernel_bug_id`'s kernel
- `bug-reproduction-{bug_id}`: int, the worker number of the kvmmanager that run its own reproducer
