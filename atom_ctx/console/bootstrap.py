# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Bootstrap entrypoint for AtomCtx console service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

if __package__ in {None, ""}:
    # Allow running as a script from a source checkout:
    # python atom_ctx/console/bootstrap.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from atom_ctx.console.app import create_console_app
from atom_ctx.console.config import load_console_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AtomCtx Console",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8020, help="Port to bind to")
    parser.add_argument(
        "--atom_ctx-url",
        type=str,
        default="http://127.0.0.1:1933",
        help="Base URL for AtomCtx HTTP service",
    )
    parser.add_argument(
        "--write-enabled",
        action="store_true",
        help="Enable write operations in console proxy",
    )
    parser.add_argument(
        "--request-timeout-sec",
        type=float,
        default=3600.0,
        help="Upstream request timeout in seconds",
    )
    parser.add_argument(
        "--cors-origins",
        type=str,
        default="*",
        help="Comma-separated CORS origins",
    )
    return parser


def main() -> None:
    """Run console service."""
    parser = _build_parser()
    args = parser.parse_args()

    config = load_console_config(
        host=args.host,
        port=args.port,
        atom_ctx_base_url=args.ctx_url,
        write_enabled=args.write_enabled,
        request_timeout_sec=args.request_timeout_sec,
        cors_origins=args.cors_origins,
    )

    app = create_console_app(config=config)
    print(f"AtomCtx Console is running on {config.host}:{config.port}")
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
