#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing ffmpeg..."
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
mkdir -p $HOME/.local/bin
cp ffmpeg-*-static/ffmpeg $HOME/.local/bin/
cp ffmpeg-*-static/ffprobe $HOME/.local/bin/
export PATH=$HOME/.local/bin:$PATH

echo "Installing python dependencies..."
pip install -r requirements.txt
