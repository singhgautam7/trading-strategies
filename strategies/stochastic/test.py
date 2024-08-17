import pandas as pd
from rich.console import Console
from rich.table import Table
import logging
from strategies.stochastic.historic_data import fetch_banknifty_futures_history
from strategies.stochastic.stochastic import apply_stochastic_strategy, select_option

log = logging.getLogger(__name__)
console = Console()

def test_stochastic_strategy():
    # Fetch historical data
    futures_data = fetch_banknifty_futures_history()

    if futures_data is None:
        log.error("Failed to fetch historical data")
        return

    # Apply stochastic strategy
    result = apply_stochastic_strategy(futures_data)

    # Filter for buy signals
    signals = result[result['buy_signal']].copy()

    if signals.empty:
        console.print("[yellow]No buy signals generated in the given period.[/yellow]")
        return

    # Select options for each signal
    signals['selected_option'] = signals['close'].apply(select_option)

    # Create a rich table to display the results
    table = Table(title="Stochastic Strategy Buy Signals")
    columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'VWAP', '%K', '%D', 'Selected Option']
    for col in columns:
        table.add_column(col, style="cyan")

    for _, row in signals.iterrows():
        table.add_row(
            str(row.name),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            f"{row['VWAP']:.2f}",
            f"{row['%K']:.2f}",
            f"{row['%D']:.2f}",
            f"{row['selected_option']:.2f}"
        )

    console.print(table)

    # Log summary statistics
    log.info(f"Total periods analyzed: {len(result)}")
    log.info(f"Total buy signals generated: {len(signals)}")

if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    console.print("[bold green]Starting Stochastic Strategy Test[/bold green]")
    test_stochastic_strategy()
    console.print("[bold green]Stochastic Strategy Test Completed[/bold green]")