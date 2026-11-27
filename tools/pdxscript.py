"""Minimal Paradox script (Clausewitz/Jomini) parser used by the mod's test tools.

parse(text) -> list of Node. A Node is (key, op, value, line) where value is either
a str (scalar) or a list[Node] (block). Anonymous list items inside a block, such as
the entries of `prerequisites = { tech_a tech_b }`, become Nodes with key None.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, Optional, Union

_TOKEN = re.compile(
    r'''
    (?P<ws>[ \t\r\n]+) |
    (?P<comment>\#[^\n]*) |
    (?P<string>"(?:[^"\\\n]|\\.)*") |
    (?P<op>==|!=|<=|>=|\?=|=|<|>) |
    (?P<open>\{) |
    (?P<close>\}) |
    (?P<word>[^\s=<>!?{}"\#]+)
    ''',
    re.VERBOSE,
)


class ParseError(Exception):
    def __init__(self, msg: str, line: int):
        super().__init__(f'line {line}: {msg}')
        self.line = line


@dataclass
class Node:
    key: Optional[str]
    op: Optional[str]
    value: Union[str, list['Node']]
    line: int
    children: list['Node'] = field(default_factory=list, repr=False)

    @property
    def is_block(self) -> bool:
        return isinstance(self.value, list)

    def get(self, key: str) -> Optional['Node']:
        if self.is_block:
            for n in self.value:  # type: ignore[union-attr]
                if n.key == key:
                    return n
        return None

    def get_all(self, key: str) -> list['Node']:
        return [n for n in self.value if n.key == key] if self.is_block else []  # type: ignore[union-attr]

    def scalar(self, key: str) -> Optional[str]:
        n = self.get(key)
        return n.value if n is not None and not n.is_block else None  # type: ignore[return-value]

    def items(self) -> list[str]:
        """Anonymous scalar entries of a block, e.g. tech names in prerequisites."""
        if not self.is_block:
            return []
        return [n.value for n in self.value if n.key is None and not n.is_block]  # type: ignore[union-attr]

    def walk(self) -> Iterator['Node']:
        yield self
        if self.is_block:
            for n in self.value:  # type: ignore[union-attr]
                yield from n.walk()


def tokenize(text: str):
    line = 1
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            raise ParseError(f'unexpected character {text[pos]!r}', line)
        kind = m.lastgroup
        tok = m.group()
        if kind not in ('ws', 'comment'):
            yield kind, tok, line
        line += tok.count('\n')
        pos = m.end()


def unquote(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s


def parse(text: str) -> list[Node]:
    if text.startswith('﻿'):
        text = text[1:]
    toks = list(tokenize(text))
    i = 0

    def parse_block(depth: int, open_line: int) -> list[Node]:
        nonlocal i
        out: list[Node] = []
        while i < len(toks):
            kind, tok, line = toks[i]
            if kind == 'close':
                if depth == 0:
                    raise ParseError('unmatched "}"', line)
                i += 1
                return out
            if kind == 'open':
                i += 1
                out.append(Node(None, None, parse_block(depth + 1, line), line))
                continue
            if kind == 'op':
                raise ParseError(f'unexpected operator {tok!r}', line)
            # word or string: maybe key op value, maybe bare item
            if i + 1 < len(toks) and toks[i + 1][0] == 'op':
                key = unquote(tok)
                op = toks[i + 1][1]
                i += 2
                if i >= len(toks):
                    raise ParseError(f'missing value after {key} {op}', line)
                vkind, vtok, vline = toks[i]
                if vkind == 'open':
                    i += 1
                    out.append(Node(key, op, parse_block(depth + 1, vline), line))
                elif vkind in ('word', 'string'):
                    i += 1
                    # `key = rgb { 1 2 3 }` / `hsv { }` style typed values
                    if i < len(toks) and toks[i][0] == 'open' and vkind == 'word' and vtok in ('rgb', 'hsv', 'hsv360', 'LIST'):
                        i += 1
                        out.append(Node(key, op, parse_block(depth + 1, toks[i - 1][2]), line))
                    else:
                        out.append(Node(key, op, unquote(vtok), line))
                else:
                    raise ParseError(f'bad value {vtok!r} after {key} {op}', vline)
            else:
                i += 1
                out.append(Node(None, None, unquote(tok), line))
        if depth != 0:
            raise ParseError('unclosed "{" opened here', open_line)
        return out

    return parse_block(0, 1)


def parse_file(path: str) -> list[Node]:
    with open(path, 'rb') as f:
        raw = f.read()
    return parse(raw.decode('utf-8', errors='replace'))
