# Testcase: Bug Reproduction Test

import os, json, argparse
import KBDr.kcomposer as kcomp

# Directory of the bug dump;

bug_dir = ''

if __name__ == '__main__':

    ap = argparse.ArgumentParser('KBDr-Runner Tester: Bug Reproduction')
    ap.add_argument('testcase')

    arg = ap.parse_args()

    with open(arg.testcase, 'r') as fp:
        bugs = json.load(fp)

    # Create a session;
    session = kcomp.KBDrSession(os.environ['KBDR_RUNNER_API_BASE_URL'], 10)
    for bug_id in bugs:
        # Use the built-in composer to get worker list, arguments, labels;
        try:
            workers, arguments, labels = kcomp.compose_bug_reproduction_from_bug(
                bug_dir,
                bug_id,
                'stretch.raw',
                metadata=False,
                compiler='clang',
                linker='ld.lld'
            )
            # Modify anything if you want;
            # Please refer to kbuilder/README.md or kvmmanager/README.md for
            # argument format;

            # with open(f'{bug_id}.config') as fp:
            #     cfg = fp.read()
            # arguments[0]['kernel-config'] = cfg

            job_id = session.create_job(workers, arguments, labels)
            print(f'{job_id}: Dispatched')
        except:
            pass
