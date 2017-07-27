#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Document class and its helper functions.

{} module also provides a deafult root-document object.
""".format(__name__)

import os
import tempfile
import shutil
from functools import partial
from types import ModuleType
from typing import Optional, Union, Callable, Any
import weakref

from wdom.element import Element, Attr
from wdom.event import Event
from wdom.node import Node, DocumentType, Text, RawHtml, Comment
from wdom.node import DocumentFragment
from wdom.options import config
from wdom.tag import Tag
from wdom.tag import Html, Head, Body, Meta, Link, Title, Script
from wdom.web_node import WdomElement
from wdom.window import Window


def getElementById(id: Union[str, int]) -> Optional[Node]:
    """Get element with ``id``."""
    elm = Element._elements_with_id.get(str(id))
    return elm


def getElementByRimoId(id: Union[str, int]) -> Optional[WdomElement]:
    """Get element with ``rimo_id``."""
    elm = WdomElement._elements_with_rimo_id.get(str(id))
    return elm


def _cleanup(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)


def create_element(tag: str, name: str = None, base: type = None,
                   attr: dict = None) -> Node:
    """Create element with a tag of ``name``.

    :arg str name: html tag.
    :arg type base: Base class of the created element
                       (defatlt: ``WdomElement``)
    :arg dict attr: Attributes (key-value pairs dict) of the new element.
    """
    from wdom.web_node import WdomElement
    from wdom.tag import Tag
    from wdom.window import customElements
    if attr is None:
        attr = {}
    if name:
        base_class = customElements.get((name, tag))
    else:
        base_class = customElements.get((tag, None))
    if base_class is None:
        attr['_registered'] = False
        base_class = base or WdomElement
    if issubclass(base_class, Tag):
        return base_class(**attr)
    return base_class(tag, **attr)


class Document(Node):
    """Document class."""

    nodeType = Node.DOCUMENT_NODE
    nodeName = '#document'
    body = None  # type: Node
    html = None  # type: Node

    @property
    def defaultView(self) -> Window:
        """Return :class:`Window` class of this document."""
        return self._window

    @property
    def tempdir(self) -> str:
        """Return temporary directory used by this document."""
        return self._tempdir

    def __init__(self, doctype: str = 'html', title: str = 'W-DOM',
                 charset: str = 'utf-8', default_class: type = WdomElement,
                 autoreload: Optional[bool] = None,
                 reload_wait: Optional[float] =None,
                 ) -> None:
        """Create new document object.

        .. caution::
            Don't create new document from :class:`Document` class constructor.
            Use :func:`get_new_document` function instead.

        :arg str doctype: doctype of the document (default: html).
        :arg str title: title of the document.
        :arg str charset: charset of the document.
        :arg type default_class: Set default Node class of the document. This
            class is used when make node by ``createElement`` method.
        :arg bool autoreload: Enable/Disable autoreload (default: False).
        :arg float reload_wait: How long (seconds) wait to reload. This
            parameter is only used when ``autoreload`` is enabled.
        """
        self._tempdir = _tempdir = tempfile.mkdtemp()
        self._finalizer = weakref.finalize(self,  # type: ignore
                                           partial(_cleanup, _tempdir))
        super().__init__()
        self._window = Window(self)
        self._default_class = default_class
        self._autoreload = autoreload
        self._reload_wait = reload_wait

        self.doctype = DocumentType(doctype, parent=self)
        self.html = Html(parent=self)
        self.head = Head(parent=self.html)
        self.charset_element = Meta(parent=self.head)
        self.characterSet = charset
        self.title_element = Title(parent=self.head)
        self.title = title

        self.body = Body(parent=self.html)
        self.script = Script(parent=self.body)
        self._autoreload_script = Script(parent=self.head)

    def _set_autoreload(self) -> None:
        self._autoreload_script.textContent = ''
        if self._autoreload is None:
            autoreload = (config.autoreload or config.debug)
        else:
            autoreload = self._autoreload

        if autoreload:
            ar_script = []
            ar_script.append('var RIMO_AUTORELOAD = true')
            if self._reload_wait is not None:
                ar_script.append('var RIMO_RELOAD_WAIT = {}'.format(
                    self._reload_wait))
            self._autoreload_script.textContent = '\n{}\n'.format(
                '\n'.join(ar_script))

    def getElementById(self, id: Union[str, int]) -> Optional[Node]:
        """Get element by ``id``.

        If this document does not have the element with the id, return None.
        """
        elm = getElementById(id)
        if elm and elm.ownerDocument is self:
            return elm
        return None

    def getElementByRimoId(self, id: Union[str, int]) -> Optional[WdomElement]:
        """Get element by ``rimo_id``.

        If this document does not have the element with the id, return None.
        """
        elm = getElementByRimoId(id)
        if elm and elm.ownerDocument is self:
            return elm
        return None

    def createElement(self, tag: str) -> Node:
        """Create new element."""
        return create_element(tag, base=self._default_class)

    def createDocumentFragment(self) -> DocumentFragment:
        """Create empty document fragment."""
        return DocumentFragment()

    def createTextNode(self, text: str) -> Text:
        """Create text node with ``text``."""
        return Text(text)

    def createComment(self, comment: str) -> Comment:
        """Create comment node with ``comment``."""
        return Comment(comment)

    def createEvent(self, event: str) -> Event:
        """Create Event object with ``event`` type."""
        return Event(event)

    def createAttribute(self, name: str) -> Attr:
        """Create Attribute object with ``name``."""
        return Attr(name)

    @property
    def title(self) -> str:
        """Return title of this document."""
        return self.title_element.textContent

    @title.setter
    def title(self, value: str) -> None:
        """Set title of this document."""
        self.title_element.textContent = value

    @property
    def characterSet(self) -> str:
        """Return character set of this document."""
        return self.charset_element.getAttribute('charset')

    @characterSet.setter
    def characterSet(self, value: str) -> None:
        """Set character set of this document."""
        self.charset_element.setAttribute('charset', value)

    @property
    def charset(self) -> str:
        """Return charset set of this document."""
        return self.characterSet

    @charset.setter
    def charset(self, value: str) -> None:
        """Set charset set of this document."""
        self.characterSet = value

    def add_jsfile(self, src: str) -> None:
        """Add JS file to load at this document's bottom."""
        self.body.appendChild(Script(src=src))

    def add_jsfile_head(self, src: str) -> None:
        """Add JS file to load at this document's header."""
        self.head.appendChild(Script(src=src))

    def add_cssfile(self, src: str) -> None:
        """Add CSS file to load at this document's bottom."""
        self.head.appendChild(Link(rel='stylesheet', href=src))

    def add_header(self, header: str) -> None:
        """Add CSS file to load at this document's header."""
        self.head.appendChild(RawHtml(header))

    def register_theme(self, theme: ModuleType) -> None:
        """Set theme."""
        if not hasattr(theme, 'css_files'):
            raise ValueError('theme module must include `css_files`.')
        for css in getattr(theme, 'css_files', []):
            self.add_cssfile(css)
        for js in getattr(theme, 'js_files', []):
            self.add_jsfile(js)
        for header in getattr(theme, 'headers', []):
            self.add_header(header)
        for cls in getattr(theme, 'extended_classes', []):
            self.defaultView.customElements.define(cls)

    def build(self) -> str:
        """Return HTML representation of this document."""
        self._set_autoreload()
        return ''.join(child.html for child in self.childNodes)


def get_new_document(  # noqa: C901
        include_rimo: bool = True,
        include_skeleton: bool = False,
        include_normalizecss: bool = False,
        autoreload: Optional[bool] = None,
        reload_wait: Optional[float] = None,
        log_level: Optional[Union[int, str]] = None,
        log_prefix: Optional[str] = None,
        log_console: bool = False,
        ws_url: Optional[str] = None,
        message_wait: Optional[float] = None,
        document_factory: Callable[..., Document] = Document,
        **kwargs: Any) -> Document:
    """Create new :class:`Document` object with options.

    :arg bool include_rimo: Include rimo.js file. Usually should be True.
    :arg bool include_skeleton: Include skelton.css.
    :arg bool include_normalizecss: Include normalize.css.
    :arg bool autoreload: Enable autoreload flag. This flag overwrites
        ``--debug`` flag, which automatically enables autoreload.
    :arg float reload_wait: Seconds to wait until reload when autoreload is
        enabled.
    :arg str log_level: Log level string, chosen from DEBUG, INFO, WARN, ERROR.
        Integer values are also acceptable like ``logging.INFO``. By default
        use ``wdom.config.options.log_level``, which default is ``INFO``.
    :arg str log_prefix: Prefix of log outputs.
    :arg bool log_console: Flag to show wdom log on browser console.
    :arg str ws_url: URL string to the ws url.
        Default: ``ws://localhost:8888/rimo_ws``.
    :arg float message_wait: Duration (seconds) to send WS messages.
    :arg Callable document_factory: Factory function/class to create Document
        object.
    :rtype: Document
    """
    document = document_factory(
        autoreload=autoreload,
        reload_wait=reload_wait,
        **kwargs
    )

    if log_level is None:
        log_level = config.logging
    if message_wait is None:
        message_wait = config.message_wait

    log_script = []
    log_script.append('var RIMO_MESSAGE_WAIT = {}'.format(message_wait))
    if isinstance(log_level, str):
        log_script.append('var RIMO_LOG_LEVEL = \'{}\''.format(log_level))
    elif isinstance(log_level, int):
        log_script.append('var RIMO_LOG_LEVEL = {}'.format(log_level))
    if log_prefix:
        log_script.append('var RIMO_LOG_PREFIX = \'{}\''.format(log_prefix))
    if log_console:
        log_script.append('var RIMO_LOG_CONSOLE = true')
    if log_script:
        _s = Script(parent=document.head)
        _s.textContent = '\n{}\n'.format('\n'.join(log_script))

    if ws_url:
        _s = Script(parent=document.head)
        _s.textContent = '\nvar RIMO_WS_URL = \'{}\'\n'.format(ws_url)

    if include_rimo:
        document.add_jsfile_head('_static/js/rimo/rimo.js')

    return document


# get_document = get_new_document
def get_document(*args: Any, **kwargs: Any) -> Document:
    """Get current root document object.

    :rtype: Document
    """
    return rootDocument


def set_document(new_document: Document) -> None:
    """Set a new document as a current root document.

    :param Document new_document: New root document.
    """
    global rootDocument
    rootDocument = new_document


def set_app(app: Tag) -> None:
    """Set root ``Tag`` as applicaion to the current root document."""
    document = get_document()
    document.body.prepend(app)


rootDocument = get_new_document()
