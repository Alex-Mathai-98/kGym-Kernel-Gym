'use client';

import { ScrollShadow, Code, Link, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@nextui-org/react";

export function kvmmanagerInfo({argument, result}: {argument: any, result: any}) {
    let reproType: string = argument['reproducer']['reproducer-type'] == "c" ? "C repro" : "Syz repro";
    const reproURL: string = URL.createObjectURL(new Blob([argument['reproducer']['reproducer-text']], { type: "text/plain" }))
    
    let imageArgument = (<></>);

    if ('image-from-worker' in argument) {
        imageArgument = (<p>From Worker #{argument['image-from-worker']}</p>);
    } else {
        imageArgument = (<p>{argument['image']['arch']}: <Link>{argument['image']['image-url']}</Link></p>);
    }

    let argumentComp = (
        <Table hideHeader aria-label="Worker Argument Information">
            <TableHeader>
                <TableColumn>KEY</TableColumn>
                <TableColumn>VALUE</TableColumn>
            </TableHeader>
            <TableBody>
                <TableRow key="machine-type">
                <TableCell>Executor Type</TableCell>
                <TableCell><Code>{argument['machine-type']}</Code></TableCell>
                </TableRow>
                <TableRow key="reproducer">
                <TableCell>Reproducer</TableCell>
                <TableCell><Link href={reproURL}>{reproType}</Link></TableCell>
                </TableRow>
                <TableRow key="reproducer-nproc">
                <TableCell># of Reproducer Processes</TableCell>
                <TableCell>{argument['reproducer']['nproc']}</TableCell>
                </TableRow>
                <TableRow key="reproducer-restart-time">
                <TableCell>Execution Duration</TableCell>
                <TableCell><Code>{argument['reproducer']['restart-time']}</Code></TableCell>
                </TableRow>
                <TableRow key="image">
                <TableCell>Image</TableCell>
                <TableCell>{imageArgument}</TableCell>
                </TableRow>
            </TableBody>
        </Table>
    );

    let resultComp = (<></>);
    
    if (result && result["result"] == "success" ) {
        resultComp = (
            <Table hideHeader aria-label="Worker Result Information">
                <TableHeader>
                    <TableColumn>KEY</TableColumn>
                    <TableColumn>VALUE</TableColumn>
                </TableHeader>
                <TableBody>
                    <TableRow key="message">
                    <TableCell>Message</TableCell>
                    <TableCell><pre>{result["message"]}</pre></TableCell>
                    </TableRow>
                    <TableRow key="image-ability">
                    <TableCell>Image Ability</TableCell>
                    <TableCell><pre>{result["image-ability"]}</pre></TableCell>
                    </TableRow>
                    <TableRow key="crash-description">
                    <TableCell>Crash Description</TableCell>
                    <TableCell>{result['crash-description'] ? result['crash-description'] : "<No Crashes Reproduced>"}</TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        );
    } else if (result) {
        resultComp = (
            <ScrollShadow className="max-h-64">
                <pre>{result["message"]}</pre>
            </ScrollShadow>
        );
    }
    
    return {
        title: "Kernel Tester",
        argument: argumentComp,
        result: resultComp
    }
}
