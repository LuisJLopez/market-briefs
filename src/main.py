import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import config
import scheduler

logger = config.logger


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for Cloud Run health checks."""

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):  # suppress default per-request stdout noise
        pass


def run_http_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info("Health check server listening on port %d", port)
    server.serve_forever()


def run_scheduler():
    sched = scheduler.Scheduler()
    logger.info("Registering scheduler jobs...")
    sched.us_jobs()
    sched.uk_jobs()
    sched.liquidity()
    sched.market_sentiment()
    sched.saturday_briefing()
    sched.sunday_briefing()
    sched.sunday_upcoming_earnings()
    sched.start()


if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    run_http_server()
