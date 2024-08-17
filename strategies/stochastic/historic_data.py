from api.breeze.breeze import BreezeAPI
import pandas as pd
from datetime import datetime, timedelta
from api.breeze import stock_codes
import logging
from rich.logging import RichHandler
from rich.console import Console

log = logging.getLogger(__name__)
console = Console()

def fetch_banknifty_futures_history():
    breeze = BreezeAPI()
    breeze.connect()

    # Set the dates
    to_date = datetime.today()
    from_date = (to_date - timedelta(days=5))
    expiry_date = datetime.strptime("2024-08-28", "%Y-%m-%d")

    data = breeze.get_futures_data(
        stock_code=stock_codes.BANK_NIFTY,
        from_date=from_date,
        to_date=to_date,
        interval="5minute",
        expiry_date=expiry_date
    )

    if data:
        df = pd.DataFrame(data['Success'])
        print("count", df.shape[0])
        print(df.head())
        return df
    else:
        log.exception(f"An error occurred while fetching Bank Nifty futures data")
        return None
