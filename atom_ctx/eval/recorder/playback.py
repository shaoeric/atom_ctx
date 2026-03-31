# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""
Deprecated: Playback module for IORecorder.

This module has been moved to atom_ctx.eval.playback.
This file provides backward compatibility.
"""

import warnings


def get_record_stats(record_file: str) -> dict:
    """
    Deprecated: Get statistics from a record file without playback.

    Use atom_ctx.eval.record_analysis.analyze_records instead.
    """
    warnings.warn(
        "get_record_stats is deprecated. Use atom_ctx.eval.record_analysis.analyze_records instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from atom_ctx.eval.record_analysis import analyze_records

    stats = analyze_records(record_file)
    return stats.to_dict()
