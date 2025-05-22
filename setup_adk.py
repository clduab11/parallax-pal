#!/usr/bin/env python3
"""
ParallaxMind ADK Setup Script

This script helps set up and configure the Google Cloud Agent Development Kit (ADK)
for the ParallaxMind project. It installs dependencies, initializes the ADK project,
and configures the development environment.
"""

import os
import sys
import subprocess
import argparse
import shutil
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}\n")

def print_step(message):
    print(f"{Colors.BLUE}→ {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def run_command(command, description=None, check=True, shell=False):
    """Run a shell command and handle errors"""
    if description:
        print_step(description)
    
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, text=True, capture_output=True)
        else:
            result = subprocess.run(command, check=check, text=True, capture_output=True)
        
        if result.stdout:
            print(result.stdout)
        
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(f"{Colors.RED}{e.stderr}{Colors.ENDC}")
        return e
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        return None

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("Checking Dependencies")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print_error(f"Python 3.9+ is required. Found Python {python_version.major}.{python_version.minor}")
        return False
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} found")
    
    # Check pip
    pip_result = run_command(["pip", "--version"], check=False)
    if pip_result and pip_result.returncode == 0:
        print_success("pip is installed")
    else:
        print_error("pip is not installed or not in PATH")
        return False
    
    # Check Google Cloud CLI
    gcloud_result = run_command(["gcloud", "--version"], check=False)
    if gcloud_result and gcloud_result.returncode == 0:
        print_success("Google Cloud CLI is installed")
    else:
        print_warning("Google Cloud CLI is not installed or not in PATH")
        print_warning("ADK will be installed but some features might not work correctly")
    
    return True

def install_adk():
    """Install the Agent Development Kit Python package"""
    print_header("Installing Agent Development Kit")
    
    run_command(
        ["pip", "install", "-U", "google-cloud-aiplatform[adk]"],
        description="Installing google-cloud-aiplatform[adk]"
    )
    
    # Verify installation
    try:
        import google.cloud.aiplatform.adk
        print_success("ADK installed successfully")
        return True
    except ImportError:
        print_error("Failed to import ADK package. Installation might have failed.")
        return False

def create_adk_project(project_id, region):
    """Initialize the ADK project"""
    print_header("Initializing ADK Project")
    
    # Initialize ADK project
    run_command(
        ["adk", "init", project_id],
        description=f"Initializing ADK project: {project_id}"
    )
    
    # Configure ADK project
    run_command(
        ["adk", "config", "set", "project_id", project_id],
        description=f"Setting project_id to {project_id}"
    )
    
    run_command(
        ["adk", "config", "set", "region", region],
        description=f"Setting region to {region}"
    )
    
    # Create necessary directories
    for d in ["agents", "schemas", "tools"]:
        os.makedirs(d, exist_ok=True)
    
    print_success(f"ADK project '{project_id}' initialized successfully")
    return True

def setup_development_environment():
    """Set up the development environment for the ADK project"""
    print_header("Setting Up Development Environment")
    
    # Check for Python virtual environment
    if not hasattr(sys, 'base_prefix') or sys.base_prefix == sys.prefix:
        print_warning("Not running in a virtual environment. It's recommended to use a virtual environment.")
        create_venv = input("Create a virtual environment? (y/n): ").lower() == 'y'
        
        if create_venv:
            venv_path = "venv"
            run_command(
                [sys.executable, "-m", "venv", venv_path],
                description=f"Creating virtual environment at {venv_path}"
            )
            
            if os.name == 'nt':  # Windows
                activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
                print_warning(f"Please activate the virtual environment by running: {activate_script}")
            else:  # Unix/Linux/Mac
                activate_script = os.path.join(venv_path, "bin", "activate")
                print_warning(f"Please activate the virtual environment by running: source {activate_script}")
            
            print_warning("Then run this script again.")
            return False
    
    # Install required packages
    print_step("Installing required packages...")
    requirements = [
        "google-cloud-aiplatform[adk]",
        "pydantic",
        "fastapi",
        "uvicorn",
        "requests",
        "tenacity",
        "pytest",
        "black",
        "isort",
        "mypy"
    ]
    
    run_command(
        ["pip", "install", "-U"] + requirements,
        description="Installing required packages"
    )
    
    # Create requirements.txt
    with open("requirements-adk.txt", "w") as f:
        for req in requirements:
            f.write(f"{req}\n")
    
    print_success("Development environment set up successfully")
    print_success("Created requirements-adk.txt with necessary dependencies")
    return True

def setup_adk_project_files():
    """Set up the ADK project files"""
    print_header("Setting Up ADK Project Files")
    
    # Check if adk-spec.yaml exists
    if not os.path.exists("adk-spec.yaml"):
        print_warning("adk-spec.yaml not found")
        print_warning("Please create an adk-spec.yaml file defining your agent structure")
    else:
        print_success("Found adk-spec.yaml")
    
    # Check if schemas directory contains required files
    schemas_dir = "schemas"
    if not os.path.exists(os.path.join(schemas_dir, "agent_messages.py")):
        print_warning("agent_messages.py not found in schemas directory")
        print_warning("Please create schema definitions for agent communication")
    else:
        print_success("Found agent message schemas")
    
    # Check for agents
    agents_dir = "agents"
    if len(os.listdir(agents_dir)) == 0:
        print_warning(f"No agent implementations found in {agents_dir}")
        print_warning("Please create your agent implementations")
    else:
        print_success(f"Found agent implementations in {agents_dir}")
    
    print_success("Project files check completed")
    return True

def main():
    """Main function to run the ADK setup script"""
    parser = argparse.ArgumentParser(description="Set up the ADK project for ParallaxMind")
    parser.add_argument("--project-id", default="parallaxmind", help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="Google Cloud region")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency checks")
    args = parser.parse_args()
    
    print_header("ParallaxMind ADK Setup")
    
    # Check dependencies
    if not args.skip_checks and not check_dependencies():
        print_error("Dependency check failed. Please install required dependencies and try again.")
        return 1
    
    # Install ADK
    if not install_adk():
        print_error("Failed to install ADK. Please check the output and try again.")
        return 1
    
    # Create ADK project
    if not create_adk_project(args.project_id, args.region):
        print_error("Failed to create ADK project. Please check the output and try again.")
        return 1
    
    # Set up development environment
    if not setup_development_environment():
        return 1
    
    # Set up ADK project files
    setup_adk_project_files()
    
    print_header("Setup Complete")
    print_success("ADK project setup completed successfully!")
    print("")
    print(f"{Colors.BOLD}Next steps:{Colors.ENDC}")
    print(f"1. Review the agent implementations in the {Colors.BOLD}agents/{Colors.ENDC} directory")
    print(f"2. Run {Colors.BOLD}adk run --agent parallaxmind{Colors.ENDC} to test your agents locally")
    print(f"3. Deploy your agents with {Colors.BOLD}adk deploy{Colors.ENDC}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())