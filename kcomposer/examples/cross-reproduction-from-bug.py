# Example: launching cross-reproduction job;
# The following piece of script will iterate each bug in the bugs
# and use `compose_cross_reproduction_from_bug` to extract information
# from bug folder to compose arguments for workers.
# Since this is cross-reproduction, there is a kbuilder and multiple kvmmanagers for
# kernel building and reproduction respectively.

import os
import KBDr.kcomposer as kcomp

# Bug pairs: { "kbuilder's bug id": ["reproducer's bug id", ...] };

bugs = {
    "6a55a8466599070797063c2cb032c3da775a1aca": [
        "a85a4c2d373f7f8ff9ac5ee351e60d3c042cc781"
    ],
    "a5428a35500f99087c534be8fbe0c39ef0bdbf8e": [
        "eff0f44ed1cb54bc43f589d033731a826fb6fb59"
    ],
    "d91344d6575d14a43b04ea1d6718266ededf8186": [
        "de95b37d8a71730291dae5125367c41f66f80287"
    ],
    "eff0f44ed1cb54bc43f589d033731a826fb6fb59": [
        "a5428a35500f99087c534be8fbe0c39ef0bdbf8e"
    ]
}

# Directory of the bug dump;

bug_dir = ''

if __name__ == '__main__':
    # Create a session;
    session = kcomp.KBDrSession(os.environ['KBDR_RUNNER_API_BASE_URL'])
    for bug_id, repro_bug_list in bugs.items():
        # Use the built-in composer to get worker list, arguments, labels;
        workers, args, kv = kcomp.compose_cross_reproduction_from_bug(
            bug_dir,
            bug_id,
            repro_bug_list,
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
