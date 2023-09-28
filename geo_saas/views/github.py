import logging
from typing import Any

import pyramid.request
from nox import param
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.view import view_config

_LOG = logging.getLogger(__name__)


@view_config(route_name="home", renderer="geo_saas:templates/home.mako")
def home(request: pyramid.request.Request) -> dict[str, Any]:
    del request  # Unused.

    return {}


@view_config(route_name="identity", renderer="json")
def identity(request: pyramid.request.Request) -> dict[str, Any]:
    params = "\n".join([": ".join(p) for p in request.params.items()])
    _LOG.error(
        f"""identity:

method: {request.method}
content_type: {request.headers.get("Content-Type")}

params:
{params}

body:
{request.body}
"""
    )

    return {}


def webhook(request: pyramid.request.Request) -> dict[str, Any]:
    params = "\n".join([": ".join(p) for p in request.params.items()])
    _LOG.error(
        f"""webhook:

method: {request.method}
content_type: {request.headers.get("Content-Type")}

params:
{params}

body:
{request.body}
"""
    )

    return {}
