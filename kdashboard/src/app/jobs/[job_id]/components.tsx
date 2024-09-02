'use client';

import '@/app/globals.css';
import { Code, Tabs, Tab, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Pagination, Skeleton, AccordionItem, Accordion } from "@nextui-org/react";
import React, { useEffect, useState } from 'react';
import { JobLogCtx, JobCtx, KV } from "@/app/types"
import kbdr_cfg from '@/app/config.json';
import { JobLogAccordionItem } from "@/app/components/log";
import { StatusChip, FormattedTime } from "@/app/components/job";
import { kbuilderInfo } from './components/kbuilder';
import { kvmmanagerInfo } from './components/kvmmanager';

export function JobOverview(
    { jobCtx } : { jobCtx: JobCtx }
) {
    return (
        <Table hideHeader removeWrapper aria-label="Job Information">
            <TableHeader>
                <TableColumn>KEY</TableColumn>
                <TableColumn>VALUE</TableColumn>
            </TableHeader>
            <TableBody>
                <TableRow key="status">
                <TableCell>Status</TableCell>
                <TableCell><StatusChip status={jobCtx.status} /></TableCell>
                </TableRow>
                <TableRow key="created_time">
                <TableCell>Created Time</TableCell>
                <TableCell><FormattedTime timeString={jobCtx['created-time']} /></TableCell>
                </TableRow>
                <TableRow key="modified_time">
                <TableCell>Modified Time</TableCell>
                <TableCell><FormattedTime timeString={jobCtx['modified-time']} /></TableCell>
                </TableRow>
            </TableBody>
        </Table>
    );
}

export function JobWorker(
    { worker_name, worker_id,  isCurrentWorker, argument, result }:
    { worker_name: string, worker_id: number, isCurrentWorker: boolean, argument: any, result: any }) {
    let subtitle = "";
    if (isCurrentWorker) {
        subtitle = "Current Worker"
    }
    type workerInfoFunc = ({argument, result}: {argument: any, result: any}) => {title: string, argument: JSX.Element, result: JSX.Element};
    const worker_map: { [key: string]: workerInfoFunc }  = {
        "kbuilder": kbuilderInfo,
        "kvmmanager": kvmmanagerInfo
    };
    const info = (worker_map[worker_name]({
        argument: argument,
        result: result
    }));
    return (
        <AccordionItem key={worker_id.toString()} title={<p className="text-xl font-bold subpixel-antialiased">{worker_id} - {info.title}</p>} subtitle={subtitle} >
            <div className='flex flex-col gap-4'>
                <p className="text-lg font-bold subpixel-antialiased">Argument</p>
                <div className='mx-1'>{info.argument}</div>
                {result ? (<><p className="text-lg font-bold subpixel-antialiased">Results</p>
                <div className='mx-1'>{info.result}</div></>) : (<></>)}
            </div>
        </AccordionItem>
    );
}

export function JobWorkerPanel({ jobCtx }: { jobCtx: JobCtx }) {
    return (
        <Accordion>
            {
                jobCtx['job-workers'].map(function(val: string, idx: number, arr: string[]) {
                    return JobWorker({
                        worker_id: idx,
                        worker_name: val,
                        isCurrentWorker: (idx == jobCtx['current-worker']),
                        argument: jobCtx['worker-arguments'][idx],
                        result: jobCtx['worker-results'][idx]
                    })
                })
            }
        </Accordion>
    );
}

export function JobLogPanel({ jobId }: { jobId: string }) {
    const [limit, setLimit] = useState(20);
    const [cpage, setCPage] = useState(1);
    const [totalPages, setTotalPages] = useState(10);
    const [comp, setComp] = useState(<></>);
    const [isLoaded, setIsLoaded] = useState(false);
    const getLogPage = (page: number) => {
        setIsLoaded(false);
        let url_params = new URL(kbdr_cfg['KBDR_API_URL'] + '/jobs/' + jobId + '/log');
        url_params.searchParams.append('job_id', jobId);
        url_params.searchParams.append('limit', limit.toString());
        url_params.searchParams.append('start', ((page - 1) * limit).toString());
        fetch(url_params.toString(), { method: "GET", cache: "no-cache", redirect: 'follow' })
        .then((resp: Response) => resp.json())
        .then((data: any) => {
            setComp(
                <Accordion>
                    {data.result.map((value: JobLogCtx, index: number, array: JobLogCtx[]) => {
                        return JobLogAccordionItem({show_job_id: false, key: index, log: value});
                    })}
                </Accordion>
            );
            setTotalPages(Math.ceil(data.total / limit));
            setIsLoaded(true);
        });
    };
    useEffect(() => { getLogPage(cpage); }, [cpage, limit]);

    return (
        <Skeleton className="rounded-lg min-h-96" isLoaded={isLoaded}>
            <div className="flex flex-col gap-1">
                {comp}
                <Pagination className='mx-auto' total={totalPages} initialPage={1} onChange={setCPage} />
            </div>
        </Skeleton>
    )
}

export function JobLabelPanel({ kv }: { kv: KV }) {
    return (
        <div className="mx-1">
            <Table aria-label="Labels" aria-placeholder='No labels'>
                <TableHeader>
                    <TableColumn>Key</TableColumn>
                    <TableColumn>Value</TableColumn>
                </TableHeader>
                <TableBody>
                    { (kv && Object.keys(kv).map((key: string, idx: number, arr: string[]) => {
                        return (
                            <TableRow key={key}>
                                <TableCell><Code>{key}</Code></TableCell>
                                <TableCell><Code>{kv[key]}</Code></TableCell>
                            </TableRow>
                        );
                    })) }
                </TableBody>
            </Table>
        </div>
    )
}

export function JobDetail({ jobCtx }: { jobCtx: JobCtx }) {
    return (
        <Tabs aria-label="Options">
            <Tab key="args" title="Workers">
                {<JobWorkerPanel jobCtx={jobCtx} />}
            </Tab>
            <Tab key="log" title="Log">
                {<JobLogPanel jobId={jobCtx['job-id']} />}
            </Tab>
            <Tab key="kv" title="Labels">
                {<JobLabelPanel kv={jobCtx.kv} />}
            </Tab>
        </Tabs>
    )
}
