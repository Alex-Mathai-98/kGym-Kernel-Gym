'use client';

import kbdr_cfg from '@/app/config.json';
import { Pagination, Accordion, Skeleton, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Button } from "@nextui-org/react";
import { JobLogAccordionItem } from "@/app/components/log";
import { useEffect, useState } from 'react';
import { JobLogCtx } from '@/app/types';

export default function Page() {
    const [limit, setLimit] = useState(20);
    const [cpage, setCPage] = useState(1);
    const [isLoaded, setIsLoaded] = useState(false);
    const [totalPages, setTotalPages] = useState(10);
    const [comp, setComp] = useState(<></>);

    const getLogDisplay = (page: number) => {
        setIsLoaded(false);
        let url_params = new URL(kbdr_cfg['KBDR_API_URL'] + '/system/displays/jobs/log');
        url_params.searchParams.append('limit', limit.toString());
        url_params.searchParams.append('start', ((page - 1) * limit).toString());
        fetch(url_params.toString(), {
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
            }
            return resp.json();
        }).then((data: any) => {
            setComp(
                <Accordion>
                    {data.result.map((value: JobLogCtx, index: number, array: JobLogCtx[]) => {
                        return JobLogAccordionItem({show_job_id: true, key: index, log: value});
                    })}
                </Accordion>
            );
            setTotalPages(Math.ceil(data.total / limit));
            setIsLoaded(true);
        });
    };
    useEffect(() => { getLogDisplay(cpage); }, [cpage, limit]);
    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-row">
                <h1 className="text-3xl font-sans font-bold subpixel-antialiased">Job Log Display</h1>
                <div className="flex-grow"></div>
                <Dropdown>
                    <DropdownTrigger>
                        <Button 
                        variant="bordered"
                        >
                        Rows: {limit}
                        </Button>
                    </DropdownTrigger>
                    <DropdownMenu 
                        className="text-foreground bg-background"
                        aria-label="Set page limit" 
                        onAction={(key) => setLimit(key as number)}
                    >
                        <DropdownItem key={10}>10</DropdownItem>
                        <DropdownItem key={20}>20</DropdownItem>
                        <DropdownItem key={50}>50</DropdownItem>
                    </DropdownMenu>
                </Dropdown>
            </div>
            <Skeleton className="rounded-lg min-h-96" isLoaded={isLoaded}>
                <div className="flex flex-col gap-1">
                    {isLoaded && comp}
                    <Pagination className='mx-auto' total={totalPages} initialPage={1} onChange={setCPage} />
                </div>
            </Skeleton>
        </div>
    );
}
