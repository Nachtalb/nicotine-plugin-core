"""This module provides functions to make HTTP requests

Example:

    .. code-block:: python

        from npc.requests import get, post, USER_AGENT_MAP

        response = get("https://httpbin.org/get")
        print(response.json)

        response = get("https://httpbin.org/get", headers={"User-Agent": USER_AGENT_MAP["windows-chrome-126"]})
        print(response.json)

        response = post("https://httpbin.org/post", data=b"Hello, World!")
        print(response.json)
"""

import json
from http.client import HTTPResponse
from random import choice
from typing import Any, Dict, Iterable, Optional, Union
from urllib.request import Request, urlopen

from .types import Readable

__all__ = ["Response", "get", "post", "USER_AGENTS", "USER_AGENT_MAP"]

USER_AGENT_MAP = {
    "windows-chrome-126": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3",
    "windows-firefox-127": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "windows-edge-126": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0",
    "mac-chrome-125": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3",
    "mac-safari-17": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "mac-firefox-127": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:127.0) Gecko/20100101 Firefox/127.0",
    "linux-chrome-126": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "linux-firefox-126": "Mozilla/5.0 (X11; Linux i686; rv:127.0) Gecko/20100101 Firefox/127.0",
    "osx-chrome-126": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.108 Mobile/15E148 Safari/604.1",
    "osx-safari-17": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "android-chrome-126": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.3",
    "android-firefox-127": "Mozilla/5.0 (Android 14; Mobile; rv:127.0) Gecko/127.0 Firefox/127.0",
}
"""Map of user agent strings to be used for making requests"""

USER_AGENTS = list(USER_AGENT_MAP.values())
"""List of user agents to be used for making requests"""


class Response:
    """Wrapper around HTTPResponse to provide additional functionality

    Args:
        obj: HTTPResponse object

    Attributes:
        mime_type (:obj:`str`): MIME type of the response
        encoding (:obj:`str`): Encoding of the response

    Properties:
        raw (:obj:`bytes`): Raw response content
        content (:obj:`str`): Response content decoded with :paramref:`encoding`
        json (:obj:`dict` | :obj:`list`): JSON response content
    """

    _raw: Optional[bytes] = None
    _content: Optional[str] = None
    _json: Any = None

    def __init__(self, obj: HTTPResponse) -> None:
        self._wrapped_obj = obj
        self.mime_type: str = self.headers.get_content_type()
        self.encoding: str = self.headers.get_content_charset()

    def __enter__(self) -> "Response":
        self._wrapped_obj.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        return self._wrapped_obj.__exit__(*args, **kwargs)

    def __getattr__(self, attr: str) -> Any:
        """Get attribute from the wrapped object if not found in the current object

        Args:
            attr (:obj:`str`): Attribute to get (e.g. status, headers, etc.

        Returns:
            :obj:`Any`: Value of the attribute
        """
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self._wrapped_obj, attr)

    def __repr__(self) -> str:
        return f'{self.__class__}(url="{self.geturl()}", status={self.status})'

    @property
    def raw(self) -> bytes:
        """Raw response content

        Returns:
            :obj:`bytes`: Raw response
        """
        if self._raw is None:
            self._raw = self.read()
        return self._raw

    @property
    def content(self) -> str:
        """Response content decoded with :paramref:`encoding`

        Returns:
            :obj:`str`: Decoded response content
        """
        if self._content is None:
            self._content = self.raw.decode(self.encoding or "utf-8")
        return self._content

    @property
    def json(self) -> Any:
        """JSON response content

        Returns:
            :obj:`dict` | :obj:`list`: JSON response content
        """
        if self._json is None:
            self._json = json.loads(self.content)
        return self._json


def get(url: str, headers: Dict[str, str] = {}, timeout: int = 30) -> Response:
    """Make a GET request to the given URL

    Args:
        url (:obj:`str`): URL to make the request to including the query parameters
        headers (:obj:`dict`, optional): Dict of headers to be sent with the request
        timeout (:obj:`int`, optional): Timeout for the request in seconds

    Returns:
        :obj:`Response`: Response object
    """
    if "User-Agent" not in headers:
        headers["User-Agent"] = choice(USER_AGENTS)

    response = urlopen(Request(url=url, headers=headers), timeout=timeout)
    return Response(response)


def post(
    url: str,
    data: Union[Readable[bytes], Iterable[bytes], bytes, None] = None,
    headers: dict[str, str] = {},
    timeout: int = 30,
) -> Response:
    """Make a POST request to the given URL

    Args:
        url (:obj:`str`): URL to make the request to including the query parameters
        data (:obj:`bytes` | :obj:`Iterable` | :obj:`Readable`, optional): Raw bytes data to be sent with the request
        headers (:obj:`dict`, optional): Dict of headers to be sent with the request
        timeout (:obj:`int`, optional): Timeout for the request in seconds

    Returns:
        :obj:`Response`: Response object
    """
    if "User-Agent" not in headers:
        headers["User-Agent"] = choice(USER_AGENTS)

    response = urlopen(Request(url=url, data=data, headers=headers, method="POST"), timeout=timeout)
    return Response(response)
