#!/bin/bash

# Ensure the script itself is executable (though Streamlit Cloud should handle this for setup.sh)
# chmod +x $0

echo "Running setup.sh: Downloading spaCy model..."
python -m spacy download en_core_web_sm

echo "setup.sh finished."