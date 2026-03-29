import pyexiv2
import pathlib
import os

path = r"D:\image_db\safe repo\ddsearch\kim_possible\kim_possible_1.webp"
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

print(f"Testing pyexiv2 on: {path}")
try:
    img = pyexiv2.Image(path)
    print("Read EXIF:", img.read_exif())
    print("Read XMP:", img.read_xmp())
    
    test_tags = {"Xmp.dc.subject": "test_tag_123"}
    print(f"Attempting to write XMP: {test_tags}")
    img.modify_xmp(test_tags)
    img.close()
    
    # Verify
    img2 = pyexiv2.Image(path)
    new_xmp = img2.read_xmp()
    print("Verified XMP:", new_xmp)
    img2.close()
    
    if test_tags["Xmp.dc.subject"] in new_xmp.get("Xmp.dc.subject", ""):
        print("SUCCESS: XMP Write/Read verified on WebP!")
    else:
        print("FAILURE: XMP data mismatch.")

except Exception as e:
    print(f"ERROR: {e}")
