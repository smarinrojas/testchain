import subprocess
import os
import time
import signal

# --- Configuration ---
ANVIL_STATE_FILE = "anvil_state.json"
# Listen on 0.0.0.0 to allow access from the internet/local network
ANVIL_HOST = "0.0.0.0" 
ANVIL_PORT = 8545
ANVIL_PID_FILE = "anvil.pid"

def start_anvil():
    """
    Starts an Anvil process accessible from the network.
    If a state file exists, it loads it.
    """
    if os.path.exists(ANVIL_PID_FILE):
        print("Anvil appears to be already running. Check the anvil.pid file.")
        return

    # The --host 0.0.0.0 argument makes Anvil accessible from outside localhost
    command = ["anvil", "--host", ANVIL_HOST, "--port", str(ANVIL_PORT)]

    if os.path.exists(ANVIL_STATE_FILE):
        print(f"State file '{ANVIL_STATE_FILE}' found. Loading previous state...")
        command.extend(["--load-state", ANVIL_STATE_FILE])
    else:
        print("No state file found. Starting a new blockchain.")

    try:
        # Start Anvil in a new process
        process = subprocess.Popen(command)
        
        # Save the process ID (PID) to be able to stop it later
        with open(ANVIL_PID_FILE, "w") as f:
            f.write(str(process.pid))
            
        print(f"\nAnvil started successfully. PID: {process.pid}")
        print(f"Listening on ALL interfaces (0.0.0.0) on port {ANVIL_PORT}")
        print("It is now accessible from your local network or the internet (if ports are open).")
        print("\nIMPORTANT SECURITY WARNING!")
        print("Exposing Anvil to the internet can be risky. Ensure your firewall")
        print(f"is configured to allow traffic on port {ANVIL_PORT} only from trusted IPs.")

    except FileNotFoundError:
        print("\nError: The 'anvil' command was not found.")
        print("Please make sure Foundry and Anvil are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn error occurred while starting Anvil: {e}")

def stop_anvil():
    """
    Stops the running Anvil process and saves its state.
    """
    if not os.path.exists(ANVIL_PID_FILE):
        print("Anvil does not appear to be running (anvil.pid not found).")
        return

    with open(ANVIL_PID_FILE, "r") as f:
        pid = int(f.read())

    try:
        # To dump the state, we connect to the instance locally.
        # Even though Anvil listens on 0.0.0.0, we can connect via localhost.
        rpc_url_local = f"http://127.0.0.1:{ANVIL_PORT}"
        
        command_dump = [
            "cast",
            "rpc",
            "anvil_dumpState",
            "--rpc-url",
            rpc_url_local
        ]
        
        print("Saving blockchain state...")
        
        # Execute the command to dump the state and save it to the file
        with open(ANVIL_STATE_FILE, "w") as state_file:
            subprocess.run(command_dump, stdout=state_file, check=True, text=True)
            
        print(f"Blockchain state saved to '{ANVIL_STATE_FILE}'.")

        # Stop the Anvil process
        print(f"Stopping Anvil process (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Wait a moment for the process to terminate
        time.sleep(2)
        
        # Remove the PID file
        os.remove(ANVIL_PID_FILE)
        print("Anvil stopped successfully.")

    except FileNotFoundError:
        print("\nError: The 'cast' command was not found.")
        print("Please make sure Foundry is installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"\nError saving Anvil state: {e}")
    except ProcessLookupError:
        print(f"\nAnvil process with PID {pid} was not found. It might have already been stopped.")
        os.remove(ANVIL_PID_FILE)
    except Exception as e:
        print(f"\nAn error occurred while stopping Anvil: {e}")

if __name__ == "__main__":
    while True:
        print("\n--- Anvil Management Menu (Public Access) ---")
        print("1. Start Anvil")
        print("2. Stop Anvil")
        print("3. Exit")
        
        choice = input("Select an option: ")

        if choice == "1":
            start_anvil()
        elif choice == "2":
            stop_anvil()
        elif choice == "3":
            if os.path.exists(ANVIL_PID_FILE):
                print("\nWARNING: Anvil still appears to be running.")
            break
        else:
            print("\nInvalid option. Please try again.")