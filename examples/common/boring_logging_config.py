"""
Centralized logging configuration
Set CTX_DEBUG=1 environment variable to enable debug logging
"""

import logging
import logging.config
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Check debug mode from environment
DEBUG = os.environ.get("CTX_DEBUG") == "1"

if DEBUG:
    # Debug mode - show all logs
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
else:
    # Production mode - aggressively suppress all logs
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {"null": {"format": ""}},
            "handlers": {
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "root": {"level": "CRITICAL", "handlers": ["null"]},
            "loggers": {
                # Suppress all AtomCtx loggers
                "atom_ctx": {"level": "CRITICAL", "handlers": ["null"], "propagate": False},
                "atom_ctx.agfs_manager": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.viking_vector_index_backend": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.queuefs": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.queuefs.queue_manager": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.vikingdb_manager": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.ctx_fs": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.session.session": {
                    "level": "ERROR",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.session.memory_extractor": {
                    "level": "ERROR",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.session.compressor": {
                    "level": "ERROR",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.async_client": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.parse": {"level": "CRITICAL", "handlers": ["null"], "propagate": False},
                "atom_ctx.parse.parsers": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.parse.parsers.markdown": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.storage.queuefs.semantic_processor": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "apscheduler": {"level": "CRITICAL", "handlers": ["null"], "propagate": False},
                "atom_ctx.parse.tree_builder": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
                "atom_ctx.service.core": {
                    "level": "CRITICAL",
                    "handlers": ["null"],
                    "propagate": False,
                },
            },
        }
    )

    # Additional enforcement: set all loggers after config
    for logger_name in ["atom_ctx", "apscheduler"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
