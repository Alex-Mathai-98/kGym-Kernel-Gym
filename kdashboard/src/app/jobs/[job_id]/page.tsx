'use client';

import { JobDetail, JobOverview } from './components';
import { JobCtx } from '@/app/types';
import kbdr_cfg from '@/app/config.json';
import { Divider } from "@nextui-org/react";
import { useState, useMemo } from 'react';

export default function Page({ params }: { params: { job_id: string } }) {
    const [jobCtx, setJobCtx] = useState<JobCtx>({
        "job-id": params.job_id,
        "created-time": "",
        "current-worker": -1,
        "job-workers": [],
        "modified-time": "",
        "status": "aborted",
        "worker-arguments": [],
        "worker-results": [],
        "kv": {}
    });
    useMemo(() => {
        fetch(kbdr_cfg['KBDR_API_URL'] + '/jobs/' + params.job_id, {
            method: "GET",
            cache: "no-cache",
            redirect: 'follow'
        }).then((resp: Response) => {
            if (!resp.ok) {
                switch (resp.status) {
                    case 404: {
                        throw new Error('No such job');
                    }
                    case 422: {
                        throw new Error('Invalid job id');
                    }
                    default: {
                        throw new Error('Unexpected exception: ' + resp.statusText);
                    }
                }
            } else {
                return resp.json();
            }
        }).then((val: JobCtx) => {
            setJobCtx(val);
        })
    }, []);
    return (
        <div className='flex flex-col gap-1'>
            <p className="text-3xl font-sans font-bold subpixel-antialiased">Context of Job {params.job_id}</p>
            <Divider />
            <JobOverview jobCtx={jobCtx} />
            <Divider />
            <JobDetail jobCtx={jobCtx} />
        </div>
    );
}
