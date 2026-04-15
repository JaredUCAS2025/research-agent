#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start the Research Agent web server with FastAPI + Uvicorn.
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if __name__ == "__main__":
    import uvicorn

    print("Research Agent Web Server (FastAPI)")
    print("Open http://127.0.0.1:5000 in your browser")
    print("API Docs: http://127.0.0.1:5000/api/docs")
    print("Press Ctrl+C to stop\n")

    uvicorn.run(
        "research_agent.web:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info"
    )
