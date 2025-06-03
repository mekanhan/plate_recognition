# License Plate Recognition Framework

## Overview
This framework is designed to perform real-time license plate recognition using live streams from a camera. It acts as a microservice, identifying vehicle details and controlling access systems like security gates. The framework integrates with an external platform featuring an online dashboard to provide enhanced features and analytics.

## Features
- **Real-Time License Plate Recognition**: Utilizes YOLO models for detecting and reading license plates.
- **Integration with Android Devices**: Supports live streaming from Android cameras using DroidCam.
- **Security Access Control**: Connects to a database to verify license plates and triggers security gate operations.
- **Live Video Streaming**: Streams processed video with recognition results to an external platform for additional processing and visualization.
- **Edge Device Compatibility**: Optimized to run on devices like the NVIDIA Jetson Nano or Raspberry Pi 5 with a connected camera.

## System Requirements
- **Python** (version corresponds to requirements.txt)
- **CUDA** (optional, for GPU support)
- **ADB & DroidCam**: For connecting and streaming from Android devices.
- **Hardware**: NVIDIA Jetson Nano, Raspberry Pi 5, or similar with camera input capability.

## Installation

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Set Up Environment**
   
   Follow the instructions in `instructions.sh` to set up the Python virtual environment and install dependencies.

3. **Configuration**
   
   - Update `config.yaml` with specific settings, such as API keys and model configurations.
   - Ensure that the device IP and other network settings are correctly set in related scripts.

## Usage

1. **Connect Camera:** 
   
   Ensure your camera is connected and accessible, whether through USB or a networked device like an Android phone through DroidCam.

2. **Start the Recognition Service:**

   ```bash
   python scripts/adb_license_plate_recognition.py
   ```

3. **Integration with External Platform:**

   Configure and connect the service to your external platform for database queries and video stream integration.

## Development and Deployment

- Designed to be deployed on edge devices like Jetson Nano and Raspberry Pi for on-site processing.
- Supports streaming recognized data to centralized systems for broader application features.

## License
[MIT License](LICENSE)

## Contributions
Contributions, issues, and feature requests are welcome. Feel free to check [issues](https://github.com/your-repo/issues) and [pull requests](https://github.com/your-repo/pulls).

## Contact
For more information, contact [Your Name/Your Organization] at [email@example.com].


## Running the Script
### For USB cameras
python scripts/lpr_live.py usb --id 0

### For IP cameras (like Android phone)
python scripts/lpr_live.py ip --ip 192.168.1.100 --port 8080

### For CSI cameras (Jetson/Raspberry Pi)
python scripts/lpr_live.py csi

## Docker Compose
To run the service using Docker Compose:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.
