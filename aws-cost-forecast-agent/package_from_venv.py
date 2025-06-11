#!/usr/bin/env python3
import os
import zipfile
import shutil
import subprocess
from pathlib import Path

def create_lambda_package():
    current_dir = Path.cwd()
    project_dir = current_dir.parent
    packaging_dir = current_dir / "packaging"
    
    # Create packaging directory if it doesn't exist
    packaging_dir.mkdir(exist_ok=True)
    
    app_deployment_zip = packaging_dir / "app.zip"
    dependencies_deployment_zip = packaging_dir / "dependencies.zip"
    
    # Clean up previous builds
    if app_deployment_zip.exists():
        os.remove(app_deployment_zip)
    if dependencies_deployment_zip.exists():
        os.remove(dependencies_deployment_zip)
    
    # Path to the virtual environment site-packages
    venv_site_packages = project_dir / ".venv/lib/python3.11/site-packages"
    
    if not venv_site_packages.exists():
        print(f"Error: Virtual environment site-packages not found at {venv_site_packages}")
        return
    
    print(f"Using virtual environment site-packages from: {venv_site_packages}")
    
    # Create dependencies zip directly from the virtual environment
    print("Creating dependencies zip from virtual environment...")
    with zipfile.ZipFile(dependencies_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(venv_site_packages):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = Path("python") / os.path.relpath(file_path, venv_site_packages)
                zipf.write(file_path, str(arcname))
    
    # Create app zip
    print("Creating app zip...")
    with zipfile.ZipFile(app_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Only include the necessary files
        for file in ["lambda_handler.py"]:
            file_path = current_dir / file
            if file_path.exists():
                zipf.write(file_path, file)
    
    print(f"Lambda package created:")
    print(f"- App code: {app_deployment_zip}")
    print(f"- Dependencies: {dependencies_deployment_zip}")
    
    # Upload to S3
    s3_bucket = "finops-deployment-packages-062025"
    print(f"Uploading packages to S3 bucket: {s3_bucket}...")
    
    subprocess.check_call([
        "aws", "s3", "cp", 
        str(app_deployment_zip), 
        f"s3://{s3_bucket}/app.zip"
    ])
    subprocess.check_call([
        "aws", "s3", "cp", 
        str(dependencies_deployment_zip), 
        f"s3://{s3_bucket}/dependencies.zip"
    ])
    
    print(f"Packages uploaded to S3 bucket: {s3_bucket}")

if __name__ == "__main__":
    create_lambda_package()
