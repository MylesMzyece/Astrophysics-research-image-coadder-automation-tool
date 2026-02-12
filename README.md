# SourceExtractor Automation Scripts

Automated scripts for batch processing astronomical images with SourceExtractor.

## Files Included

1. **run_sextractor.py** - Python version (recommended)
2. **run_sextractor.sh** - Bash version
3. **default.sex** - SourceExtractor configuration file
4. **default.param** - Output parameter definitions

## Prerequisites

- SourceExtractor installed (`sex` command available)
- Python 3.x (for Python script) OR Bash shell (for Bash script)

## Setup

1. Place all files in your working directory
2. Place your FITS images in the same directory
3. Make the scripts executable:
   ```bash
   chmod +x run_sextractor.py
   chmod +x run_sextractor.sh
   ```

## Usage

### Option 1: Python Script (Recommended)

```bash
./run_sextractor.py
```

Or:
```bash
python3 run_sextractor.py
```

### Option 2: Bash Script

```bash
./run_sextractor.sh
```

Or:
```bash
bash run_sextractor.sh
```

## What the Scripts Do

1. **Find all FITS images** in the current directory (*.fits, *.fit, *.FITS, *.FIT)
2. **Process each image** with SourceExtractor using your configuration
3. **Save outputs** to the `catalogs/` directory:
   - `imagename.cat` - Source catalog
   - `imagename_check.fits` - Background-subtracted check image

## Output Catalog Contents

Based on your `default.param` file, each catalog will contain:

- **NUMBER** - Object identifier
- **ALPHAPEAK_SKY** - Right ascension of brightest pixel (degrees)
- **DELTAPEAK_SKY** - Declination of brightest pixel (degrees)
- **X_IMAGE** - X position in image (pixels)
- **Y_IMAGE** - Y position in image (pixels)

## Weight Image Detection

The scripts automatically detect and use weight/uncertainty images when available. **Two naming patterns are supported:**

### Pattern 1: Suffix Pattern
Append uncertainty/weight suffixes to the base image name:
```
image.fits               → Science image
image_unc.fits           → Uncertainty (stddev) image → Uses MAP_RMS
image_stddev.fits        → Alternative uncertainty name
image_weight.fits        → Weight/invvar image → Uses MAP_WEIGHT
```

### Pattern 2: Component Replacement Pattern
Replace the science component with uncertainty/weight component:
```
image-int.fits           → Science image (-int component)
image-unc.fits           → Replace -int with -unc → Uses MAP_RMS
image-weight.fits        → Replace -int with -weight → Uses MAP_WEIGHT
image-sci.fits           → Science image (-sci component)
image-rms.fits           → Replace -sci with -rms → Uses MAP_RMS
```

**Supported suffixes:** `_unc`, `_stddev`, `_stdev`, `_rms`, `_uncert`, `_sigma`, `_weight`, `_wht`, `_wt`, `_ivar`

**Supported component replacements:** `-int` and `-sci` → replaced with uncertainty or weight names

If a matching weight image is found, it will be automatically passed to SourceExtractor with the appropriate weight type:
- **MAP_RMS**: For uncertainty/stddev images (pixels weighted inversely by uncertainty)
- **MAP_WEIGHT**: For weight/inverse-variance images (higher = more trustworthy)

## Customization

### Change Input Directory

Edit the script to process images from a different location:

**Python:**
```python
images = find_images("/path/to/images")
```

**Bash:**
```bash
cd /path/to/images
./run_sextractor.sh
```

### Modify Configuration

Edit `default.sex` to change detection parameters:
- `DETECT_THRESH` - Detection threshold
- `DETECT_MINAREA` - Minimum detection area
- `PHOT_APERTURES` - Aperture size for photometry
- `MAG_ZEROPOINT` - Photometric zero point

### Add More Output Parameters

Edit `default.param` and uncomment any parameters you need:
```
FLUX_AUTO                # Kron flux
MAG_AUTO                 # Kron magnitude
FWHM_IMAGE              # FWHM in pixels
CLASS_STAR              # Star/galaxy classifier
```

## Troubleshooting

### "SourceExtractor not found"
Install SourceExtractor:
```bash
# Ubuntu/Debian
sudo apt-get install sextractor

# macOS (using Homebrew)
brew install sextractor
```

### "No FITS images found"
- Check that your images have .fits or .fit extension
- Verify you're in the correct directory
- Check file permissions

### Processing Errors
- Verify your FITS files are valid
- Check the SourceExtractor log output
- Ensure `gauss_5.0_9x9.conv` filter file exists (or modify `FILTER_NAME` in config)

## Example Workflow

```bash
# 1. Setup
mkdir my_analysis
cd my_analysis
cp /path/to/default.sex .
cp /path/to/default.param .
cp /path/to/run_sextractor.py .

# 2. Copy your images
cp /path/to/images/*.fits .

# 3. Run the script
./run_sextractor.py

# 4. Check results
ls catalogs/
head catalogs/image1.cat
```

## Advanced: Processing Specific Images

To process only certain images, modify the Python script:

```python
# Process only images matching a pattern
images = glob.glob("ngc*.fits")

# Or specify images manually
images = ["image1.fits", "image2.fits", "image3.fits"]
```

## Support

For SourceExtractor documentation:
- Official manual: https://sextractor.readthedocs.io/
- Parameter reference: Run `sex -dd` to see all available parameters
