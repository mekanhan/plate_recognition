#!/usr/bin/env python
"""
Script to manage models between training and application
"""
import os
import sys
import shutil
import argparse
from pathlib import Path
import datetime

def copy_model_to_app(model_path, app_models_dir, model_name=None):
    """Copy a trained model to the application models directory"""
    if not os.path.exists(model_path):
        print(f"Error: Model file not found: {model_path}")
        return False
    
    # Create app models directory if it doesn't exist
    os.makedirs(app_models_dir, exist_ok=True)
    
    # Generate a default name if not provided
    if not model_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"yolo_license_plate_{timestamp}.pt"
    
    # Ensure .pt extension
    if not model_name.endswith('.pt'):
        model_name += '.pt'
    
    # Copy the model
    dest_path = os.path.join(app_models_dir, model_name)
    shutil.copy2(model_path, dest_path)
    print(f"Model copied to: {dest_path}")
    
    return True

def list_models(models_dir):
    """List all models in the directory"""
    if not os.path.exists(models_dir):
        print(f"Directory not found: {models_dir}")
        return
    
    models = list(Path(models_dir).glob('**/*.pt'))
    
    if not models:
        print(f"No models found in {models_dir}")
        return
    
    print(f"Found {len(models)} models:")
    for i, model in enumerate(models, 1):
        size_mb = os.path.getsize(model) / (1024 * 1024)
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(model))
        print(f"{i}. {model} ({size_mb:.1f} MB, modified: {mod_time})")

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the train directory (parent of scripts directory)
    train_dir = os.path.dirname(script_dir)
    # Set up app models directory path
    app_models_dir = os.path.join(train_dir, "..", "app", "models")
    
    parser = argparse.ArgumentParser(description="Manage YOLO models between training and application")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    list_parser.add_argument("--trained", action="store_true", help="List trained models")
    list_parser.add_argument("--app", action="store_true", help="List application models")
    list_parser.add_argument("--all", action="store_true", help="List all models")
    
    # Copy command
    copy_parser = subparsers.add_parser("copy", help="Copy model to application")
    copy_parser.add_argument("model_path", help="Path to the model file to copy")
    copy_parser.add_argument("--name", help="Name to give the model in the application directory")
    
    # Copy-best command (shortcut to copy the best model)
    copy_best_parser = subparsers.add_parser("copy-best", help="Copy the best trained model to application")
    copy_best_parser.add_argument("--name", help="Name to give the model in the application directory")
    
    args = parser.parse_args()
    
    # Default to list all if no command is provided
    if not args.command:
        args.command = "list"
        args.all = True
    
    if args.command == "list":
        if args.trained or args.all:
            trained_models_dir = os.path.join(train_dir, "models")
            print("\n=== Trained Models ===")
            list_models(trained_models_dir)
        
        if args.app or args.all:
            print("\n=== Application Models ===")
            list_models(app_models_dir)
    
    elif args.command == "copy":
        copy_model_to_app(args.model_path, app_models_dir, args.name)
    
    elif args.command == "copy-best":
        # Find the best model
        best_model_path = os.path.join(train_dir, "models", "trained", "license_plate_detector", "weights", "best.pt")
        if not os.path.exists(best_model_path):
            print("Error: Best model not found. Have you trained the model yet?")
            print(f"Expected path: {best_model_path}")
            return
        
        copy_model_to_app(best_model_path, app_models_dir, args.name)

if __name__ == "__main__":
    main()