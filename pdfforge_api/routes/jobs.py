"""Blueprint for job retrieval / download / delete endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, send_file

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.utils.job_store import (
    delete_job,
    is_expired,
    output_file_path,
    read_manifest,
)
from pdfforge_api.utils.response import expired_job_error, job_not_found_error

jobs_bp = Blueprint("jobs_v1", __name__, url_prefix="/api/v1/jobs")


@jobs_bp.get("/<job_id>")
@require_api_key
def get_job(job_id: str):
    manifest = read_manifest(job_id)
    if manifest is None:
        return job_not_found_error(job_id)
    if is_expired(manifest):
        delete_job(job_id)
        return expired_job_error(job_id)
    return jsonify(manifest), 200


@jobs_bp.get("/<job_id>/download")
@require_api_key
def download_job(job_id: str):
    manifest = read_manifest(job_id)
    if manifest is None:
        return job_not_found_error(job_id)
    if is_expired(manifest):
        delete_job(job_id)
        return expired_job_error(job_id)

    path = output_file_path(job_id)
    if path is None:
        return job_not_found_error(job_id)

    return send_file(
        path,
        as_attachment=True,
        download_name=manifest.get("output_filename", path.name),
        mimetype=manifest.get("mimetype", "application/octet-stream"),
    )


@jobs_bp.delete("/<job_id>")
@require_api_key
def remove_job(job_id: str):
    existed = delete_job(job_id)
    if not existed:
        return job_not_found_error(job_id)
    return Response(status=204)
