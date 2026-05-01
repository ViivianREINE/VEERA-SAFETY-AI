#!/bin/bash
# AI-Powered Predictive Crowd Panic Detection
# Dataset Download Script

echo "Starting dataset downloads..."

# Make sure kaggle CLI is installed and configured
# pip install kaggle
# Ensure ~/.kaggle/kaggle.json exists

# Create data directory
mkdir -p data/video
mkdir -p data/audio

# VIDEO DATASETS
echo "Downloading UCF-Crime Dataset..."
kaggle datasets download -d odins0n/ucf-crime-dataset -p data/video --unzip

echo "Downloading RWF-2000 Dataset..."
kaggle datasets download -d vulamnguyen/rwf2000 -p data/video --unzip

echo "Downloading Hockey Fight Dataset..."
kaggle datasets download -d yassershrief/hockey-fight-vidoes -p data/video --unzip

echo "Downloading Real Life Violence Dataset..."
kaggle datasets download -d mohamedmustafa/real-life-violence-situations-dataset -p data/video --unzip

echo "Downloading Combined Violence Dataset..."
kaggle datasets download -d yash07yadav/project-data -p data/video --unzip

# AUDIO DATASETS
echo "Downloading UrbanSound8K Dataset..."
kaggle datasets download -d chrisfilo/urbansound8k -p data/audio --unzip

echo "Downloading ESC-50 Dataset..."
curl -L -o data/audio/esc50.zip https://github.com/karolpiczak/ESC-50/archive/master.zip
unzip data/audio/esc50.zip -d data/audio/
rm data/audio/esc50.zip

echo "All datasets downloaded and extracted successfully."
