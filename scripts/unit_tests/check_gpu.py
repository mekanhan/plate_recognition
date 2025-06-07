import torch
import sys

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"Memory allocated: {torch.cuda.memory_allocated(i) / 1024**2:.2f} MB")
        print(f"Memory reserved: {torch.cuda.memory_reserved(i) / 1024**2:.2f} MB")
else:
    print("CUDA is not available. Running on CPU only.")
    print("Please ensure you have:")
    print("1. NVIDIA GPU drivers installed")
    print("2. CUDA Toolkit installed (compatible with your PyTorch version)")
    print("3. Installed PyTorch with CUDA support")

# Test a simple tensor operation on GPU
if torch.cuda.is_available():
    print("\nRunning a simple GPU test...")
    # Create a tensor on GPU
    x = torch.rand(1000, 1000).cuda()
    y = torch.rand(1000, 1000).cuda()
    
    # Time a matrix multiplication
    import time
    start = time.time()
    z = torch.matmul(x, y)
    torch.cuda.synchronize()  # Wait for GPU operation to complete
    end = time.time()
    
    print(f"Matrix multiplication time: {(end - start) * 1000:.2f} ms")
    print("GPU test completed successfully!")