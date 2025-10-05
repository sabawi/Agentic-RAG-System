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
    local venv_names=("venv" ".venv" "env" ".env" "virtualenv")
    
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

# Check if we need to activate the project's virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    # No virtual environment active - activate one
    activate_venv
else
    # Virtual environment is active - check if it's the correct one for this project
    project_venv_path=""

    # Find the project's virtual environment path
    venv_names=("venv" ".venv" "env" ".env" "virtualenv")
    for venv_name in "${venv_names[@]}"; do
        if [ -d "$venv_name" ] && [ -f "$venv_name/bin/activate" ]; then
            project_venv_path="$(pwd)/$venv_name"
            break
        fi
    done

    # If no named venv found, check for any directory with bin/activate
    if [ -z "$project_venv_path" ]; then
        for dir in */; do
            if [ -f "${dir}bin/activate" ]; then
                project_venv_path="$(pwd)/${dir%/}"
                break
            fi
        done
    fi

    if [ -n "$project_venv_path" ] && [ "$VIRTUAL_ENV" != "$project_venv_path" ]; then
        # Wrong virtual environment - switch to project's venv
        echo "🔄 Switching from $(basename "$VIRTUAL_ENV") to project virtual environment..."
        deactivate 2>/dev/null || true
        activate_venv
    elif [ -n "$project_venv_path" ] && [ "$VIRTUAL_ENV" = "$project_venv_path" ]; then
        # Already in correct virtual environment
        echo "✅ Correct virtual environment already active: $(basename "$VIRTUAL_ENV")"
    else
        # No project venv found, but another venv is active
        echo "🐍 Virtual environment active: $(basename "$VIRTUAL_ENV") (no project venv found)"
    fi
fi
