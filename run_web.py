#!/usr/bin/env python
"""
Start the Research Agent web server.
"""

from research_agent.web import app

if __name__ == "__main__":
    print("🚀 Research Agent Web Server")
    print("📍 Open http://127.0.0.1:5000 in your browser")
    print("⏹️  Press Ctrl+C to stop\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
