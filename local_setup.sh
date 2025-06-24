#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "❌ This script must be sourced. Please run: source ${BASH_SOURCE[0]}"
  exit 1
fi

# Don't use set -e when sourcing, as it can exit the shell
# set -e
source .env

# Install pyenv and pyenv-virtualenv if not installed
if ! command -v pyenv &>/dev/null; then
  echo "✉️ Installing pyenv and pyenv-virtualenv with homebrew..."
  brew install pyenv pyenv-virtualenv
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
else
  echo "✉️ Pyenv and pyenv-virtualenv already installed."
  # Make sure pyenv is initialized in current shell
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
fi

# Install python version if not installed
if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
  echo "✉️ Installing python $PYTHON_VERSION with pyenv..."
  pyenv install $PYTHON_VERSION
else
  echo "✉️ Python $PYTHON_VERSION already installed."
fi

# Create virtualenv if not created
if ! pyenv virtualenvs --bare | grep -q "^${VIRTUALENV_NAME}$"; then
  echo "✉️ Creating virtualenv $VIRTUALENV_NAME..."
  pyenv virtualenv $PYTHON_VERSION $VIRTUALENV_NAME
  pyenv local $VIRTUALENV_NAME
else
  echo "✉️ Virtualenv $VIRTUALENV_NAME already created."
  # Check if it's using the correct Python version
  current_python=$(pyenv activate $VIRTUALENV_NAME 2>/dev/null && python --version 2>&1 | cut -d' ' -f2 || echo "unknown")
  if [[ "$current_python" != "$PYTHON_VERSION" && "$current_python" != "unknown" ]]; then
    echo "⚠️  Virtualenv $VIRTUALENV_NAME is using Python $current_python but $PYTHON_VERSION is specified in .env"
    echo "✉️ Recreating virtualenv with correct Python version..."
    pyenv virtualenv-delete -f $VIRTUALENV_NAME 2>/dev/null || true
    pyenv virtualenv $PYTHON_VERSION $VIRTUALENV_NAME
    pyenv local $VIRTUALENV_NAME
  fi
fi

# Activate virtualenv if not activated
current_env=$(pyenv local 2>/dev/null || echo "")
if [[ "$current_env" != "$VIRTUALENV_NAME" ]]; then
  echo "✉️ Activating virtualenv $VIRTUALENV_NAME..."
  pyenv local $VIRTUALENV_NAME
else
  echo "✉️ Virtualenv $VIRTUALENV_NAME already activated."
fi

# Install requirements
echo "✉️ Installing requirements..."
pip install --upgrade pip
if pip-compile requirements.in && pip-sync requirements.txt; then
  pip install -r requirements.txt
else
  echo "⚠️ pip-compile/pip-sync failed, installing requirements directly..."
  pip install -r requirements.txt
fi
pip install -r dev_requirements.txt

# Install pnpm if not installed
if ! command -v pnpm &>/dev/null; then
  echo "✉️ Installing pnpm..."
  npm install -g pnpm
fi
pnpm install
npx lefthook install

echo "✅ Setup complete! Python version: $(python --version)"
