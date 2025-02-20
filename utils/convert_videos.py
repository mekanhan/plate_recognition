import os
import subprocess

# Get the project root directory (one level up from the script location)
root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
print("root_folder:", root_folder)

# Define input and output folders relative to the project root
input_folder = os.path.join(root_folder, 'input_videos')  # Input folder in the root directory
output_folder = os.path.join(root_folder, 'input_videos', 'converted_videos2')
output_format = 'mp4'  # Change to desired format, e.g., mp4, mkv, avi

# Create output directory if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Supported video file extensions
video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.ts', '.m4v']

# Function to convert video
def convert_video(input_file, output_file):
    try:
        # FFmpeg command for conversion without re-encoding
        command = [
            'ffmpeg', '-i', input_file,
            '-c', 'copy',  # Copy codec to avoid re-encoding
            output_file
        ]
        print(f"Converting: {input_file} -> {output_file}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {input_file}: {e}")

# Iterate over all files in the input folder
if os.path.exists(input_folder):
    for file_name in os.listdir(input_folder):
        input_file = os.path.join(input_folder, file_name)
        # Check if it's a video file
        if os.path.isfile(input_file) and any(file_name.lower().endswith(ext) for ext in video_extensions):
            # Construct output file path
            output_file = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}.{output_format}")
            # Convert the video
            convert_video(input_file, output_file)
else:
    print(f"Error: Input folder does not exist: {input_folder}")

print("All videos converted successfully.")
