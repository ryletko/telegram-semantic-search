import os
import subprocess
import sys
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor

def run_flask():
    print("Starting Flask backend...")
    env = os.environ.copy()
    env["FLASK_ENV"] = "development"
    flask_proc = subprocess.Popen([sys.executable, "app.py"], env=env)
    return flask_proc

def run_vite():
    print("Starting Vite dev server...")
    if os.name == 'nt':  # Windows
        vite_proc = subprocess.Popen(["npm", "run", "dev"], cwd="frontend", shell=True)
    else:  # Unix/Mac
        vite_proc = subprocess.Popen(["npm", "run", "dev"], cwd="frontend")
    return vite_proc

def main():
    # Handle termination signals
    def handle_signal(sig, frame):
        print("\nShutting down servers...")
        if vite_proc:
            if os.name == 'nt':  # Windows
                vite_proc.kill()
            else:
                vite_proc.terminate()
        if flask_proc:
            flask_proc.terminate()
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Start both servers
    flask_proc = None
    vite_proc = None

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            flask_future = executor.submit(run_flask)
            # Wait a bit for Flask to start
            time.sleep(2)
            vite_future = executor.submit(run_vite)
            
            flask_proc = flask_future.result()
            vite_proc = vite_future.result()
            
            # Print info
            print("\n-----------------------------------------")
            print("Development servers are running!")
            print("Flask API: http://localhost:5000")
            print("Vite Dev Server: http://localhost:5173")
            print("Press Ctrl+C to stop both servers")
            print("-----------------------------------------\n")
            
            # Keep the script running
            flask_proc.wait()
            
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        # Clean up
        if vite_proc:
            if os.name == 'nt':  # Windows
                vite_proc.kill()
            else:
                vite_proc.terminate()
        if flask_proc:
            flask_proc.terminate()

if __name__ == "__main__":
    main() 