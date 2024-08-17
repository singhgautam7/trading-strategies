import pandas as pd
from rich.console import Console
from rich.table import Table
import logging
from strategies.stochastic.historic_data import fetch_banknifty_futures_history, fetch_banknifty_options_history
from strategies.stochastic.stochastic import apply_stochastic_strategy, select_option, get_next_expiry

log = logging.getLogger(__name__)
console = Console()

def test_stochastic_strategy():
    # Fetch historical data
    futures_data = fetch_banknifty_futures_history()

    if futures_data is None:
        log.error("Failed to fetch futures historical data")
        return

    # Apply stochastic strategy to futures data
    futures_result, _ = apply_stochastic_strategy(futures_data, futures_data)  # Temporary placeholder for options data

    # Filter for potential signals
    potential_signals = futures_result[(futures_result['last_5_above_vwap'] | futures_result['last_5_below_vwap'])].copy()

    if potential_signals.empty:
        console.print("[yellow]No potential signals generated in the given period.[/yellow]")
        return

    breakpoint()

    # Process each potential signal
    final_signals = []
    for timestamp, row in potential_signals.iterrows():
        option_type = 'call' if row['last_5_above_vwap'] else 'put'
        strike_price = select_option(row['close'], option_type)

        # Fetch options data for the selected strike price
        expiry_date = get_next_expiry(timestamp.date())
        options_data = fetch_banknifty_options_history(strike_price, option_type, expiry_date)

        if options_data is None:
            log.warning(f"Failed to fetch options data for {strike_price} {option_type} expiring on {expiry_date}")
            continue

        # Apply stochastic strategy to options data
        _, options_result = apply_stochastic_strategy(futures_data, options_data)

        # Check for stochastic crossover in options data
        if options_result.loc[timestamp, 'stoch_crossover']:
            final_signals.append({
                'Timestamp': timestamp,
                'Futures Price': row['close'],
                'VWAP': row['VWAP'],
                'Option Type': option_type.capitalize(),
                'Strike Price': strike_price,
                'Option Open': options_data.loc[timestamp, 'open'],
                'Option High': options_data.loc[timestamp, 'high'],
                'Option Low': options_data.loc[timestamp, 'low'],
                'Option Close': options_data.loc[timestamp, 'close'],
                '%K': options_result.loc[timestamp, '%K'],
                '%D': options_result.loc[timestamp, '%D']
            })

    if not final_signals:
        console.print("[yellow]No final signals generated after analyzing options data.[/yellow]")
        return

    # Create a rich table to display the results
    table = Table(title="Stochastic Strategy Signals")
    columns = ['Timestamp', 'Futures Price', 'VWAP', 'Option Type', 'Strike Price',
               'Option Open', 'Option High', 'Option Low', 'Option Close', '%K', '%D']
    for col in columns:
        table.add_column(col, style="cyan")

    for signal in final_signals:
        table.add_row(
            str(signal['Timestamp']),
            f"{signal['Futures Price']:.2f}",
            f"{signal['VWAP']:.2f}",
            signal['Option Type'],
            f"{signal['Strike Price']:.2f}",
            f"{signal['Option Open']:.2f}",
            f"{signal['Option High']:.2f}",
            f"{signal['Option Low']:.2f}",
            f"{signal['Option Close']:.2f}",
            f"{signal['%K']:.2f}",
            f"{signal['%D']:.2f}"
        )

    console.print(table)

    # Log summary statistics
    log.info(f"Total periods analyzed: {len(futures_result)}")
    log.info(f"Total potential signals: {len(potential_signals)}")
    log.info(f"Total final signals: {len(final_signals)}")

def run_test():
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    console.print("[bold green]Starting Stochastic Strategy Test[/bold green]")
    test_stochastic_strategy()
    console.print("[bold green]Stochastic Strategy Test Completed[/bold green]")

if __name__ == "__main__":
    pass