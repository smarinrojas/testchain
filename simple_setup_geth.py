import os
import json
import subprocess
import questionary
import shutil
import sys
from decimal import Decimal, InvalidOperation
from eth_utils import to_checksum_address

DATA_DIR = "data"
GENESIS_FILE = "genesis.json"
PASSWORD_FILE = "password.txt"
LOG_FILE = os.path.join(DATA_DIR, "geth.log") # We assume the log file will be inside the data directory.

def eth_to_wei(eth_str: str) -> str | None:
    """
    Safely converts an ETH amount (as a string) to Wei using Decimal to avoid precision issues.
    Returns None if the input is not a valid number.
    """
    try:
        # Use Decimal instead of float to handle monetary values and avoid precision errors.
        eth_decimal = Decimal(eth_str)
        wei_decimal = eth_decimal * Decimal("1e18")
        # Format the Decimal as a plain, non-scientific string. The '.0f' specifier
        # ensures a fixed-point representation with zero decimal places, which is
        # the most reliable way to prevent scientific notation for Geth.
        return f'{wei_decimal:.0f}'
    except InvalidOperation:
        print(f"Error: '{eth_str}' is not a valid ETH amount.")
        return None

def ask_alloc() -> dict:
    """Prompts the user for addresses and their initial balances."""
    alloc = {}
    print("Enter the accounts for the genesis.json file. Leave the address blank to finish.")
    while True:
        address = questionary.text("Ethereum Address:").ask()
        if not address:
            break
        
        try:
            # Validate and normalize the address to checksum format.
            # to_checksum_address will raise a ValueError if the address is invalid.
            checksum_address = to_checksum_address(address)
        except ValueError:
            print("Error: Invalid Ethereum address. It must start with 0x and be 42 characters long.")
            continue

        balance_eth_str = questionary.text(f"Initial balance in ETH for {checksum_address}:").ask()
        balance_wei = eth_to_wei(balance_eth_str)
        
        if balance_wei is not None:
            alloc[checksum_address] = {"balance": balance_wei}
            
    return alloc

def write_genesis(alloc: dict):
    """Writes the allocation dictionary to the genesis.json file."""
    genesis = {
        "config": {
            "chainId": 1337,
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "berlinBlock": 0,
            "londonBlock": 0,
            "terminalTotalDifficulty": 0
        },
        "difficulty": "1",
        "gasLimit": "8000000",
        "alloc": alloc
    }
    try:
        with open(GENESIS_FILE, "w") as f:
            json.dump(genesis, f, indent=4)
        print(f"File '{GENESIS_FILE}' created successfully.")
    except IOError as e:
        print(f"Error writing to '{GENESIS_FILE}': {e}")

def write_password():
    """Prompts for and saves a password to a text file."""
    # Important security warning.
    print("\n WARNING: The password will be saved in plain text in 'password.txt'.")
    print("Use this for local development only and never with real accounts.\n")
    
    pw = questionary.password("Enter the password for the new account:").ask()
    try:
        with open(PASSWORD_FILE, "w") as f:
            f.write(pw)
        print(f"File '{PASSWORD_FILE}' created successfully.")
    except IOError as e:
        print(f"Error writing to '{PASSWORD_FILE}': {e}")

def delete_data():
    """Deletes the data directory for a clean reset."""
    if os.path.exists(DATA_DIR):
        confirm = questionary.confirm(f"Are you sure you want to delete the '{DATA_DIR}' directory and reset everything?").ask()
        if confirm:
            try:
                # Using shutil.rmtree is safer and cross-platform compared to 'rm -rf'.
                shutil.rmtree(DATA_DIR)
                print(f"Directory '{DATA_DIR}' deleted.")
            except OSError as e:
                print(f"Error deleting directory '{DATA_DIR}': {e}")
    else:
        print(f"Directory '{DATA_DIR}' does not exist, nothing to delete.")

def start_node():
    """Runs the script to start the Geth node."""
    print("Attempting to start the Geth node...")
    # Using subprocess.run is more modern and flexible.
    # Note: 'bash' assumes a Unix-like environment (Linux, macOS, WSL on Windows).
    subprocess.run(["bash", "./start-node.sh"])

def restart_node():
    """Stops any running Geth process and restarts it."""
    print("Attempting to restart the node...")
    try:
        # pkill is effective but specific to Unix/Linux/macOS.
        # A platform check could be added here if needed.
        subprocess.run(["pkill", "geth"], check=True, capture_output=True)
        print(" Geth process stopped.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("No running Geth process was found.")
    
    start_node()

def view_logs(num_lines: int = 20):
    """
    Displays the last N lines of the Geth log file.
    """
    print(f"Displaying the last {num_lines} lines of '{LOG_FILE}'...")
    try:
        with open(LOG_FILE, 'r') as f:
            # Read all lines from the file.
            lines = f.readlines()
            # Join and print only the last N lines.
            last_lines = "".join(lines[-num_lines:])
            print("-" * 50)
            print(last_lines.strip())
            print("-" * 50)
    except FileNotFoundError:
        print(f"Log file '{LOG_FILE}' not found.")
        print("Please ensure Geth is running and your 'start-node.sh' script is configured to write to that file.")
        print("Example: geth --datadir ./data --log.file ./data/geth.log ...")
    except Exception as e:
        print(f"An unexpected error occurred while reading the log file: {e}")


def main_menu():
    """Displays the main menu and handles user selection."""
    while True:
        choice = questionary.select(
            "Main Menu:",
            choices=[
                "Generate genesis.json and password.txt",
                "Start Node",
                "Restart Node",
                "View Latest Logs",
                "Delete Data and Reset",
                "Exit"
            ]
        ).ask()

        if choice is None:
            print("\nExiting...")
            break
        elif choice == "Generate genesis.json and password.txt":
            alloc = ask_alloc()
            if alloc:
                write_genesis(alloc)
                write_password()
            else:
                print("No accounts were entered. No files were generated.")
        elif choice == "Start Node":
            start_node()
        elif choice == "Restart Node":
            restart_node()
        elif choice == "View Latest Logs":
            view_logs()
        elif choice == "Delete Data and Reset":
            delete_data()
        elif choice == "Exit":
            print("👋 Exiting...")
            sys.exit(0)

if __name__ == "__main__":
    main_menu()