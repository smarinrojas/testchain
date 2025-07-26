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
ANVIL_LOG_FILE = "anvil.log" # File to store Anvil's output

def start_anvil():
    """
    Starts Anvil as a detached background process, saving its logs to a file.
    """
    if os.path.exists(ANVIL_PID_FILE):
        print("\nError: Anvil appears to be already running. Check the anvil.pid file.")
        return

    command = ["anvil", "--host", ANVIL_HOST, "--port", str(ANVIL_PORT)]

    if os.path.exists(ANVIL_STATE_FILE):
        print(f"\nInfo: State file '{ANVIL_STATE_FILE}' found. Loading previous state...")
        command.extend(["--load-state", ANVIL_STATE_FILE])
    else:
        print("\nInfo: No state file found. Starting a new blockchain.")

    try:
        print(f"Starting Anvil in the background. Logs will be saved to '{ANVIL_LOG_FILE}'...")

        # Open the log file in append mode
        log_file = open(ANVIL_LOG_FILE, 'a')
        
        # Platform-specific arguments for creating a detached process
        popen_kwargs = {}
        if os.name == 'posix':
            # On Linux/macOS, os.setsid makes the process a new session leader
            popen_kwargs['preexec_fn'] = os.setsid
        elif os.name == 'nt':
            # On Windows, DETACHED_PROCESS flag creates a new process without a console
            DETACHED_PROCESS = 0x00000008
            popen_kwargs['creationflags'] = DETACHED_PROCESS

        # Start Anvil as a truly detached process, redirecting stdout/stderr to the log file
        process = subprocess.Popen(
            command, 
            stdout=log_file, 
            stderr=subprocess.STDOUT, 
            **popen_kwargs
        )
        
        # Save the process ID (PID)
        with open(ANVIL_PID_FILE, "w") as f:
            f.write(str(process.pid))
            
        print(f"\nSuccess: Anvil started successfully as a background process. PID: {process.pid}")
        print(f"   Listening on ALL interfaces ({ANVIL_HOST}) on port {ANVIL_PORT}")
        print("\n   IMPORTANT SECURITY WARNING!")
        print("   Exposing Anvil to the internet can be risky. Ensure your firewall")
        print(f"   is configured to allow traffic on port {ANVIL_PORT} only from trusted IPs.")

    except FileNotFoundError:
        print("\nError: The 'anvil' command was not found.")
        print("   Please make sure Foundry and Anvil are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nError: An error occurred while starting Anvil: {e}")

def stop_anvil():
    """
    Stops the running Anvil process and saves its state.
    """
    if not os.path.exists(ANVIL_PID_FILE):
        print("\nInfo: Anvil does not appear to be running (anvil.pid not found).")
        return

    with open(ANVIL_PID_FILE, "r") as f:
        pid = int(f.read())

    try:
        rpc_url_local = f"http://127.0.0.1:{ANVIL_PORT}"
        command_dump = ["cast", "rpc", "anvil_dumpState", "--rpc-url", rpc_url_local]
        
        print("\nSaving blockchain state...")
        with open(ANVIL_STATE_FILE, "w", encoding='utf-8') as state_file:
            subprocess.run(command_dump, stdout=state_file, check=True, text=True)
        print(f"   State successfully saved to '{ANVIL_STATE_FILE}'.")

        print(f"Stopping Anvil process (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        os.remove(ANVIL_PID_FILE)
        print("Success: Anvil stopped successfully.")

    except FileNotFoundError:
        print("\nError: The 'cast' command was not found.")
    except subprocess.CalledProcessError:
        print(f"\nError saving Anvil state. Is Anvil running and accessible at {rpc_url_local}?")
    except ProcessLookupError:
        print(f"\nInfo: Anvil process with PID {pid} was not found. Removing stale PID file.")
        os.remove(ANVIL_PID_FILE)
    except Exception as e:
        print(f"\nError: An error occurred while stopping Anvil: {e}")

def view_logs():
    """
    Displays the Anvil log file in real-time.
    """
    if not os.path.exists(ANVIL_LOG_FILE):
        print(f"\nInfo: Log file '{ANVIL_LOG_FILE}' not found. Have you started Anvil yet?")
        return

    print(f"\nStreaming logs from '{ANVIL_LOG_FILE}'. Press Ctrl+C to stop.")
    try:
        # Platform-independent way to tail a file would be more complex,
        # so we rely on system commands which are standard.
        if os.name == 'posix':
            # Use 'tail -f' on Linux/macOS
            subprocess.run(["tail", "-f", ANVIL_LOG_FILE])
        elif os.name == 'nt':
            # Use PowerShell's 'Get-Content -Wait' on Windows
            subprocess.run([
                "powershell", "-Command", 
                f"Get-Content '{ANVIL_LOG_FILE}' -Wait"
            ])
    except KeyboardInterrupt:
        print("\nStopped viewing logs.")
    except FileNotFoundError:
        print("\nError: 'tail' (or PowerShell for Windows) command not found.")


def main_menu():
    """
    Displays the main interactive menu and handles user choices.
    """
    while True:
        # Check current status for display
        status = "Running" if os.path.exists(ANVIL_PID_FILE) else "Stopped"

        questions = [
            inquirer.List(
                'action',
                message=f"Anvil Manager | Status: {status}",
                choices=['Start Anvil', 'Stop Anvil', 'View Anvil Logs', 'Exit'],
                carousel=True
            ),
        ]
        
        try:
            answers = inquirer.prompt(questions, theme=GreenPassion())
            if not answers:  # User pressed Ctrl+C
                break

            choice = answers['action']

            if choice == 'Start Anvil':
                start_anvil()
            elif choice == 'Stop Anvil':
                stop_anvil()
            elif choice == 'View Anvil Logs':
                view_logs()
            elif choice == 'Exit':
                if os.path.exists(ANVIL_PID_FILE):
                    print("\nWARNING: Anvil still appears to be running.")
                break
        
        except KeyboardInterrupt: # Catches Ctrl+C again for graceful exit
            break
        
        # Only pause if not coming back from the log viewer
        if answers and answers['action'] != 'View Anvil Logs':
             input("\nPress Enter to return to the menu...")
        
        # Clear screen for a cleaner interface (optional)
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    main_menu()
    print("\nGoodbye!")