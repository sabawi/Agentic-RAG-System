#!/bin/bash
# Auto-activate virtual environment when entering the project directory
# Discovers virtual environment automatically
#
# CUSTOMIZATION:
# To prioritize a specific virtual environment name, edit the venv_names array below.
# The script will try each name in order until it finds a valid virtual environment.

# Function to find and activate virtual environment
activate_venv() {
    # Common virtual environment directory names (in order of preference)
    local venv_names=("venv" "venv_fastapi" ".venv" "env" ".env" "virtualenv")
    
    for venv_name in "${venv_names[@]}"; do
        if [ -d "$venv_name" ] && [ -f "$venv_name/bin/activate" ]; then
            echo "🐍 Activating virtual environment: $venv_name"
            source "./$venv_name/bin/activate"
            return 0
        fi
    done
    
    # Check for any directory with bin/activate
    for dir in */; do
        if [ -f "${dir}bin/activate" ]; then
            echo "🐍 Activating virtual environment: ${dir%/}"
            source "./${dir}bin/activate"
            return 0
        fi
    done
    
    echo "⚠️  No virtual environment found. Create one with:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    return 1
}

# Only activate if not already in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    activate_venv
else
    echo "🐍 Virtual environment already active: $(basename "$VIRTUAL_ENV")"
fi
