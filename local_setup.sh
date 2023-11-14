#!/bin/bash

set -e
source .env

# Install pyenv and pyenv-virtualenv if not installed
if ! command -v pyenv &> /dev/null
then
    echo "✉️ Installing pyenv and pyenv-virtualenv with honebrew..."
    brew install pyenv pyenv-virtualenv
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
else
    echo "✉️ Pyenv and pyenv-virtualenv already installed."
fi

# Install python version if not installed
if ! pyenv versions | grep -q $PYTHON_VERSION
then
    echo "✉️ Installing python $PYTHON_VERSION with pyenv..."
    pyenv install $PYTHON_VERSION
else
    echo "✉️ Python $PYTHON_VERSION already installed."
fi

# Create virtualenv if not created
if ! pyenv virtualenvs | grep -q $VIRTUALENV_NAME
then
    echo "✉️ Creating virtualenv $VIRTUALENV_NAME..."
    pyenv virtualenv $PYTHON_VERSION $VIRTUALENV_NAME
    pyenv local $VIRTUALENV_NAME
else
    echo "✉️ Virtualenv $VIRTUALENV_NAME already created."
fi

# Activate virtualenv if not activated
if ! pyenv local | grep -q $VIRTUALENV_NAME
then
    echo "✉️ Activating virtualenv $VIRTUALENV_NAME..."
    pyenv local $VIRTUALENV_NAME
else
    echo "✉️ Virtualenv $VIRTUALENV_NAME already activated."
fi

# Install requirements
echo "✉️ Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev_requirements.txt
