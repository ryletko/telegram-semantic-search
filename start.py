"""
Startup script for Telegram Semantic Search application.
Launches both the backend and frontend simultaneously.
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit

# Platform-specific settings
is_windows = sys.platform.startswith("win")

# Use the current Python executable (includes virtual environment if active)
python_cmd = sys.executable
npm_cmd = "npm.cmd" if is_windows else "npm"

# Global process variables
backend_process = None
frontend_process = None


def cleanup_processes():
    """Clean up processes on exit"""
    print("\nShutting down services...")

    if frontend_process:
        if is_windows:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)])
        else:
            os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)

    if backend_process:
        if is_windows:
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)])
        else:
            os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)

    print("All services have been stopped.")


def start_backend():
    """Start the Flask backend server"""
    global backend_process

    print("Starting backend server...")
    print(f"Using Python interpreter: {python_cmd}")

    if is_windows:
        backend_process = subprocess.Popen(
            [python_cmd, "app.py"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        backend_process = subprocess.Popen([python_cmd, "app.py"], preexec_fn=os.setsid)

    # Give the backend a moment to start
    time.sleep(2)

    # Check if process is still running (didn't crash immediately)
    if backend_process.poll() is not None:
        print("ERROR: Backend server failed to start.")
        print(
            "Check that all required packages are installed in your virtual environment."
        )
        print("Try running: pip install -r requirements.txt")
        return False

    print("Backend server running at http://localhost:5000")
    return True


def start_frontend():
    """Start the Vue.js development server"""
    global frontend_process

    print("Starting frontend development server...")
    os.chdir("frontend")

    # First check if node_modules exists, if not, run npm install
    if not os.path.exists("node_modules"):
        print("Installing frontend dependencies...")
        subprocess.run([npm_cmd, "install"], check=True)

    if is_windows:
        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev"], preexec_fn=os.setsid
        )

    # Change back to original directory
    os.chdir("..")

    # Give the frontend a moment to start
    time.sleep(3)

    # Check if process is still running
    if frontend_process.poll() is not None:
        print("ERROR: Frontend server failed to start.")
        print("Check that Node.js is installed and that the frontend code is intact.")
        return False

    print("Frontend server running at http://localhost:5173")
    return True


def main():
    """Main function to start all services"""
    print("Starting Telegram Semantic Search application...")

    # Register cleanup function
    atexit.register(cleanup_processes)

    # Start backend
    backend_started = start_backend()
    if not backend_started:
        sys.exit(1)

    # Start frontend
    frontend_started = start_frontend()
    if not frontend_started:
        sys.exit(1)

    # Open browser
    print("Opening application in browser...")
    webbrowser.open("http://localhost:5173")

    print("\nApplication is now running!")
    print("Press Ctrl+C to stop all services.")

    try:
        # Keep the script running to maintain the processes
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("Backend server stopped unexpectedly.")
                break

            if frontend_process.poll() is not None:
                print("Frontend server stopped unexpectedly.")
                break

            time.sleep(1)
    except KeyboardInterrupt:
        # This will trigger the atexit handler
        pass


if __name__ == "__main__":
    main()
