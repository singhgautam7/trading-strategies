import logging
from rich.logging import RichHandler
from rich.console import Console
from strategies.stochastic.historic_data import fetch_banknifty_futures_history, fetch_banknifty_options_history
from strategies.stochastic.stochastic import run_strategy

# Set up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

# Create a console object for rich output
console = Console()

def test_futures():
    console.print("[bold green]Starting Bank Nifty Futures Data Fetch[/bold green]")
    banknifty_futures_data = fetch_banknifty_futures_history()
    if banknifty_futures_data is not None:
        print(banknifty_futures_data)
        print("columns", banknifty_futures_data.columns.values.tolist())
        console.print("[bold green]Data fetched successfully. Ready for further processing.[/bold green]")
        # Process the data further or apply your strategy here
    else:
        console.print("[bold red]Failed to fetch data. Please check the logs for more information.[/bold red]")

def test_options():
    console.print("[bold green]Starting Bank Nifty Options Data Fetch[/bold green]")
    banknifty_options_data = fetch_banknifty_options_history(50100, "Call")
    if banknifty_options_data is not None:
        print(banknifty_options_data)
        print("columns", banknifty_options_data.columns.values.tolist())
        console.print("[bold green]Data fetched successfully. Ready for further processing.[/bold green]")
        # Process the data further or apply your strategy here
    else:
        console.print("[bold red]Failed to fetch data. Please check the logs for more information.[/bold red]")

if __name__ == "__main__":
    # test_futures()
    # test_options()
    run_strategy()