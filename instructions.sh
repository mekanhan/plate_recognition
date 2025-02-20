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


# To run the training script, run the following commands:
yolo train model=models/yolo11m_best.pt data=datasets/license_plate_data/dataset.yaml epochs=20


# To view the logs in tensorboard, run the following commands:
# Convert the logs to tensorboard format:
python utils\convert_to_tensorboard.py
# Run the tensorboard server:
tensorboard --logdir runs/detect/train13/tb_logs/ 
# opens the tensorboard dashboard in the browser
http://localhost:6006/

