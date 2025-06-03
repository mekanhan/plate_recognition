import requests
import os
import json
import sys

# Base URL - Make sure this matches your server
BASE_URL = 'http://localhost:8000'  # Update with your actual server URL

def test_upload_detection(image_path):
    """Test the image upload detection endpoint"""
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found")
        return
        
    try:
        url = f"{BASE_URL}/detection/detect/upload"
        print(f"Sending request to: {url}")
        print(f"Uploading file: {image_path}")
        
        with open(image_path, 'rb') as img:
            files = {'file': (os.path.basename(image_path), img, 'image/jpeg')}
            print("Sending POST request...")
            response = requests.post(url, files=files)
            
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print("Response content (parsed JSON):")
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError:
            print("Response content (raw):")
            print(response.text)

        if response.status_code == 200:
            print("\nSuccess! Detection results:")
            # Check if detection is nested in the response
            if 'detection' in result:
                detection = result['detection']
                print(f"Plate Text: {detection.get('plate_text', 'None')}")
                print(f"Confidence: {detection.get('confidence', 0) * 100:.2f}%")
                print(f"OCR Confidence: {detection.get('ocr_confidence', 0) * 100:.2f}%")
                print(f"Detection Confidence: {detection.get('detection_confidence', 0) * 100:.2f}%")
                print(f"Raw Text: {detection.get('raw_text', 'None')}")
                if detection.get('state'):
                    print(f"State: {detection.get('state')}")
                print(f"Bounding Box: {detection.get('box', 'None')}")
            else:
                # Fall back to looking at the root level
                print(f"Plate Text: {result.get('plate_text', 'None')}")
                print(f"Confidence: {result.get('confidence', 0) * 100:.2f}%")
                if result.get('state'):
                    print(f"State: {result.get('state')}")
        else:
            print(f"\nError: Status code {response.status_code}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

def test_detection_status():
    """Test the detection status endpoint"""
    try:
        url = f"{BASE_URL}/detection/status"
        response = requests.get(url)

        if response.status_code == 200:
            print("Success! Status information:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    # Example usage
    print("License Plate Detection Test Script")
    print("==================================")
    
    # Test the upload endpoint with a sample image
    sample_image = input("Enter path to test image: ")
    if sample_image:
        print("\nTesting Upload Detection:")
        test_upload_detection(sample_image)
    
    # Test the status endpoint
    print("\nTesting Detection Status:")
    test_detection_status()