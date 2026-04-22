#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start the Research Agent web server with FastAPI + Uvicorn.
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

if __name__ == "__main__":
    import uvicorn

    print("Research Agent Web Server (FastAPI, flush=True)", flush=True)
    print("Open http://127.0.0.1:5000 in your browser", flush=True)
    print("API Docs: http://127.0.0.1:5000/api/docs", flush=True)
    print("Press Ctrl+C to stop\n", flush=True)

    uvicorn.run(
        "research_agent.web:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info",
        access_log=True
    )
