#!/bin/bash

# Continuous Learning Pipeline Runner
# This script runs the model training pipeline on a schedule

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_PATH="$PROJECT_ROOT/.venv"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/continuous_learning_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting continuous learning pipeline"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Install dependencies if requirements.txt exists
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    log "Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt" >> "$LOG_FILE" 2>&1
fi

# Additional ML dependencies
log "Installing ML dependencies..."
pip install pandas numpy scikit-learn transformers torch >> "$LOG_FILE" 2>&1

# Change to project root
cd "$PROJECT_ROOT"

# Run the training pipeline
log "Running model training pipeline..."
python "$SCRIPT_DIR/model_training_pipeline.py" >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    log "Pipeline completed successfully"
    
    # Optional: Send success notification (uncomment and configure as needed)
    # curl -X POST -H 'Content-type: application/json' \
    #     --data '{"text":"RoleReady continuous learning pipeline completed successfully"}' \
    #     "$SLACK_WEBHOOK_URL"
    
else
    log "Pipeline failed with exit code $?"
    
    # Optional: Send failure notification (uncomment and configure as needed)
    # curl -X POST -H 'Content-type: application/json' \
    #     --data '{"text":"RoleReady continuous learning pipeline failed. Check logs."}' \
    #     "$SLACK_WEBHOOK_URL"
    
    exit 1
fi

log "Continuous learning pipeline finished"

# Clean up old log files (keep last 30 days)
find "$LOG_DIR" -name "continuous_learning_*.log" -mtime +30 -delete

log "Log cleanup completed"
