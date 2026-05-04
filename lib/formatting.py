"""Shared table / json / csv formatting for query script output."""

from __future__ import annotations

import json
from typing import Any, Iterable, Sequence


def format_rows(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    output: str = "table",
    max_col_width: int = 80,
) -> str:
    """Format rows in one of `table`, `json`, `csv`.

    Rows are assumed to be already string-coerced or coercible via str().
    """
    if not rows:
        return "No data found."

    if output == "json":
        return json.dumps(
            [dict(zip(headers, row)) for row in rows],
            indent=2,
            default=str,
        )

    if output == "csv":
        lines = [",".join(_csv_escape(h) for h in headers)]
        for row in rows:
            lines.append(",".join(_csv_escape(str(v)) for v in row))
        return "\n".join(lines)

    str_rows = [[str(v) for v in row] for row in rows]
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))
    col_widths = [min(w, max_col_width) for w in col_widths]

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "|" + "|".join(f" {h[:col_widths[i]]:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"

    out = [sep, header_line, sep]
    for row in str_rows:
        truncated = [v[:col_widths[i]] for i, v in enumerate(row)]
        out.append("|" + "|".join(f" {v:<{col_widths[i]}} " for i, v in enumerate(truncated)) + "|")
    out.append(sep)
    out.append(f"\nRows returned: {len(str_rows)}")
    return "\n".join(out)


def _csv_escape(val: str) -> str:
    if any(c in val for c in (",", '"', "\n")):
        return '"' + val.replace('"', '""') + '"'
    return val
