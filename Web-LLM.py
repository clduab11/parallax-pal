#!/usr/bin/env python3
"""
Parallax Pal - Your AI Research Assistant
This script serves as the main entry point for Parallax Pal, redirecting to Self_Improving_Search.py
"""

import os
import sys
from colorama import init, Fore, Style
from parallax_pal import main as parallax_main

# Initialize colorama for Windows
if os.name == 'nt':
    init(convert=True)
else:
    init()

if __name__ == "__main__":
    print(f"{Fore.CYAN}Redirecting to Parallax Pal...{Style.RESET_ALL}")
    parallax_main()
