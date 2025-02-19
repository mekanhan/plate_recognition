# Deactivate the virtual environment if it's active
deactivate

# Remove the existing virtual environment
rm -rf .venv

# Create a new virtual environment
python -m venv .venv

# Activate the new virtual environment
source .venv/Scripts/activate

# Update pip and setuptools
python -m pip install --upgrade pip
pip install --upgrade setuptools

# Install all dependencies
pip install -r requirements.txt

# Ensure the environment variables are loaded
export $(grep -v '^#' .env | xargs)

# Run the main script
python src/main.py

# Manually update requirements.txt
pip freeze >> requirements.txt

# Rebuild the app
pyinstaller --onefile --windowed --name TalkieBud --icon=src/images/icon.ico --paths=src --add-data "TalkieBud_Portable/dependencies/ffmpeg.exe;dependencies" src/components/gui.py


# Windows setup
# Install OpenALPR: https://github.com/openalpr/openalpr/releases
# Add OpenALPR path to the environment system variables: "C:\OpenALPR\"