# Example: launching bug-reproduction job;
# The following piece of script will iterate each bug in the bugs
# and use `compose_bug_reproduction_from_bug` to extract information
# from bug folder to compose arguments for workers.

import os
import KBDr.kcomposer as kcomp

# Bug pairs: { "kbuilder's bug id": ["reproducer's bug id", ...] };

bugs = [
    "29dc1bfc5b84e25cd68b61bc98c924d3548b3b2c"
]

# Directory of the bug dump;

bug_dir = ''

if __name__ == '__main__':
    # Create a session;
    session = kcomp.KBDrSession(os.environ['KBDR_RUNNER_API_BASE_URL'])
    for bug_id in bugs:
        # Use the built-in composer to get worker list, arguments, labels;
        workers, args, kv = kcomp.compose_bug_reproduction_from_bug(
            bug_dir,
            bug_id,
            'buildroot.raw',
            False,
            'gcc',
            'ld'
        )

        # Modify anything if you want;
        # Please refer to kbuilder/README.md or kvmmanager/README.md for
        # argument format;

        # with open(f'{bug_id}.config') as fp:
        #     cfg = fp.read()
        # arguments[0]['kernel-config'] = cfg

        session.create_job(workers, args, kv)
