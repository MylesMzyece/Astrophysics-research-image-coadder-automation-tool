#!/usr/bin/env python3
"""
Automated SourceExtractor script
Processes all FITS images in a directory using SourceExtractor
"""

import os
import subprocess
import glob
import sys
from pathlib import Path

# Configuration
CONFIG_FILE = "default.sex"
PARAM_FILE = "default.param"
IMAGE_EXTENSIONS = ["*.fits", "*.fit", "*.FITS", "*.FIT"]

# Weight image detection
# stddev/uncertainty images should use MAP_RMS (pixel RMS map)
# weight/invvar images should use MAP_WEIGHT (weight map)
WEIGHT_SUFFIXES = {
    "MAP_RMS": ["_stddev", "_stdev", "_rms", "_unc", "_uncert", "_sigma"],
    "MAP_WEIGHT": ["_weight", "_wht", "_wt", "_ivar"]
}

def check_sextractor():
    """Check if SourceExtractor is installed"""
    try:
        subprocess.run(["sex", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: SourceExtractor (sex) not found!")
        print("Please install SExtractor first.")
        return False

def find_images(directory="."):
    """Find all FITS images in the directory"""
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(glob.glob(os.path.join(directory, ext)))
    return sorted(images)

def find_weight_image(image_path):
    """Find a matching weight image for a given FITS image.
    
    Handles two naming patterns:
    1. Suffix pattern: image_unc.fits, image_stddev.fits, etc.
    2. Component replacement: image-int.fits -> image-unc.fits, etc.
    """
    image_dir = os.path.dirname(image_path) or "."
    stem = Path(image_path).stem
    
    # Pattern 1: Try suffix candidates first (stddev/uncertainty)
    for suffix in WEIGHT_SUFFIXES["MAP_RMS"]:
        for file_ext in (".fits", ".fit", ".FITS", ".FIT"):
            candidate = os.path.join(image_dir, f"{stem}{suffix}{file_ext}")
            if os.path.exists(candidate):
                return "MAP_RMS", candidate

    # Pattern 1: Try suffix candidates for weight maps
    for suffix in WEIGHT_SUFFIXES["MAP_WEIGHT"]:
        for file_ext in (".fits", ".fit", ".FITS", ".FIT"):
            candidate = os.path.join(image_dir, f"{stem}{suffix}{file_ext}")
            if os.path.exists(candidate):
                return "MAP_WEIGHT", candidate

    # Pattern 2: Try component replacement (e.g., -int -> -unc, -weight)
    uncertainty_names = ["unc", "stddev", "stdev", "rms", "uncert", "sigma"]
    weight_names = ["weight", "wht", "wt", "ivar"]
    components_to_replace = ["-int", "-sci"]  # Common components to replace
    
    # Try replacements for uncertainty/stddev images
    for component in components_to_replace:
        if component in stem:
            for unc_name in uncertainty_names:
                replacement_stem = stem.replace(component, f"-{unc_name}")
                for file_ext in (".fits", ".fit", ".FITS", ".FIT"):
                    candidate = os.path.join(image_dir, f"{replacement_stem}{file_ext}")
                    if os.path.exists(candidate):
                        return "MAP_RMS", candidate
    
    # Try replacements for weight images
    for component in components_to_replace:
        if component in stem:
            for weight_name in weight_names:
                replacement_stem = stem.replace(component, f"-{weight_name}")
                for file_ext in (".fits", ".fit", ".FITS", ".FIT"):
                    candidate = os.path.join(image_dir, f"{replacement_stem}{file_ext}")
                    if os.path.exists(candidate):
                        return "MAP_WEIGHT", candidate

    return None, None


def run_sextractor(image_path, config_file, output_dir="catalogs"):
    """Run SourceExtractor on a single image"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output catalog name
    image_name = Path(image_path).stem
    catalog_name = os.path.join(output_dir, f"{image_name}.cat")
    check_image_name = os.path.join(output_dir, f"{image_name}_check.fits")
    
    # Build SourceExtractor command
    cmd = [
        "sex",
        image_path,
        "-c", config_file,
        "-CATALOG_NAME", catalog_name,
        "-CHECKIMAGE_NAME", check_image_name
    ]

    weight_type, weight_image = find_weight_image(image_path)
    if weight_type and weight_image:
        cmd.extend(["-WEIGHT_TYPE", weight_type, "-WEIGHT_IMAGE", weight_image])
    
    print(f"Processing: {image_path}")
    print(f"  → Catalog: {catalog_name}")
    if weight_type and weight_image:
        print(f"  → Weight: {weight_image} ({weight_type})")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ ERROR processing {image_path}")
        print(f"    {e.stderr}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Automated SourceExtractor Processing")
    print("=" * 60)
    
    # Check if SourceExtractor is available
    if not check_sextractor():
        sys.exit(1)
    
    # Check if config files exist
    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found!")
        sys.exit(1)
    
    if not os.path.exists(PARAM_FILE):
        print(f"ERROR: Parameter file '{PARAM_FILE}' not found!")
        sys.exit(1)
    
    # Find all images
    print(f"\nSearching for images...")
    images = find_images()
    
    if not images:
        print("No FITS images found in current directory!")
        sys.exit(1)
    
    print(f"Found {len(images)} image(s):")
    for img in images:
        print(f"  - {img}")
    
    # Process each image
    print(f"\nProcessing images...")
    print("-" * 60)
    
    success_count = 0
    for image in images:
        if run_sextractor(image, CONFIG_FILE):
            success_count += 1
        print()
    
    # Summary
    print("=" * 60)
    print(f"SUMMARY: {success_count}/{len(images)} images processed successfully")
    print("=" * 60)
    print("\nCatalogs saved in './catalogs/' directory")

if __name__ == "__main__":
    main()
