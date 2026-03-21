import pyexiv2

# Open the image file
with pyexiv2.Image(r"E:\rawimagedb\repository\_art books\Art_Books_-_Brom__Ofrendas__it_\001 - BROM - OFRENDAS - PORTADA.jpg") as img:
    # Prepare your XMP metadata as a dictionary
    xmp_data = {
        'Xmp.dc.creator': 'John Doe',
        'Xmp.dc.subject': ['tag1', 'tag2'],
        'Xmp.xmp.Rating': '5'
    }
    # Modify (write) XMP metadata
    img.modify_xmp(xmp_data)
    # Changes are saved automatically when using 'with'