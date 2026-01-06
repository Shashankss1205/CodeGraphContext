#!/bin/bash
set -e

echo "Running Post Install fix for CodeGraphContext..."

detect_shell_config() {
    # Windows PowerShell detection
    if [[ "$OS" == "Windows_NT" ]] && [[ -n "$PROFILE" ]]; then
        echo "$PROFILE"
        return
    fi
    
    # Unix/Linux/Mac shell detection
    if [ "$SHELL" = "/bin/bash" ] || [ "$SHELL" = "/usr/bin/bash" ]; then
        echo "$HOME/.bashrc"
    elif [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
        echo "$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        echo "$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "$HOME/.zshrc"
    else
        echo "$HOME/.profile"
    fi
}

# Add to PATH for Windows PowerShell
fix_windows_path() {
    local profile_file="$1"
    local path_line='$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"'
    
    echo "Using PowerShell profile: $profile_file"
    
    # Create profile directory if needed
    local profile_dir=$(dirname "$profile_file")
    mkdir -p "$profile_dir" 2>/dev/null || true
    
    # Check if already configured
    if [[ -f "$profile_file" ]] && grep -q ".local" "$profile_file"; then
        echo "PATH is already configured in PowerShell profile"
    else
        echo "Adding to PowerShell PATH..."
        echo "" >> "$profile_file"
        echo "# Added by CodeGraphContext" >> "$profile_file"
        echo "$path_line" >> "$profile_file"
        echo "Added PATH to PowerShell profile"
    fi
    
    # Add to current session (Windows style)
    export PATH="$USERPROFILE/.local/bin:$PATH"
    
    echo "⚠️ Please restart PowerShell or run: . \$PROFILE"
}

# Add to PATH for Linux/Mac
fix_unix_path() {
    local config_file="$1"
    local path_line='export PATH="$HOME/.local/bin:$PATH"'

    echo "Using shell config: $config_file"

    # check if PATH is already configured
    if [ -f "$config_file" ] && grep -q ".local/bin" "$config_file"; then
        echo "PATH is already configured in $config_file"
    else
        echo "Adding ~/.local/bin to PATH..."
        echo "" >> "$config_file"
        echo "# Added by CodeGraphContext" >> "$config_file"
        echo "$path_line" >> "$config_file"
        echo "Added PATH to $config_file"
    fi

    # Source the config for current session
    echo "Sourcing/Reloading shell config for current session..."
    export PATH="$HOME/.local/bin:$PATH"

    # source it 
    if [ -f "$config_file" ]; then
        source "$config_file" 2>/dev/null || true
    fi
}

# Main PATH fixing function
fix_path() {
    local config_file=$(detect_shell_config)
    
    # Check if we're on Windows
    if [[ "$OS" == "Windows_NT" ]] && [[ -n "$PROFILE" ]]; then
        fix_windows_path "$config_file"
    else
        fix_unix_path "$config_file"
    fi
}

check_cgc() {
    if command -v cgc >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Get potential cgc locations based on platform
get_cgc_locations() {
    if [[ "$OS" == "Windows_NT" ]]; then
        # Windows locations
        echo "$USERPROFILE/.local/bin/cgc.exe"
        echo "$USERPROFILE/.local/bin/cgc"
        echo "$HOME/.local/bin/cgc.exe"
        echo "$HOME/.local/bin/cgc"
    else
        # Linux/Mac locations
        echo "$HOME/.local/bin/cgc"
    fi
}


# Main execution
if check_cgc; then
    echo "✅ cgc (CodeGraphContext) is already available!"
else
    echo "⚠️ cgc command not found, fixing PATH..."

    # Check if cgc exists in expected locations
    cgc_found=false
    for cgc_path in $(get_cgc_locations); do
        if [[ -f "$cgc_path" ]]; then
            cgc_found=true
            echo "📍 Found cgc at: $cgc_path"
            break
        fi
    done

    if [[ "$cgc_found" == true ]]; then
        fix_path

        # Check again
        if check_cgc; then
            echo "✅ cgc command (CodeGraphContext) is now available to use!"
            echo "You can now run: cgc neo4j setup"
        else
            if [[ "$OS" == "Windows_NT" ]]; then
                echo "⚠️ Please restart PowerShell or run: . \$PROFILE"
            else
                echo "❌ There seems to still be an issue... Please reload your terminal manually."
            fi
        fi
    else
        if [[ "$OS" == "Windows_NT" ]]; then
            echo "❌ cgc not found in expected Windows locations. Please reinstall:"
            echo "   pip install codegraphcontext"
        else
            echo "❌ cgc not found in ~/.local/bin. Please reinstall:"
            echo "   pip install codegraphcontext"
        fi
    fi
fi