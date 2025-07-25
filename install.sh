
# --- Python Virtual Environment Setup ---
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
else
    print_info "Virtual environment '$VENV_DIR' already exists."
fi

# --- Activate Virtual Environment and Install Dependencies ---
print_info "Activating virtual environment and installing dependencies from requirements.txt..."
source "$VENV_DIR/bin/activate"

pip install -r requirements.txt

# --- Final Instructions ---
print_success "Setup complete!"
print_info "To activate the virtual environment in the future, run:
    source $VENV_DIR/bin/activate"
