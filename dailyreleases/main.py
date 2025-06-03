"""Main entry point for the daily releases script"""

import logging
import time
from datetime import datetime, timedelta
import threading
import schedule

from .Config import CONFIG
from .Generator import Generator
from .util import setup_logging

logger = logging.getLogger(__name__)

class Main:
    def __init__(self):
        self.generator = Generator()
        setup_logging()

    def run_immediate_mode(self):
        """Run the script once immediately"""
        logger.info("Running in immediate mode")
        self.generator.generate(discord_post=True)
        return True

    def run_midnight_mode(self):
        """Run the script at midnight"""
        logger.info("Running in midnight mode")
        while True:
            now = datetime.now()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now > midnight:
                midnight = midnight + timedelta(days=1)
            seconds_until_midnight = (midnight - now).total_seconds()
            logger.info(f"Sleeping for {seconds_until_midnight} seconds until midnight")
            time.sleep(seconds_until_midnight)
            self.generator.generate(discord_post=True)

    def run_admin_mode(self):
        """Run the script in admin panel mode"""
        logger.info("Running in admin panel mode")
        from .admin import app, run_admin_panel
        import sys
        debug = '--debug' in sys.argv
        run_admin_panel(debug=debug)

    def run_test_mode(self):
        """Run the script in test mode"""
        logger.info("Running in test mode")
        self.generator.generate(discord_post=False)

    def run_main(self):
        """Main entry point"""
        mode = CONFIG.CONFIG['main']['mode'].lower()
        
        if mode == 'immediate':
            self.run_immediate_mode()
        elif mode == 'midnight':
            self.run_midnight_mode()
        elif mode in ['admin', 'admin panel']:
            self.run_admin_mode()
        elif mode == 'test':
            self.run_test_mode()
        else:
            logger.error(f"Unknown mode: {mode}")
            return False
        
        return True
