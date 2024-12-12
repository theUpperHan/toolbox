#!/bin/zsh
imgpath="$1"
color="$2"
tintval="$3"
if [ -z "$imgpath" ]; then
    echo "No argument provided"
    exit 1
fi

if [ ! -f "$imgpath" ]; then
    echo "The provided path is not a valid file"
    exit 1
fi

filetype=$(file --mime-type -b "$imgpath")
if [[ $filetype != image/* ]]; then
    echo "The provided file is not an image"
    exit 1
fi

if ! command -v folderify &> /dev/null; then
    echo "folderify is not installed. Install by: brew install folderify"
    exit 1
fi

if ! command -v magick &> /dev/null; then
    echo "imaegmagick is not installed. Install by: brew install imagemagick"
    exit 1
fi

if [ -z "$color" ]; then
    color="green"
fi

if [ -z "$tintval" ]; then
    tintval="100"
fi


folderify "$imgpath"

output_dir=$(dirname "$imgpath")
filename=$(basename "$imgpath")
filename_without_ext="${filename%.*}"
icns_file="${output_dir}/${filename_without_ext}.icns"
icnsset_dir="${output_dir}/${filename_without_ext}.iconset"

if [ -f "$icns_file" ]; then
    echo "ICNS file created at $icns_file"
else
    echo "Failed to create ICNS file"
    exit 1
fi

if [ -d "$icnsset_dir" ]; then
    echo "Iconset folder created at $icnsset_dir"
else
    echo "Failed to create Iconset folder"
    exit 1
fi

for pngfile in "$icnsset_dir"/*.png; do
    magick "$pngfile" -fill $color -tint $tintval "$pngfile"
done

iconutil -c icns -o "${output_dir}/${filename_without_ext}_tinted.icns" "$icnsset_dir"
if [ -f "${output_dir}/${filename_without_ext}_tinted.icns" ]; then
    echo "Output ICNS file created at ${output_dir}/${filename_without_ext}_tinted.icns"
else
    echo "Failed to create output ICNS file"
    exit 1
fi

/Users/yunhanhuang/Documents/Tool\ Script/IconSwitch/removeicnset.sh "$icnsset_dir"

read -p "Please enter the directory where you want to move the tinted ICNS file (Enter q to quit): " target_dir

if [ -z "$target_dir" ]; then
    echo "No directory provided. Exiting."
    exit 1
fi

if [ ! -d "$target_dir" ]; then
    echo "The provided path is not a valid directory. Exiting."
    exit 1
fi

icon_set_command="fileicon set \"$target_dir\" \"${output_dir}/${filename_without_ext}_tinted.icns\""