import datetime
import logging
import os
from typing import Set

import c2cwsgiutils.db
import c2cwsgiutils.health_check
import yaml
from pyramid.config import Configurator

_LOG = logging.getLogger(__name__)


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    del global_config  # Unused.
    with Configurator(settings=settings) as config:
        config.include("pyramid_mako")
        config.include(".routes")
        config.include("c2cwsgiutils.pyramid")
        config.scan()
        # Initialize the health checks
        c2cwsgiutils.health_check.HealthCheck(config)

        return config.make_wsgi_app()

