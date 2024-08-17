import os
import logging
from dotenv import load_dotenv
from breeze_connect import BreezeConnect
import pytz
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler

load_dotenv()

log = logging.getLogger("breeze_api")
console = Console()

class BreezeAPI:
    def __init__(self):
        self.api_key = os.getenv('BREEZE_API_KEY')
        self.api_secret = os.getenv('BREEZE_API_SECRET')
        self.session_id = os.getenv('BREEZE_SESSION_ID')
        self.breeze = None

    def connect(self):
        try:
            self.breeze = BreezeConnect(api_key=self.api_key)
            self.breeze.generate_session(api_secret=self.api_secret, session_token=self.session_id)
            log.info("Connected to Breeze API")
        except Exception as e:
            log.error(f"Failed to connect to Breeze API: {e}")
            raise

    def _format_date(self, date):
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        # Convert to UTC
        utc_date = date.replace(tzinfo=pytz.UTC)

        # Format to the specific string format required by the API
        return utc_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def get_futures_data(self, stock_code, from_date, to_date, interval="5minute", expiry_date=None):
        if not self.breeze:
            log.error("Not connected to Breeze API. Call connect() first.")
            raise Exception("Not connected to Breeze API. Call connect() first.")

        try:
            # Convert dates to the required format
            from_date = self._format_date(from_date)
            to_date = self._format_date(to_date)
            expiry_date = self._format_date(expiry_date) if expiry_date else None

            log.info(f"Fetching futures data for {stock_code}")
            log.debug(f"Parameters: from_date={from_date}, to_date={to_date}, interval={interval}, expiry_date={expiry_date}")

            data = self.breeze.get_historical_data_v2(
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                stock_code=stock_code,
                exchange_code="NFO",
                product_type="futures",
                expiry_date=expiry_date,
                right="others",
                strike_price="0"
            )
            log.info(f"Successfully fetched futures data for {stock_code}")
            return data
        except Exception as e:
            log.error(f"Error fetching futures data: {e}")
            return None

    def get_option_data(self, stock_code, strike_price, option_type, from_date, to_date, interval="5minute", expiry_date=None):
        if not self.breeze:
            log.error("Not connected to Breeze API. Call connect() first.")
            raise Exception("Not connected to Breeze API. Call connect() first.")

        try:
            # Convert dates to the required format
            from_date = self._format_date(from_date)
            to_date = self._format_date(to_date)
            expiry_date = self._format_date(expiry_date) if expiry_date else None

            log.info(f"Fetching option data for {stock_code}")
            log.debug(f"Parameters: strike_price={strike_price}, option_type={option_type}, from_date={from_date}, to_date={to_date}, interval={interval}, expiry_date={expiry_date}")

            data = self.breeze.get_historical_data(
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                stock_code=stock_code,
                exchange_code="NFO",
                product_type="Options",
                strike_price=strike_price,
                right=option_type,
                expiry_date=expiry_date
            )
            log.info(f"Successfully fetched option data for {stock_code}")
            return data
        except Exception as e:
            log.error(f"Error fetching option data: {e}")
            return None