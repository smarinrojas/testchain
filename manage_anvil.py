import subprocess
import os
import time
import signal
import inquirer
from inquirer.themes import GreenPassion

# --- Configuration ---
ANVIL_STATE_FILE = "anvil_state.json"
ANVIL_HOST = "0.0.0.0" 
ANVIL_PORT = 8545
ANVIL_PID_FILE = "anvil.pid"
ANVIL_LOG_FILE = "anvil.log"

def start_anvil():
    """
    Starts Anvil as a background process without prior validation.
    It overwrites any existing PID file.
    """
    command = ["anvil", "--host", ANVIL_HOST, "--port", str(ANVIL_PORT)]

    if os.path.exists(ANVIL_STATE_FILE):
        print(f"\nInfo: State file '{ANVIL_STATE_FILE}' found. Loading state...")
        command.extend(["--load-state", ANVIL_STATE_FILE])
    else:
        print("\nInfo: No state file found. Starting a new blockchain.")

    try:
        print(f"Executing command to start Anvil. Logs will be saved to '{ANVIL_LOG_FILE}'...")
        # Use 'w' to start with a clean log file each time
        log_file = open(ANVIL_LOG_FILE, 'w') 

        popen_kwargs = {}
        if os.name == 'posix':
            popen_kwargs['preexec_fn'] = os.setsid
        elif os.name == 'nt':
            DETACHED_PROCESS = 0x00000008
            popen_kwargs['creationflags'] = DETACHED_PROCESS

        process = subprocess.Popen(
            command, 
            stdout=log_file, 
            stderr=subprocess.STDOUT, 
            **popen_kwargs
        )
        
        with open(ANVIL_PID_FILE, "w") as f:
            f.write(str(process.pid))
            
        print(f"\nSuccess: Start command sent to Anvil. PID: {process.pid}")

    except FileNotFoundError:
        print("\nError: The 'anvil' command was not found.")
        print("   Please make sure Foundry is installed and in your system's PATH.")
    except Exception as e:
        print(f"\nError: An error occurred while trying to start Anvil: {e}")

def stop_anvil():
    """
    Attempts to stop the Anvil process based on the PID file, without validation.
    It always cleans up the PID file.
    """
    print("\nAttempting to stop Anvil...")
    try:
        with open(ANVIL_PID_FILE, "r") as f:
            pid = int(f.read())

        # 1. Attempt to save state (this may fail if the process is already dead)
        try:
            print("Attempting to save the blockchain state...")
            rpc_url_local = f"http://127.0.0.1:{ANVIL_PORT}"
            command_dump = ["cast", "rpc", "anvil_dumpState", "--rpc-url", rpc_url_local]
            with open(ANVIL_STATE_FILE, "w", encoding='utf-8') as state_file:
                subprocess.run(command_dump, stdout=state_file, check=True, text=True, timeout=10)
            print("   State saved successfully.")
        except Exception as e:
            print(f"   Warning: Could not save state. The process might have already been stopped. ({e})")

        # 2. Attempt to kill the process
        try:
            print(f"Sending stop signal to process with PID {pid}...")
            os.kill(pid, signal.SIGTERM)
            print("   Stop signal sent.")
        except ProcessLookupError:
            print(f"   Warning: Process with PID {pid} was not found. It was already stopped.")
        except Exception as e:
            print(f"   Error while stopping the process: {e}")

    except FileNotFoundError:
        print("Info: anvil.pid file not found. Nothing to stop.")
    except Exception as e:
        print(f"Error: An unexpected error occurred during the stop process: {e}")
    finally:
        # 3. Always clean up the PID file if it exists
        if os.path.exists(ANVIL_PID_FILE):
            os.remove(ANVIL_PID_FILE)
            print("Cleanup: PID file removed.")

def view_logs():
    """
    Displays the Anvil log file in real-time.
    """
    if not os.path.exists(ANVIL_LOG_FILE):
        print(f"\nInfo: Log file '{ANVIL_LOG_FILE}' does not exist. Start Anvil first.")
        return

    print(f"\nStreaming logs from '{ANVIL_LOG_FILE}'. Press Ctrl+C to stop.")
    try:
        if os.name == 'posix':
            subprocess.run(["tail", "-f", ANVIL_LOG_FILE])
        elif os.name == 'nt':
            subprocess.run(["powershell", "-Command", f"Get-Content '{ANVIL_LOG_FILE}' -Wait"])
    except KeyboardInterrupt:
        print("\nStopped viewing logs.")
    except FileNotFoundError:
        print("\nError: 'tail' (or PowerShell) command not found.")


def main_menu():
    """
    Displays the main interactive menu.
    """
    while True:
        status = "Assumed Running (Check logs)" if os.path.exists(ANVIL_PID_FILE) else "Stopped"
        questions = [
            inquirer.List(
                'action',
                message=f"Anvil Manager | Inferred Status: {status}",
                choices=['Start Anvil', 'Stop Anvil', 'View Anvil Logs', 'Exit'],
                carousel=True
            ),
        ]
        try:
            answers = inquirer.prompt(questions, theme=GreenPassion())
            if not answers: break
            choice = answers['action']

            if choice == 'Start Anvil':
                start_anvil()
            elif choice == 'Stop Anvil':
                stop_anvil()
            elif choice == 'View Anvil Logs':
                view_logs()
            elif choice == 'Exit':
                break
        except KeyboardInterrupt:
            break
        
        if answers and answers['action'] != 'View Anvil Logs':
             input("\nPress Enter to return to the menu...")
        
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    main_menu()
    print("\nGoodbye.")