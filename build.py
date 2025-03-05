#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil
from pathlib import Path

def main():
    print("🔨 Building Telegram Semantic Search application...")
    
    # Check if we're in the project root
    project_root = Path(os.getcwd())
    frontend_dir = project_root / "frontend"
    static_dir = project_root / "static"
    dist_dir = frontend_dir / "dist"
    
    if not frontend_dir.exists():
        print(f"❌ Error: Frontend directory not found at {frontend_dir}")
        sys.exit(1)
    
    # Check if npm is installed
    print("\n🔍 Checking for npm...")
    npm_found = False
    
    try:
        # Try the standard method first
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        npm_found = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try with shell=True as an alternative on Windows
        try:
            subprocess.run("npm --version", shell=True, check=True, capture_output=True)
            npm_found = True
        except subprocess.CalledProcessError:
            npm_found = False
    
    if not npm_found:
        print("❌ Error: npm not found. Please install Node.js and npm.")
        print("\nInstallation instructions:")
        print("1. Download Node.js from https://nodejs.org/")
        print("2. Run the installer and follow the instructions")
        print("3. Restart your terminal/PowerShell and try again")
        sys.exit(1)
    
    # Check for node_modules directory and install dependencies if needed
    node_modules_dir = frontend_dir / "node_modules"
    if not node_modules_dir.exists():
        print("\n📦 Installing npm dependencies...")
        install_command = "npm install"
        try:
            result = subprocess.run(install_command, cwd=str(frontend_dir), shell=True, check=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, install_command)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: Failed to install dependencies. Error code: {e.returncode}")
            sys.exit(1)
    
    # Build frontend
    print("\n📦 Building frontend with Vite...")
    build_command = "npm run build"
    
    try:
        # Use shell=True for Windows compatibility
        result = subprocess.run(build_command, cwd=str(frontend_dir), shell=True, check=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, build_command)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Failed to build frontend. Error code: {e.returncode}")
        sys.exit(1)
    
    # Copy built files to static directory
    if dist_dir.exists():
        print("\n📂 Copying built files to static directory...")
        
        # Clear existing static directory
        if static_dir.exists():
            shutil.rmtree(static_dir)
        
        # Create static directory
        static_dir.mkdir(exist_ok=True)
        
        # Copy files
        for item in dist_dir.glob('*'):
            if item.is_dir():
                shutil.copytree(item, static_dir / item.name)
            else:
                shutil.copy2(item, static_dir / item.name)
        
        print("✅ Files copied successfully!")
    else:
        print(f"❌ Error: Build output directory not found at {dist_dir}")
        sys.exit(1)
    
    print("\n✅ Build completed successfully!")
    print("\nTo run the application:")
    print("  python app.py")
    print("\nThen open your browser at: http://localhost:5000")

if __name__ == "__main__":
    main() 