"use client";

import { JobItemRowCell } from "../components/job";
import kbdr_cfg from '@/app/config.json';
import { JobDigest } from "../types";
import React, { useEffect, useState, Key, useMemo } from "react";
import { Skeleton, Popover, PopoverTrigger, PopoverContent, Divider, CircularProgress, Progress } from "@nextui-org/react";
import { SearchOutlined } from "@ant-design/icons";

import {
    Table,
    TableHeader,
    TableColumn,
    TableBody,
    TableRow,
    TableCell,
    Input,
    Button,
    DropdownTrigger,
    Dropdown,
    DropdownMenu,
    DropdownItem,
    Chip,
    User,
    Pagination,
    Selection,
    ChipProps,
    SortDescriptor
  } from "@nextui-org/react";
// import { useRouter } from "next/router";
import { useRouter } from "next/navigation";

export default function Page() {

    const allColumns = [
        {key: "job-id", title: "Job ID"},
        {key: "status", title: "Status"},
        {key: "current-worker", title: "Current Worker"},
        {key: "modified-time", title: "Modified Time"},
        {key: "created-time", title: "Created Time"}
    ];

    const [totalEntries, setTotalEntries] = useState(10);
    const [limit, setLimit] = useState(20);
    const [page, setPage] = useState(1);
    const [totalPage, setTotalPage] = useState(10);
    const [isLoaded, setIsLoaded] = useState(false);
    const [loadingMode, setLoadingMode] = useState<("by_modified_time" | "by_created_time")>("by_modified_time")
    const [visibleColumns, setVisibleColumns] = useState<Selection>(new Set(["job-id", "status", "current-worker", "job-workers", "modified-time"]));
    const headerColumns = useMemo(() => {
        if (visibleColumns === "all")
            return allColumns;
        return allColumns.filter((column) => Array.from(visibleColumns).includes(column.key));
    }, [visibleColumns, allColumns]);
    const [startTime, setStartTime] = useState("0000-00-00T00:00:00.000000");
    const [endTime, setEndTime] = useState("9999-99-99T99:99:99.999999");
    const [jobList, setJobList] = useState<Array<JobDigest>>([]);

    useEffect(function () {
        setIsLoaded(false);
        let url_params = new URL(kbdr_cfg['KBDR_API_URL'] + '/jobs/');
        url_params.searchParams.append('limit', limit.toString());
        url_params.searchParams.append('start', ((page - 1) * limit).toString());
        url_params.searchParams.append('mode', loadingMode);
        url_params.searchParams.append('start_time', startTime);
        url_params.searchParams.append('end_time', endTime);
        const req = fetch(url_params.toString(), {
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
        }, (reason: any) => {
            console.log(reason);
        }).then((data: any) => {
            setJobList(data.result);
            setTotalPage(Math.ceil(data.total / limit));
            setTotalEntries(data.total);
            setIsLoaded(true);
        });
    }, [limit, page, startTime, endTime, loadingMode]);

    const [selectedJobs, setSelectedJobs] = useState<Selection>(new Set([]));
    const onRowsPerPageChange = React.useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
        setLimit(Number(e.target.value));
        setPage(1);
    }, []);
    const isButtonDisabled = useMemo<boolean>(() => {
        if (selectedJobs == 'all')
            return false;
        return selectedJobs.size == 0;
    }, [selectedJobs]);

    type restartStateType = "idle" | "restarting" | "restarted";

    const [restartState, setRestartState] = useState<restartStateType>("idle"); 

    const [restartRequests, setRestartRequests] = useState<Set<string>>(new Set<string>([]));
    const [errorRequests, setErrorRequests] = useState<Set<string>>(new Set<string>([]));
    const [finishedRequests, setFinishedRequests] = useState<Set<string>>(new Set<string>([]));
    const restartProgressPercentage = useMemo(() => {
        if (restartRequests.size == 0) {
            return 0;
        }
        return 100 * (finishedRequests.size + errorRequests.size) / restartRequests.size;
    }, [errorRequests, finishedRequests, restartRequests]);

    const ableToReset = useMemo<boolean>(() => {
        return !(restartRequests.size != 0 && finishedRequests.size + errorRequests.size == restartRequests.size);
    }, [errorRequests, finishedRequests, restartRequests]);

    const restartRows = function(e: any) {
        if (restartState == "idle") {
            setRestartState("restarting");
            setErrorRequests(new Set<string>([]));
            setFinishedRequests(new Set<string>([]));

            let jobs: Array<string>;
            if (selectedJobs == 'all') {
                jobs = jobList.map((value: JobDigest, index: number, array: JobDigest[]) => value["job-id"]);
            } else {
                jobs = Array.from((selectedJobs as Set<string>).values());
            }
            let requests = new Set<string>([]);
            for (var jid in jobs) {
                const job_id = jobs[jid];
                const req = fetch(kbdr_cfg.KBDR_API_URL + '/jobs/' + job_id + '/restart', {
                    method: "POST",
                    cache: "no-cache",
                    redirect: 'follow'
                }).then((resp: Response) => {
                    if (resp.ok) {
                        setFinishedRequests(new Set([...finishedRequests, job_id]));
                    } else {
                        setErrorRequests(new Set([...errorRequests, job_id]));
                    }
                }, (reason: any) => {
                    setErrorRequests(new Set([...errorRequests, job_id]));
                });
                requests.add(job_id);
            }
            setRestartRequests(requests);
        } else {
        }
    };

    const onReset = (e: any) => {
        setErrorRequests(new Set<string>([]));
        setFinishedRequests(new Set<string>([]));
        setRestartRequests(new Set<string>([]));
        setRestartState("idle");
    };

    const [inputValue, setInputValue] = useState("");
    const router = useRouter();

    const onJobIDSubmit = (e: any) => {
        router.replace('/jobs/' + inputValue);
        // bye bye;
    };

    const restartingJobList = useMemo(() => {
        return (
            <div className="flex flex-col gap-1">
                {
                    Array.from(restartRequests.keys()).map((val: string) => (
                        <div key={val} className="flex flex-row justify-between items-center">
                            <div className="flex flex-row gap-1 justify-between items-center" key={val}>
                                <CircularProgress size="sm" isIndeterminate={!(finishedRequests.has(val) || errorRequests.has(val))} aria-label="Loading..." />
                                <p className="text-sm">{val}</p>
                            </div>
                            {
                                (errorRequests.has(val) && <Chip size="sm" color="danger">Error</Chip>) ||
                                (finishedRequests.has(val) && <Chip size="sm" color="success">Success</Chip>) ||
                                (<></>)
                            }
                        </div>
                    ))
                }
            </div>
        );
    }, [restartRequests, finishedRequests, errorRequests]);

    const isGotoButtonDisabled = useMemo<boolean>(() => {
        return inputValue.match('^[0-9a-f]{8}$') ? false : true;
    }, [inputValue]);
    
    const tableControl = useMemo(() => {
        return (
            <div className="flex flex-col gap-4">
                <div className="flex justify-between gap-3 items-center">
                    <div className="flex flex-row grow gap-4 items-center">
                        <Input
                        isClearable
                        size="sm"
                        className="w-full justify-self-stretch"
                        placeholder="Go to Job by ID..."
                        value={inputValue}
                        onValueChange={setInputValue}
                        onClear={() => {setInputValue("")}}
                        />
                        <Button color="primary" isDisabled={isGotoButtonDisabled} onClick={onJobIDSubmit}>
                            Go
                        </Button>
                    </div>
                    <div className="flex flex-row gap-4">
                        <Dropdown>
                            <DropdownTrigger className="hidden sm:flex">
                                <Button variant="flat">
                                Columns
                                </Button>
                            </DropdownTrigger>
                            <DropdownMenu
                                className="text-foreground bg-background"
                                disallowEmptySelection
                                aria-label="Table Columns"
                                closeOnSelect={false}
                                selectedKeys={visibleColumns}
                                selectionMode="multiple"
                                onSelectionChange={setVisibleColumns}
                            >
                                {allColumns.map((column) => (
                                <DropdownItem key={column.key} className="capitalize">
                                    {column.title}
                                </DropdownItem>
                                ))}
                            </DropdownMenu>
                        </Dropdown>
                        <Dropdown>
                            <DropdownTrigger className="hidden sm:flex">
                                <Button variant="flat">
                                Sort by
                                </Button>
                            </DropdownTrigger>
                            <DropdownMenu
                                className="text-foreground bg-background"
                                aria-label="Table Sort by"
                                disallowEmptySelection
                                closeOnSelect={true}
                                selectedKeys={[loadingMode]}
                                selectionMode='single'
                                onAction={(key: Key) => { setLoadingMode(key.toString() as ("by_created_time" | "by_modified_time")); }}
                            >
                                <DropdownItem key="by_created_time">
                                    By Created Time
                                </DropdownItem>
                                <DropdownItem key="by_modified_time">
                                    By Modified Time
                                </DropdownItem>
                            </DropdownMenu>
                        </Dropdown>
                        <Popover placement="bottom" showArrow={true}>
                            <PopoverTrigger>
                                <Button isDisabled={isButtonDisabled} onClick={restartRows}>Restart Jobs</Button>
                            </PopoverTrigger>
                            <PopoverContent className="text-foreground bg-background">
                                <div className="min-w-[300px] flex flex-col gap-1">
                                    <p className="text-base font-bold">Restart Progress</p>
                                    <Divider />
                                    {restartingJobList}
                                    <Divider />
                                    <Progress value={restartProgressPercentage} />
                                    <Button isDisabled={ableToReset} size="sm" onClick={onReset}>Reset</Button>
                                </div>
                            </PopoverContent>
                        </Popover>
                    </div>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-default-400 text-small">Total {totalEntries} jobs</span>
                    <label className="flex items-center text-default-400 text-small">
                        Rows per page:
                        <select
                        className="bg-transparent outline-none text-default-400 text-small"
                        onChange={onRowsPerPageChange}
                        defaultValue={20}
                        >
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                        </select>
                    </label>
                </div>
            </div>
        )
    }, [restartingJobList, totalEntries, visibleColumns, inputValue]);

    const tableHeader = useMemo(() => {
        return (
            <TableHeader columns={headerColumns}>
                { 
                    (column) => (
                        <TableColumn key={column.key}>
                            {column.title}
                        </TableColumn>
                    )
                }
            </TableHeader>
        );
    }, [headerColumns])

    return (
        <div className="flex flex-col gap-4">
            <h1 className="text-3xl font-sans font-bold subpixel-antialiased">Job List</h1>
            <Skeleton isLoaded={isLoaded} className="rounded-lg min-h-96 w-full">
                <Table
                    aria-label="Job list"
                    isHeaderSticky
                    bottomContent={<Pagination className='mx-auto' total={totalPage} initialPage={1} page={page} onChange={setPage} />}
                    bottomContentPlacement="outside"
                    selectedKeys={selectedJobs}
                    selectionMode="multiple"
                    topContent={tableControl}
                    topContentPlacement="outside"
                    onSelectionChange={setSelectedJobs}
                >
                    {tableHeader}
                    <TableBody emptyContent={"No jobs listed"} items={jobList}>
                        {(item) => (
                            <TableRow key={item["job-id"]} >
                                {(cln) => <TableCell>{JobItemRowCell(item, cln)}</TableCell>}
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </Skeleton>
        </div>
    )
}
