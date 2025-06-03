import os
import glob
from test_detection import test_upload_detection

# Test with all jpg images in a directory
def test_all_images_in_directory(directory):
    """Test all jpg images in the specified directory"""
    image_paths = glob.glob(os.path.join(directory, "*.jpg"))
    
    if not image_paths:
        print(f"No jpg images found in {directory}")
        return
        
    print(f"Found {len(image_paths)} images to test")
    
    for i, image_path in enumerate(image_paths, 1):
        print(f"\n\n--- Testing image {i}/{len(image_paths)}: {image_path} ---")
        test_upload_detection(image_path)
        
        if i < len(image_paths):
            input("Press Enter to continue to the next image...")

if __name__ == "__main__":
    image_dir = input("Enter directory containing test images: ")
    if not image_dir:
        image_dir = "images"  # Default directory
        
    if not os.path.isdir(image_dir):
        print(f"Error: {image_dir} is not a valid directory")
    else:
        test_all_images_in_directory(image_dir)