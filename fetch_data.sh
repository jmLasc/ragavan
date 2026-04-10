#!/bin/sh
# fetch_data.sh
# Downloads the latest Scryfall Oracle Cards bulk data to data/scryfall_cards.json

set -e

DATA_DIR="$(dirname "$0")/data"
OUT_FILE="$DATA_DIR/scryfall_cards.json"

mkdir -p "$DATA_DIR"

echo "Fetching bulk data manifest..."
DOWNLOAD_URI=$(curl -sf \
  -H "User-Agent: mtg-rag-project/1.0" \
  -H "Accept: application/json" \
  "https://api.scryfall.com/bulk-data" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data['data']:
    if item['type'] == 'oracle_cards':
        print(item['download_uri'].encode('ascii', 'ignore').decode())
        break
" | tr -d '\r')

if [ -z "$DOWNLOAD_URI" ]; then
  echo "Error: could not find oracle_cards download URI." >&2
  exit 1
fi

echo "Downloading from: $DOWNLOAD_URI"
curl -L \
  -H "User-Agent: mtg-rag-project/1.0" \
  --progress-bar \
  -o "$OUT_FILE" \
  "$DOWNLOAD_URI"

echo "Saved to: $OUT_FILE"