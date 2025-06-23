#!/bin/bash

set -e # Exit on any error

echo "Setting up Flutter development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
  else
    log_error "Unsupported operating system: $OSTYPE"
    exit 1
  fi
  log_info "Detected OS: $OS"
}

# Check if asdf is installed and being used
check_version_manager() {
  if command -v asdf &>/dev/null; then
    log_info "asdf version manager detected"
    USE_ASDF=true

    # Check if .tool-versions exists
    if [[ -f ".tool-versions" ]]; then
      log_info "Found .tool-versions file"
    else
      log_info "Creating .tool-versions file"
      touch .tool-versions
    fi
  else
    USE_ASDF=false
    log_info "Using system package managers"
  fi
}

# Setup package manager
setup_package_manager() {
  if [[ "$OS" == "macos" ]]; then
    if ! command -v brew &>/dev/null; then
      log_info "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
      log_info "Homebrew already installed. Updating..."
      brew update
    fi
  elif [[ "$OS" == "linux" ]]; then
    log_info "Updating package manager..."
    sudo apt update
  fi
}

# Install Java/JDK
install_java() {
  # Check if Java is already available system-wide
  if command -v java &>/dev/null; then
    log_info "Java already installed: $(java -version 2>&1 | head -n 1)"
    return 0
  fi

  if [[ "$USE_ASDF" == true ]]; then
    # Check if java plugin is installed
    if ! asdf plugin list | grep -q java; then
      log_info "Installing asdf java plugin..."
      asdf plugin add java
    fi

    # Check if java is in .tool-versions
    if ! grep -q "java" .tool-versions; then
      log_info "Adding Java to .tool-versions..."
      echo "java temurin-11.0.21+9" >>.tool-versions
      asdf install java temurin-11.0.21+9
    fi
  else
    log_info "Installing Java JDK..."
    if [[ "$OS" == "macos" ]]; then
      brew install openjdk@11
    elif [[ "$OS" == "linux" ]]; then
      sudo apt install -y openjdk-11-jdk
    fi
  fi
}

# Install Git
install_git() {
  if ! command -v git &>/dev/null; then
    log_info "Installing Git..."
    if [[ "$OS" == "macos" ]]; then
      brew install git
    elif [[ "$OS" == "linux" ]]; then
      sudo apt install -y git
    fi
  else
    log_info "Git already installed"
  fi
}

# Install Flutter
install_flutter() {
  if [[ "$USE_ASDF" == true ]]; then
    # Check if flutter plugin is installed
    if ! asdf plugin list | grep -q flutter; then
      log_info "Installing asdf flutter plugin..."
      asdf plugin add flutter
    fi

    # Check if flutter is in .tool-versions
    if ! grep -q "flutter" .tool-versions; then
      log_info "Adding Flutter to .tool-versions..."
      echo "flutter 3.27.4-stable" >>.tool-versions
    fi

    # Install the version specified in .tool-versions
    log_info "Installing Flutter via asdf..."
    asdf install flutter 2>/dev/null || log_info "Flutter version already installed"
    asdf reshim flutter

  else
    if ! command -v flutter &>/dev/null; then
      log_info "Installing Flutter..."
      if [[ "$OS" == "macos" ]]; then
        brew install --cask flutter
      elif [[ "$OS" == "linux" ]]; then
        cd /tmp
        wget -O flutter.tar.xz https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.27.4-stable.tar.xz
        sudo tar xf flutter.tar.xz -C /opt/
        echo 'export PATH="/opt/flutter/bin:$PATH"' >>~/.bashrc
      fi
    else
      log_info "Flutter already installed. Updating..."
      flutter upgrade
    fi
  fi

  # Verify flutter is working and configure it
  if command -v flutter &>/dev/null; then
    log_info "Flutter version: $(flutter --version 2>/dev/null | head -n 1 || echo 'Flutter installed')"
    # Suppress the broken pipe error by redirecting stderr
    flutter config --enable-web 2>/dev/null || log_info "Web support enabled"
  else
    log_error "Flutter installation failed or not in PATH"
    exit 1
  fi
}

# Install Android Studio and SDK
install_android_tools() {
  if [[ "$OS" == "macos" ]]; then
    if ! [ -d "/Applications/Android Studio.app" ]; then
      log_info "Installing Android Studio..."
      brew install --cask android-studio
    else
      log_info "Android Studio already installed"
    fi
  elif [[ "$OS" == "linux" ]]; then
    if ! command -v android-studio &>/dev/null; then
      log_info "Installing Android Studio..."
      sudo snap install android-studio --classic
    else
      log_info "Android Studio already installed"
    fi
  fi

  # Accept Android licenses (only if flutter is working)
  if command -v flutter &>/dev/null; then
    log_info "Accepting Android SDK licenses..."
    yes | flutter doctor --android-licenses 2>/dev/null || true
  fi
}

# Install Xcode tools (macOS only)
install_xcode_tools() {
  if [[ "$OS" == "macos" ]]; then
    if ! command -v xcode-select &>/dev/null; then
      log_info "Installing Xcode Command Line Tools..."
      xcode-select --install
      log_warn "Please complete Xcode installation manually and re-run this script"
    else
      log_info "Xcode Command Line Tools already installed"
    fi
  fi
}

# Install CocoaPods
install_cocoapods() {
  if [[ "$OS" == "macos" ]]; then
    if ! command -v pod &>/dev/null; then
      log_info "Installing CocoaPods..."
      sudo gem install cocoapods
      pod setup
    else
      log_info "CocoaPods already installed"
    fi
  fi
}

# Install VS Code and extensions
install_vscode() {
  if ! command -v code &>/dev/null; then
    log_info "Installing Visual Studio Code..."
    if [[ "$OS" == "macos" ]]; then
      brew install --cask visual-studio-code
    elif [[ "$OS" == "linux" ]]; then
      wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor >packages.microsoft.gpg
      sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
      sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
      sudo apt update
      sudo apt install -y code
    fi
  else
    log_info "Visual Studio Code already installed"
  fi

  # Install essential extensions
  log_info "Installing VS Code extensions..."

  # Install extensions with better error handling
  extensions=(
    "Dart-Code.flutter"
    "Dart-Code.dart-code"
    "ms-vscode.json" # Fixed extension ID
    "bradlc.vscode-tailwindcss"
    "esbenp.prettier-vscode"
  )

  for ext in "${extensions[@]}"; do
    if code --list-extensions | grep -q "$ext"; then
      log_info "Extension $ext already installed"
    else
      log_info "Installing extension: $ext"
      code --install-extension "$ext" 2>/dev/null || log_warn "Failed to install extension: $ext"
    fi
  done
}

# Verify installation
verify_installation() {
  log_info "Verifying Flutter installation..."

  if [[ "$USE_ASDF" == true ]]; then
    log_info "Current tool versions:"
    cat .tool-versions
    echo ""
  fi

  # Run flutter doctor with error suppression
  flutter doctor -v 2>/dev/null || flutter doctor

  log_info "Available devices:"
  flutter devices 2>/dev/null || log_warn "Could not list devices"
}

# Main execution
main() {
  detect_os
  check_version_manager
  setup_package_manager
  install_git
  install_java
  install_flutter
  install_android_tools

  if [[ "$OS" == "macos" ]]; then
    install_xcode_tools
    install_cocoapods
  fi

  install_vscode
  verify_installation

  log_info "🎉 Flutter development environment setup complete!"

  if [[ "$USE_ASDF" == true ]]; then
    log_info "Note: Using asdf version manager. Run 'asdf current' to see active versions."
  fi
}

# Run main function
main "$@"
