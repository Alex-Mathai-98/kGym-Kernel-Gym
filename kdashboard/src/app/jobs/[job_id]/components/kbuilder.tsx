'use client';
import { ScrollShadow, Code, Link, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@nextui-org/react";

export function kbuilderInfo({argument, result}: {argument: any, result: any}) {
    let cmdline = (argument['kernel-cmdline'] == "" || !argument['kernel-cmdline']) ? "<No Command Supplied>" : argument['kernel-cmdline'];

    const kernelCfg: string = argument['kernel-config'];
    const kernelCfgURL: string = URL.createObjectURL(new Blob([kernelCfg], { type: "text/plain" }));

    // argument;
    let argumentComp = (
        <Table hideHeader aria-label="Worker Argument Information">
            <TableHeader>
                <TableColumn>KEY</TableColumn>
                <TableColumn>VALUE</TableColumn>
            </TableHeader>
            <TableBody>
                <TableRow key="kernel-git-url">
                <TableCell>Kernel Git URL</TableCell>
                <TableCell><Link href={argument['kernel-git-url']}>{argument['kernel-git-url']}</Link></TableCell>
                </TableRow>
                <TableRow key="kernel-commit-id">
                <TableCell>Kernel Commit ID</TableCell>
                <TableCell><Code>{argument['kernel-commit-id']}</Code></TableCell>
                </TableRow>
                <TableRow key="kernel-config">
                <TableCell>Kernel Config</TableCell>
                <TableCell><Link href={kernelCfgURL}>Download</Link></TableCell>
                </TableRow>
                {/* TODO: userspace image signed URL */}
                <TableRow key="userspace-image-name">
                <TableCell>Userspace Image</TableCell>
                <TableCell><Link>{argument['userspace-image-name']}</Link></TableCell>
                </TableRow>
                <TableRow key="kernel-arch">
                <TableCell>Kernel Architecture</TableCell>
                <TableCell><Code>{argument['kernel-arch']}</Code></TableCell>
                </TableRow>
                <TableRow key="kernel-cmdline">
                <TableCell>Kernel Command Line</TableCell>
                <TableCell><Code>{cmdline}</Code></TableCell>
                </TableRow>
                {argument['bug-metadata'] && (
                    <TableRow key="bug-metadata-gen">
                    <TableCell>Bug Metadata Generation</TableCell>
                    <TableCell>
                        Enabled
                    </TableCell>
                    </TableRow>
                )}
                {argument['bug-metadata'] && (
                    <TableRow key="bug-id">
                    <TableCell>Bug ID</TableCell>
                    <TableCell>
                        <Link href={"https://syzkaller.appspot.com/bug?id=" + argument['bug-metadata']['bug-id']}>
                            {argument['bug-metadata']['bug-id']}
                        </Link>
                    </TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );
    /*
    {
        "result": "failure",
        "message": "Failed to build"
      }
      {
        "result": "success",
        "kernel-compile-commands-url": "https://storage.cloud.google.com/kbdr-beta-v0-2-4/jobs/00000003/compile_commands.json",
        "kernel-image-url": "https://storage.cloud.google.com/kbdr-beta-v0-2-4/jobs/00000003/kernel",
        "kernel-config-url": "https://storage.cloud.google.com/kbdr-beta-v0-2-4/jobs/00000003/kernel.config",
        "vm-image-url": "https://storage.cloud.google.com/kbdr-beta-v0-2-4/jobs/00000003/image.tar.gz",
        "message": "Everything OK"
      },
    */
    let resultComp = <></>;
    if (result && result["result"]) {
        resultComp = result["result"] == 'success' ? (
        <Table hideHeader aria-label="Successful Result">
            <TableHeader>
                <TableColumn>KEY</TableColumn>
                <TableColumn>VALUE</TableColumn>
            </TableHeader>
            <TableBody>
                <TableRow key="kernel-compile-commands-url">
                <TableCell>compile_commands.json</TableCell>
                <TableCell><Link>{result['kernel-compile-commands-url']}</Link></TableCell>
                </TableRow>
                <TableRow key="kernel-image-url">
                <TableCell>Kernel Image</TableCell>
                <TableCell><Link>{result['kernel-image-url']}</Link></TableCell>
                </TableRow>
                <TableRow key="kernel-config-url">
                <TableCell>Kernel Config</TableCell>
                <TableCell><Link>{result['kernel-config-url']}</Link></TableCell>
                </TableRow>
                <TableRow key="vm-image-url">
                <TableCell>Disk Image</TableCell>
                <TableCell><Link>{result['vm-image-url']}</Link></TableCell>
                </TableRow>
            </TableBody>
        </Table>) : (
            <ScrollShadow className="max-h-64">
                <pre>{result["message"]}</pre>
            </ScrollShadow>
        );
    }


    return {
        title: "Kernel Builder",
        argument: argumentComp,
        result: resultComp
    }
}
