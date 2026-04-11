"""Blueprint serving API documentation UI and OpenAPI spec."""

from __future__ import annotations

import os

from flask import Blueprint, Response, jsonify, render_template

from pdfforge_api.auth.api_key import require_api_key
from pdfforge_api.openapi.spec import build_openapi_spec

docs_bp = Blueprint(
    "docs_v1",
    __name__,
    url_prefix="/api/v1",
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
)


@docs_bp.get("/openapi.json")
def openapi_json():
    return jsonify(build_openapi_spec())


@docs_bp.get("/docs")
def swagger_ui():
    return render_template("swagger.html")


@docs_bp.get("/redoc")
def redoc_ui():
    return render_template("redoc.html")
