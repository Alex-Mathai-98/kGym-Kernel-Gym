'use client';

import { Chip } from "@nextui-org/react";
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Pagination, Spinner, getKeyValue } from "@nextui-org/react";
import { JobDigest } from "../types";
import { Key } from "react";
import TimeAgo from 'javascript-time-ago';
import en from 'javascript-time-ago/locale/en';
import Link from "next/link";

export function StatusChip({ status }: { status: string }) {
    const status_color: { [key: string]: "primary" | "default" | "danger" | "secondary" | "success" | "warning" | undefined } = {
        "in_progress": "primary",
        "pending": "default",
        "aborted": "danger",
        "finished": "success",
        "waiting": "secondary"
    };
    const status_text: { [key: string]: string } = {
        "in_progress": "In Progress",
        "pending": "Pending",
        "aborted": "Aborted",
        "finished": "Finished",
        "waiting": "Waiting"
    };
    return (<Chip color={status_color[status]}>{status_text[status]}</Chip>);
}

export function GetUTCTime(timeString: string) {
    let utcDt = new Date(timeString);
    return (new Date(Date.UTC(
        utcDt.getFullYear(),
        utcDt.getMonth(),
        utcDt.getDate(),
        utcDt.getHours(),
        utcDt.getMinutes(),
        utcDt.getSeconds(),
        utcDt.getMilliseconds(),
    )))
}

export function FormattedTime({ timeString }: { timeString: string }) {
    return GetUTCTime(timeString).toString();
}

export function TimeAgoString(timeString: string) {
    TimeAgo.addLocale(en);
    let timeAgoTool = new TimeAgo('en-US');
    return timeAgoTool.format(GetUTCTime(timeString));
}

export function JobItemRowCell(digest: JobDigest, column: Key) {
    switch (column) {
        case "job-id": {
            return (<Link href={"/jobs/" + digest["job-id"]} color="primary">{digest["job-id"]}</Link>);
        }
        case "created-time": {
            return TimeAgoString(digest["created-time"]);
        }
        case "modified-time": {
            return TimeAgoString(digest["modified-time"]);
        }
        case "status": {
            return (<StatusChip status={digest["status"]} />);
        }
        case "current-worker": {
            return (<p>{digest["current-worker"]}</p>);
        }
        case "job-workers": {
            return (<p>{digest["job-workers"].length} {"worker" + (digest["job-workers"].length != 1 ? "s" : "")}</p>);
        }
    }
}
