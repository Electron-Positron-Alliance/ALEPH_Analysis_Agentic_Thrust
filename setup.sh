#!/bin/bash

# Initialize submodules
git submodule update --init --remote --merge

# Force submodules off detached HEAD and onto main/master
git submodule foreach --recursive '
    target=$(git show-ref --verify --quiet refs/heads/main && echo main || echo master)
    git checkout $target
    git branch -u origin/$target $target
    git pull origin $target
'

# Create session alias for updates
alias update-skills='git submodule update --remote --merge'

echo "Setup complete. Submodules are on their tracking branches."
