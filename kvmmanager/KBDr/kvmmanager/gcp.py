import sys, os, asyncio
from typing import Any
from functools import partial
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from google.api_core.exceptions import NotFound
from google.auth import default
from KBDr.kworker import run_async

def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 600
) -> Any:
    result = operation.result(timeout=timeout)
    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


STOPPED_MACHINE_STATUS = (
    compute_v1.Instance.Status.TERMINATED.name,
    compute_v1.Instance.Status.STOPPED.name,
)

async def delete_image_in_gce(image_name: str):
    cred, project_id = default()
    image_client = compute_v1.ImagesClient()
    try:
        existing_image = await run_async(image_client.get, project=project_id, image=image_name)
        await run_async(wait_for_extended_operation,
            image_client.delete(project=project_id, image=image_name),
            verbose_name='image deletion')
    except NotFound:
        pass

async def create_image_from_gcs(
    source_disk_gcs_url: str,
    image_name: str,
    storage_location: str | None = None
) -> compute_v1.Image:
    cred, project_id = default()
    image_client = compute_v1.ImagesClient()
    try:
        existing_image = await run_async(image_client.get, project=project_id, image=image_name)
        await run_async(wait_for_extended_operation,
            image_client.delete(project=project_id, image=image_name),
            verbose_name='image deletion'
        )
    except NotFound:
        pass

    image = compute_v1.Image()
    image.raw_disk.source = source_disk_gcs_url
    image.name = image_name
    if storage_location:
        image.storage_locations = [storage_location]

    operation = image_client.insert(project=project_id, image_resource=image)

    await run_async(wait_for_extended_operation,
        operation,
        verbose_name='image creation from GCS'
    )

    return image_client.get(project=project_id, image=image_name)
