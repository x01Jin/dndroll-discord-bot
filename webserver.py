"""Tiny Flask keep-alive server for Render Web Services.

Render requires the process to bind $PORT or the deploy is marked failed
and the health check never passes. This module runs Flask in a daemon
thread so the Discord bot can remain the main process — the classic
Replit/Render "trick". Always-on (no env flag) per user choice.
"""

from __future__ import annotations

import logging
import os
from threading import Thread

from flask import Flask, jsonify

logger = logging.getLogger(__name__)

app = Flask("")


@app.route("/")
def home() -> str:
    return "dnd is ok"


@app.route("/health")
def health():  # type: ignore[no-untyped-def]
    return jsonify(status="ok"), 200


def run() -> None:
    port = int(os.getenv("PORT", "8080"))
    # threaded=True so /health can be polled while bot runs
    logger.info("Starting keep-alive webserver on 0.0.0.0:%d", port)
    # use_reloader=False is critical inside a thread
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)


def keep_alive() -> Thread:
    t = Thread(target=run, daemon=True, name="keep_alive")
    t.start()
    logger.info("Keep-alive thread started (daemon=%s)", t.daemon)
    return t
