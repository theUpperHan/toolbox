#!/bin/zsh

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory> <icns_file>"
    exit 1
fi

# Assign arguments to variables
directory=$1
icns_file=$2

# Check if the directory exists
if [ ! -d "$directory" ]; then
    echo "Error: Directory $directory does not exist."
    exit 1
fi

# Check if the icns file exists
if [ ! -f "$icns_file" ]; then
    echo "Error: ICNS file $icns_file does not exist."
    exit 1
fi

# Set the custom icon for the directory
icon_set_command="fileicon set \"$directory\" \"$icns_file\""

# Execute the command
eval $icon_set_command

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Successfully set the icon for $directory."
else
    echo "Failed to set the icon for $directory."
    exit 1
fi