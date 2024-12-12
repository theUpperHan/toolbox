#!/bin/zsh

# Check if the directory argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

# Remove the directory
rm -rf "$1"

# Check if the removal was successful
if [ $? -eq 0 ]; then
    echo "Directory '$1' removed successfully."
else
    echo "Failed to remove directory '$1'."
fi