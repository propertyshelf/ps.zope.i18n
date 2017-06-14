# -*- coding: utf-8 -*-
"""Plural support for zope.i18n."""

# python imports
import logging


logger = logging.getLogger('ps.zope.i18n monkey patching: patched')


def load_patches():
    """Load patches."""
    from ps.zope.i18n import zope_i18n
    assert(zope_i18n)  # pyflakes
    logger.info('zope.i18n')
