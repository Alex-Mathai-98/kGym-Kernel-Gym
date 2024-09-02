'use client';

import { JobLogCtx, WorkerLogCtx } from '@/app/types';
import { Chip, Accordion, AccordionItem, ScrollShadow } from "@nextui-org/react";
import { FormattedTime, GetUTCTime, TimeAgoString } from './job';
import { ToolOutlined, CloudOutlined } from '@ant-design/icons';

export function JobLogAccordionItem({ show_job_id, key, log }: { show_job_id: boolean, key: number, log: JobLogCtx }) {
    let messageDigest = log.log.split('\n')[0];
    if (messageDigest.length > 50)
        messageDigest = messageDigest.substring(0, 50) + '...';
    let icon = log.worker == 'kbuilder' ? (<ToolOutlined />) : (<CloudOutlined />);
    return (
        <AccordionItem
            key={key}
            startContent={icon}
            subtitle={
            <p className="flex">
                Updated {TimeAgoString(log['log-time'])}, from worker {log['worker']} @ {log['worker-hostname']}
            </p>
            }
            title={
            <div className='flex flex-row gap-1'>
                {show_job_id && <Chip color="primary" variant="bordered">{log['job-id']}</Chip>}
                <p>{messageDigest}</p>
            </div>
            }
            aria-label={log.log}
        >
            <p>Log at <FormattedTime timeString={log['log-time']} /></p>
            <ScrollShadow className="max-h-64">
                <pre>
                    {log.log}
                </pre>
            </ScrollShadow>
        </AccordionItem>
    )
}

export function WorkerLogAccordionItem({ key, log }: { key: number, log: WorkerLogCtx }) {
    let messageDigest = log.log.split('\n')[0];
    if (messageDigest.length > 50)
        messageDigest = messageDigest.substring(0, 50) + '...';
    let icon = log.worker == 'kbuilder' ? (<ToolOutlined />) : (<CloudOutlined />);
    return (
        <AccordionItem
            key={key}
            startContent={icon}
            subtitle={
            <p className="flex">
                Updated {TimeAgoString(log['log-time'])}, from worker {log['worker']} @ {log['worker-hostname']}
            </p>
            }
            title={messageDigest}
        >
            <p>Log at <FormattedTime timeString={log['log-time']} /></p>
            <ScrollShadow className="max-h-64">
                <pre>
                    {log.log}
                </pre>
            </ScrollShadow>
        </AccordionItem>
    )
}
