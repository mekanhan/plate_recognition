"""
Script to install PyTorch with CUDA support for use with an NVIDIA GPU.
"""
import os
import subprocess
import sys

def run_command(command):
    """Run a command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
    return result.returncode == 0

def main():
    # Uninstall existing PyTorch packages
    print("=== Uninstalling existing PyTorch packages ===")
    packages_to_uninstall = ["torch", "torchvision", "torchaudio"]
    for package in packages_to_uninstall:
        run_command(f"{sys.executable} -m pip uninstall -y {package}")

    # Install PyTorch with CUDA support
    print("\n=== Installing PyTorch with CUDA support ===")
    
    # PyTorch 2.5.1 with CUDA 12.1
    cuda_command = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    
    success = run_command(cuda_command)
    
    if success:
        print("\n=== Installation completed successfully ===")
        print("Now verifying CUDA availability...")
        
        # Verify CUDA is available
        verify_script = """
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("CUDA is still not available. Please check your NVIDIA drivers.")
"""
        
        # Write the verification script to a temporary file
        with open("verify_cuda.py", "w") as f:
            f.write(verify_script)
        
        # Run the verification script
        run_command(f"{sys.executable} verify_cuda.py")
        
        # Clean up
        if os.path.exists("verify_cuda.py"):
            os.remove("verify_cuda.py")
    else:
        print("\n=== Installation failed ===")
        print("Please try installing manually with:")
        print(cuda_command)

if __name__ == "__main__":
    main()