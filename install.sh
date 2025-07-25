#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install git
echo "Installing git..."
sudo apt-get install -y git

# Install python3-pip
echo "Installing python3-pip..."
sudo apt-get install -y python3-pip
``
# Add Ethereum PPA
echo "Adding Ethereum PPA..."
sudo add-apt-repository -y ppa:ethereum/ethereum

# Update package lists again after adding new PPA
echo "Updating package lists again..."
sudo apt-get update

# Install Ethereum (geth)
echo "Installing Ethereum (geth)..."
sudo apt-get install -y ethereum

echo "All dependencies installed successfully!"
