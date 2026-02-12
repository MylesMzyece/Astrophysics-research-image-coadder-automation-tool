#!/bin/bash
################################################################################
# Automated SourceExtractor Batch Processing Script
# Processes all FITS images in the current directory
################################################################################

# Configuration
CONFIG_FILE="default.sex"
PARAM_FILE="default.param"
OUTPUT_DIR="catalogs"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Automated SourceExtractor Processing"
echo "============================================================"

# Ensure non-matching globs expand to nothing (avoid literal patterns)
shopt -s nullglob

# Check if SourceExtractor is installed
if ! command -v sex &> /dev/null; then
    echo -e "${RED}ERROR: SourceExtractor (sex) not found!${NC}"
    echo "Please install SExtractor first."
    exit 1
fi

# Check if config files exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Configuration file '$CONFIG_FILE' not found!${NC}"
    exit 1
fi

if [ ! -f "$PARAM_FILE" ]; then
    echo -e "${RED}ERROR: Parameter file '$PARAM_FILE' not found!${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Find all FITS files
echo -e "\nSearching for FITS images..."
IMAGES=(*.fits *.fit *.FITS *.FIT)

# Remove non-existent patterns
VALID_IMAGES=()
for img in "${IMAGES[@]}"; do
    if [ -f "$img" ]; then
        VALID_IMAGES+=("$img")
    fi
done

if [ ${#VALID_IMAGES[@]} -eq 0 ]; then
    echo -e "${RED}No FITS images found in current directory!${NC}"
    exit 1
fi

echo -e "Found ${YELLOW}${#VALID_IMAGES[@]}${NC} image(s):"
for img in "${VALID_IMAGES[@]}"; do
    echo "  - $img"
done

# Process each image
echo -e "\nProcessing images..."
echo "------------------------------------------------------------"

SUCCESS_COUNT=0
TOTAL_COUNT=${#VALID_IMAGES[@]}

for image in "${VALID_IMAGES[@]}"; do
    # Get base name without extension
    basename="${image%.*}"
    
    # Define output filenames
    catalog="${OUTPUT_DIR}/${basename}.cat"
    checkimg="${OUTPUT_DIR}/${basename}_check.fits"
    
    echo "Processing: $image"
    echo "  → Catalog: $catalog"

    # Detect matching weight image (stddev/uncertainty or weight map)
    weight_type=""
    weight_image=""
    base_no_ext="${basename}"

    # Pattern 1: Try suffix approach (image_unc.fits, image_stddev.fits, etc.)
    for suffix in _stddev _stdev _rms _unc _uncert _sigma; do
        for ext in .fits .fit .FITS .FIT; do
            candidate="${base_no_ext}${suffix}${ext}"
            if [ -f "$candidate" ]; then
                weight_type="MAP_RMS"
                weight_image="$candidate"
                break 2
            fi
        done
    done

    if [ -z "$weight_image" ]; then
        for suffix in _weight _wht _wt _ivar; do
            for ext in .fits .fit .FITS .FIT; do
                candidate="${base_no_ext}${suffix}${ext}"
                if [ -f "$candidate" ]; then
                    weight_type="MAP_WEIGHT"
                    weight_image="$candidate"
                    break 2
                fi
            done
        done
    fi

    # Pattern 2: Try component replacement (image-int.fits -> image-unc.fits, etc.)
    if [ -z "$weight_image" ]; then
        for component in "-int" "-sci"; do
            if [[ "$base_no_ext" == *"$component"* ]]; then
                # Try uncertainty/stddev names
                for unc_name in unc stddev stdev rms uncert sigma; do
                    replacement_stem="${base_no_ext/$component/-$unc_name}"
                    for ext in .fits .fit .FITS .FIT; do
                        candidate="${replacement_stem}${ext}"
                        if [ -f "$candidate" ]; then
                            weight_type="MAP_RMS"
                            weight_image="$candidate"
                            break 3
                        fi
                    done
                done
            fi
        done
    fi

    # Pattern 2: Try weight map replacements if uncertainty not found
    if [ -z "$weight_image" ]; then
        for component in "-int" "-sci"; do
            if [[ "$base_no_ext" == *"$component"* ]]; then
                # Try weight map names
                for weight_name in weight wht wt ivar; do
                    replacement_stem="${base_no_ext/$component/-$weight_name}"
                    for ext in .fits .fit .FITS .FIT; do
                        candidate="${replacement_stem}${ext}"
                        if [ -f "$candidate" ]; then
                            weight_type="MAP_WEIGHT"
                            weight_image="$candidate"
                            break 3
                        fi
                    done
                done
            fi
        done
    fi
    
    # Run SourceExtractor
    if [ -n "$weight_image" ]; then
        echo "  → Weight: $weight_image ($weight_type)"
    fi

    if sex "$image" \
        -c "$CONFIG_FILE" \
        -CATALOG_NAME "$catalog" \
        -CHECKIMAGE_NAME "$checkimg" \
        ${weight_type:+-WEIGHT_TYPE "$weight_type"} \
        ${weight_image:+-WEIGHT_IMAGE "$weight_image"} \
        2>&1 | grep -v "^>" ; then
        
        echo -e "  ${GREEN}✓ Success!${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "  ${RED}✗ ERROR processing $image${NC}"
    fi
    echo
done

# Summary
echo "============================================================"
echo -e "SUMMARY: ${GREEN}$SUCCESS_COUNT${NC}/${TOTAL_COUNT} images processed successfully"
echo "============================================================"
echo -e "\nCatalogs saved in './$OUTPUT_DIR/' directory"
