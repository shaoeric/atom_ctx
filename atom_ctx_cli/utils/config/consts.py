# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Configuration constants for AtomCtx."""

from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".ctx"
SYSTEM_CONFIG_DIR = Path("/etc/ctx")

CTX_CONFIG_ENV = "CTX_CONFIG_FILE"
CTX_CLI_CONFIG_ENV = "CTX_CLI_CONFIG_FILE"

DEFAULT_CTX_CONF = "ctx.conf"
DEFAULT_CTX_CLI_CONF = "ctx-cli.conf"
