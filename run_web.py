#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start the Research Agent web server.
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from research_agent.web import app

if __name__ == "__main__":
    print("🚀 Research Agent Web Server")
    print("📍 Open http://127.0.0.1:5000 in your browser")
    print("⏹️  Press Ctrl+C to stop\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
