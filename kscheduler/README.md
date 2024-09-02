# kscheduler

## Objectives

- Dispatch jobs
- Monitor job logs
- Manage jobs and their static resources

## Documentation

### Environment Variables

- `KBDR_SCHEDULER_DB_STR`: Database connection string
- `KBDR_SCHEDULER_RABBITMQ_CONN_URL`: Something like `amqp://username:password@host:port/<virtual_host>[?query-string]`
- `GCS_BUCKET_NAME`: Name of the KBDr storage bucket
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the credential

MQ timeout to be adjusted

### Storage Structure

```
- /
  |- userspace-images
  | |- syzbot-img.raw
  | |- syzbot-img.raw.id
  |- jobs
  | |- <job-id>
  | | |- <id>_<worker_name>
```

### Log Message Format

```json
{
    "job-id": "",
    "log-time": "UTC time in ISO-format",
    "worker": "",
    "worker-hostname": "",
    "log": ""
}
```

### System Log Format

```json
{
    "log-time": "UTC time in ISO-format",
    "worker": "",
    "worker-hostname": "",
    "log": ""
}
```

### Job Message Format

Job request:

```json
{
    "job-workers": [
        "worker1-name",
        "worker2-name",
        "worker3-name"
    ],
    "worker-arguments": [
        {}, {}, {}
    ],
    "kv": {
        "key": "value"
    }
}
```

Job context:

```json
{
    "job-id": "<8 digit hex number>",
    "created-time": "UTC time in ISO-format",
    "job-workers": [
        "worker1-name",
        "worker2-name",
        "worker3-name"
    ],
    "current-worker": 0,
    "current-worker-hostname": "",
    "status": "pending|in_progress|waiting|aborted|finished",
    "worker-results": [
        {}, {}, {}
    ],
    "worker-arguments": [
        {}, {}, {}
    ],
    "modified-time": "",
    "kv": {
        "key": "value"
    }
}
```

### Sync note

Use the RCU strategy and write to the database conditionally.
