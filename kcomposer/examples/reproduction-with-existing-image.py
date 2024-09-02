# Example: launching reproduction job with built kernels;
# The following piece of script will iterate each bug in the bugs
# and use `composers.compose_cross_reproduction` to extract information
# from bug folder to compose arguments for workers.
# Since this is cross-reproduction, there are kbuilder and kvmmanagers for
# kernel building and reproduction respectively.

import os
import KBDr.kcomposer as kcomp

# Directory of the bug dump;

bug_dir = ''

if __name__ == '__main__':
    # Create a session;
    session = kcomp.KBDrSession(os.environ['KBDR_RUNNER_API_BASE_URL'])

    # Get the job context of the job to reuse;
    job_ctx = session.get_job_ctx('<Job ID>')
    # Get the image from 0th worker;
    url, arch, vmlinux = kcomp.models.image_from_existing_job(job_ctx, 0)

    workers = ['kvmmanager']
    arguments = [kcomp.models.kvmmanager_argument(
        kcomp.models.reproducer_from_bug(
            kcomp.models.open_bug(bug_dir, '<Bug ID>'),
            8, '10m', 5
        ),
        machine_type='gce:e2-standard-2',
        image_url=url,
        arch=arch,
        vmlinux_url=vmlinux
    )]
    labels = {
        'composed-by': 'custom.compose_bug_reproduction_with_existing_kernel',
        'bug-reproduction-for': '<Bug ID>',
        'reused-job': '0000011f'
    }

    print(session.create_job(workers, arguments, labels))
