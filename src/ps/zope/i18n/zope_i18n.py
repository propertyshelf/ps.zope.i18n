# -*- coding: utf-8 -*-
"""Patch adding plural support for zope.i18n."""

# zope imports
from zope.component import queryUtility
from zope.i18n import (
    interpolate,
    negotiate,
)
from zope.i18n.interfaces import (
    IFallbackTranslationDomainFactory,
    INegotiator,
    ITranslationDomain,
)
from zope.i18n.simpletranslationdomain import SimpleTranslationDomain
from zope.i18nmessageid import Message
import zope.i18n
import zope.i18n.gettextmessagecatalog
import zope.i18n.simpletranslationdomain
import zope.i18n.testmessagecatalog
import zope.i18n.translationdomain


# Patch: zope.i18n.__init__.py
def translate(
        msgid, domain=None, mapping=None, context=None, target_language=None,
        default=None, plural=None, n=None):
    """Translate text.

    First setup some test components:

    >>> from zope import component, interface
    >>> import zope.i18n.interfaces

    >>> class TestDomain:
    ...     interface.implements(zope.i18n.interfaces.ITranslationDomain)  # noqa
    ...
    ...     def __init__(self, **catalog):
    ...         self.catalog = catalog
    ...
    ...     def translate(self, text, *_, **__):
    ...         return self.catalog[text]

    Normally, the translation system will use a domain utility:

    >>> component.provideUtility(TestDomain(eek=u'ook'), name='my.domain')
    >>> translate(u'eek', 'my.domain')
    u'ook'

    Normally, if no domain is given, or if there is no domain utility
    for the given domain, then the text isn't translated:

    >>> translate(u'eek')
    u'eek'

    Moreover the text will be converted to unicode:

    >>> translate('eek', 'your.domain')
    u'eek'

    A fallback domain factory can be provided. This is normally used
    for testing:

    >>> def fallback(domain=u''):
    ...     return TestDomain(eek=u'test-from-' + domain)
    >>> interface.directlyProvides(  # noqa
    ...     fallback,
    ...     zope.i18n.interfaces.IFallbackTranslationDomainFactory,
    ...     )

    >>> component.provideUtility(fallback)

    >>> translate(u'eek')
    u'test-from-'

    >>> translate(u'eek', 'your.domain')
    u'test-from-your.domain'
    """
    if isinstance(msgid, Message):
        domain = msgid.domain
        default = msgid.default
        if mapping is None:
            mapping = msgid.mapping

    if default is None:
        default = unicode(msgid)

    if domain:
        util = queryUtility(ITranslationDomain, domain)
        if util is None:
            util = queryUtility(IFallbackTranslationDomainFactory)
            if util is not None:
                util = util(domain)
    else:
        util = queryUtility(IFallbackTranslationDomainFactory)
        if util is not None:
            util = util()

    if util is None:
        return interpolate(default, mapping)

    if target_language is None and context is not None:
        target_language = negotiate(context)

    return util.translate(
        msgid, mapping, context, target_language, default, plural, n,
    )


zope.i18n.translate = translate


# Patch: zope.i18n.gettextmessagecatalog.py
class _KeyErrorRaisingFallback(object):

    def gettext(self, msgid):
        raise KeyError(msgid)

    def ugettext(self, msgid):
        raise KeyError(msgid)

    def ngettext(self, singular, plural, n):
        raise KeyError(singular)

    def ungettext(self, singular, plural, n):
        raise KeyError(singular)


zope.i18n.gettextmessagecatalog._KeyErrorRaisingFallback = \
    _KeyErrorRaisingFallback


# Patch: zope.i18n.gettextmessagecatalog.py
def _gettext(self, msgid, default=None):
    try:
        return self._catalog.gettext(msgid)
    except KeyError:
        return default


def _ugettext(self, msgid, default=None):
    try:
        return self._catalog.ugettext(msgid)
    except KeyError:
        return default


def _ngettext(self, singular, plural, n, default=None):
    try:
        return self._catalog.ngettext(singular, plural, n)
    except KeyError:
        if n != 1:
            return plural
        return default


def _ungettext(self, singular, plural, n, default=None):
    try:
        return self._catalog.ungettext(singular, plural, n)
    except KeyError:
        if n != 1:
            return plural
        return default


def queryMessage(  # noqa
        self,
        msgid,
        default=None, plural=None, n=None, funcname=None):
    """See IMessageCatalog."""
    if isinstance(msgid, Message):
        if default is None:
            default = msgid.default
        if funcname is None:
            funcname = msgid.funcname
        if plural is None:
            plural = msgid.plural
        if n is None:
            n = msgid.n

    if funcname is None and n is not None:
        funcname = 'ungettext'
    elif funcname is None:
        funcname = 'ugettext'

    text = default
    if funcname == 'ugettext':
        text = self._ugettext(msgid, default)
    elif funcname == 'ungettext':
        text = self._ungettext(msgid, plural, n, default)
    elif funcname == 'gettext':
        text = self._gettext(msgid, default)
    elif funcname == 'ngettext':
        text = self._ngettext(msgid, plural, n, default)

    if text == msgid and default:
        text = default

    return text


zope.i18n.gettextmessagecatalog.GettextMessageCatalog._gettext = _gettext
zope.i18n.gettextmessagecatalog.GettextMessageCatalog._ugettext = _ugettext
zope.i18n.gettextmessagecatalog.GettextMessageCatalog._ngettext = _ngettext
zope.i18n.gettextmessagecatalog.GettextMessageCatalog._ungettext = _ungettext
zope.i18n.gettextmessagecatalog.GettextMessageCatalog.queryMessage = \
    queryMessage


# Patch: zope.i18n.simpletranslationdomain.py
zope.i18n.simpletranslationdomain.SimpleTranslationDomain.__translate_orig = \
    zope.i18n.simpletranslationdomain.SimpleTranslationDomain.translate


def translate_std(
        self, msgid, mapping=None, context=None, target_language=None,
        default=None, plural=None, n=None):
    """See interface ITranslationDomain"""
    return self.__translate_orig(
        msgid, mapping, context, target_language, default,
    )


zope.i18n.simpletranslationdomain.SimpleTranslationDomain.translate = \
    translate_std


# Patch: zope.i18n.testmessagecatalog.py
zope.i18n.testmessagecatalog.TestMessageCatalog.__queryMessage_orig = \
    zope.i18n.testmessagecatalog.TestMessageCatalog.queryMessage


def queryMessage_tmc(
        self, msgid, default=None, plural=None, n=None, funcname=None):
    return self.__queryMessage_orig(msgid, default)


zope.i18n.testmessagecatalog.TestMessageCatalog.queryMessage = \
    queryMessage_tmc
zope.i18n.testmessagecatalog.TestMessageCatalog.getMessage = \
    queryMessage_tmc


# Patch: zope.i18n.translationdomain.py
class TranslationDomain(SimpleTranslationDomain):

    def __init__(self, domain, fallbacks=None):
        self.domain = domain
        # _catalogs maps (language, domain) to IMessageCatalog instances
        self._catalogs = {}
        # _data maps IMessageCatalog.getIdentifier() to IMessageCatalog
        self._data = {}
        # What languages to fallback to, if there is no catalog for the
        # requested language (no fallback on individual messages)
        if fallbacks is None:
            fallbacks = zope.i18n.translationdomain.LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    def _registerMessageCatalog(self, language, catalog_name):
        key = language
        mc = self._catalogs.setdefault(key, [])
        mc.append(catalog_name)

    def addCatalog(self, catalog):
        self._data[catalog.getIdentifier()] = catalog
        self._registerMessageCatalog(catalog.language,
                                     catalog.getIdentifier())

    def setLanguageFallbacks(self, fallbacks=None):
        if fallbacks is None:
            fallbacks = zope.i18n.translationdomain.LANGUAGE_FALLBACKS
        self._fallbacks = fallbacks

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None, plural=None, n=None):
        """See zope.i18n.interfaces.ITranslationDomain"""
        # if the msgid is empty, let's save a lot of calculations and return
        # an empty string.
        if msgid == u'':
            return u''

        if target_language is None and context is not None:
            langs = self._catalogs.keys()
            # invoke local or global unnamed 'INegotiator' utilities
            negotiator = zope.component.getUtility(INegotiator)
            # try to determine target language from negotiator utility
            target_language = negotiator.getLanguage(langs, context)

        return self._recursive_translate(msgid, mapping, target_language,
                                         default, context, plural, n)

    def _recursive_translate(  # noqa
            self,
            msgid,
            mapping,
            target_language,
            default,
            context,
            plural=None, n=None, seen=None):
        """Recursively translate msg."""
        # MessageID attributes override arguments
        if isinstance(msgid, Message):
            if msgid.domain != self.domain:
                return translate(msgid, msgid.domain, mapping, context,
                                 target_language, default, plural, n)
            default = msgid.default
            if mapping is None:
                mapping = msgid.mapping

        # Recursively translate mappings, if they are translatable
        mapping_values = None
        if mapping is not None:
            mapping_values = (type(m) for m in mapping.values())
        if (mapping is not None and Message in mapping_values):
            if seen is None:
                seen = set()
            seen.add(msgid)
            mapping = mapping.copy()
            for key, value in mapping.items():
                if isinstance(value, Message):
                    if value in seen:
                        raise ValueError(
                            'Circular reference in mappings detected: '
                            '{0}'.format(value)
                        )
                    mapping[key] = self._recursive_translate(
                        value, value.mapping, target_language,
                        value.default, context, value.plural, n, seen)

        if default is None:
            default = unicode(msgid)

        # Get the translation. Use the specified fallbacks if this fails
        catalog_names = self._catalogs.get(target_language)
        if catalog_names is None:
            for language in self._fallbacks:
                catalog_names = self._catalogs.get(language)
                if catalog_names is not None:
                    break

        text = default
        if catalog_names:
            if len(catalog_names) == 1:
                # this is a slight optimization for the case when there is a
                # single catalog. More importantly, it is extremely helpful
                # when testing and the test language is used, because it
                # allows the test language to get the default.
                text = self._data[catalog_names[0]].queryMessage(
                    msgid, default, None, n)
            else:
                for name in catalog_names:
                    catalog = self._data[name]
                    s = catalog.queryMessage(msgid)
                    if s is not None:
                        text = s
                        break

        # Now we need to do the interpolation
        if text and mapping:
            text = interpolate(text, mapping)
        return text

    def getCatalogsInfo(self):
        return self._catalogs

    def reloadCatalogs(self, catalogNames):
        for catalogName in catalogNames:
            self._data[catalogName].reload()


zope.i18n.translationdomain.TranslationDomain = TranslationDomain
