
export type JobLogCtx = {
    "job-id": string,
    "log-time": string,
    "worker": string,
    "worker-hostname": string,
    "log": string
}

export type WorkerLogCtx = {
    "log-time": string,
    "worker": string,
    "worker-hostname": string,
    "log": string
}

export type KV = { [key: string]: string }

export type JobCtx = {
    "job-id": string,
    "created-time": string,
    "job-workers": Array<string>,
    "current-worker": number,
    "status": "pending" | "in_progress" | "aborted"| "finished",
    "worker-results": Array<object>,
    "worker-arguments": Array<object>,
    "modified-time": string,
    "kv": KV
}

export type JobDigest = {
    "job-id": string,
    "created-time": string,
    "job-workers": Array<string>
    "current-worker": number,
    "status": string,
    "modified-time": string
}
