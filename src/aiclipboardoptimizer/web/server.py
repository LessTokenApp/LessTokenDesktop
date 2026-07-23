"""Flask web server runner."""
import os
from pathlib import Path
from . import create_app


def run_server(host: str = "localhost", port: int = 5000, debug: bool = False):
    """Run the Flask development server."""
    app = create_app()

    mode = 'Debug' if debug else 'Production'
    print(f"""
========================================
   Token Optimizer Web Server
========================================
Server: http://{host}:{port}
Mode: {mode}
========================================

API Endpoints:
  GET  /api/operations       - List available operations
  POST /api/process          - Process text
  GET  /api/stats            - Get usage statistics
  GET  /api/settings         - Get settings
  POST /api/settings         - Update settings
  GET  /api/cache-stats      - Get cache statistics
    """)

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
