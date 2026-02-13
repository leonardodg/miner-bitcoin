#!/bin/bash
# Get Last 10 Blocks from Bitcoin Core and display their details

CURRENT_HEIGHT=$(bitcoin-cli getblockcount)

echo "┌─────────────────────────────────────────────────────────────────────┐"
echo "│                            LAST 10 BLOCKS                           │"
echo "└─────────────────────────────────────────────────────────────────────┘"

for i in {0..9}; do
    HEIGHT=$((CURRENT_HEIGHT - i))
    HASH=$(bitcoin-cli getblockhash $HEIGHT)
    BLOCK=$(bitcoin-cli getblock $HASH)
    
    TIME=$(echo $BLOCK | jq -r '.time')
    SIZE=$(echo $BLOCK | jq -r '.size')
    TX_COUNT=$(echo $BLOCK | jq -r '.nTx')
    BLOCO_CLEAN=$(echo $BLOCK | jq 'del(.tx)')
    
    echo ""
    echo "============================= Block #$HEIGHT ========================="
    echo "  Hash: ${HASH}"
    echo "  Transactions: $TX_COUNT"
    echo "  Size: $SIZE bytes"
    echo "  Timestamp: $(date -d @$TIME)"
    echo ""
    echo ">> JSON:"
    echo "  $BLOCO_CLEAN" | jq .
    echo "======================================================================"
done