# IconSwitch

A automated shell script for switching folder icon in MacOS Finder.

***Required packages: folderify, imagemagick, fileicon**

```shell
# Install all
cd path/to/this/folder
brew install $(<packages.txt)

# Install separately
brew install folderify
brew install imagemagick
brew install fileicon
```

## Usage

```shell
./setfoldericon.sh IMAGE_PATH "HEXCODE" TINT_VALUE 
```
