#!/bin/bash

# CONFIG
DATA_DIR="./data"
PASSWORD_FILE="./password.txt"
CREATED_FILE="$DATA_DIR/keystore/created"
ACCOUNT_ADDRESS=""

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Initialize the chain if not already initialized
if [ ! -f "$DATA_DIR/geth/chaindata/LOG" ]; then
    echo "Initializing private chain..."
    geth --datadir "$DATA_DIR" init "$(pwd)/genesis.json"
fi

# Create a new account if none exists
if [ ! -f "$CREATED_FILE" ]; then
    echo "Creating new account..."
    ACCOUNT_ADDRESS=$(geth --datadir "$DATA_DIR" account new --password "$PASSWORD_FILE" | grep -oP '(?<=\{).*(?=\})')
    echo "$ACCOUNT_ADDRESS" > "$CREATED_FILE"
else
    ACCOUNT_ADDRESS=$(cat "$CREATED_FILE")
fi

echo "Using account: 0x$ACCOUNT_ADDRESS"

# Start the node with mining and unlocked account
nohup geth --datadir "$DATA_DIR" \
  --networkid 1337 \
  --http \
  --http.port 8545 \
  --http.api "eth,net,web3,personal,miner" \
  --allow-insecure-unlock \
  --unlock "0x$ACCOUNT_ADDRESS" \
  --password "$PASSWORD_FILE" \
  --mine \
  --miner.etherbase="0x$ACCOUNT_ADDRESS" \
  --nodiscover \
  > geth.log 2>&1 &


echo "Node started in background. Check logs with: tail -f geth.log"
