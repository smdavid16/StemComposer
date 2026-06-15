#!/bin/bash
set -e

echo "Setting up NVIDIA Container Toolkit repo..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --yes --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

echo "Updating apt packages..."
apt-get update

echo "Installing nvidia-container-toolkit..."
apt-get install -y nvidia-container-toolkit

echo "Configuring Docker to use nvidia runtime..."
nvidia-ctk runtime configure --runtime=docker

echo "Restarting Docker daemon..."
service docker restart

echo "NVIDIA Container Toolkit installation complete!"
