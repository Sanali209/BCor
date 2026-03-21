
import clr


clr.AddReference("MetadataExtractor")


from MetadataExtractor import ImageMetadataReader


def read_image_metadata(path):
    # mdmanager = MDManager(path)
    # mdmanager.Read()
    # metadata = mdmanager.metadata


    metadata1 = ImageMetadataReader.ReadMetadata(path)
    return convert_ImageMetadata_reader_to_exiftool_metadata(metadata1)

def convert_ImageMetadata_reader_to_exiftool_metadata(metadata):
    exiftool_metadata = {}
    for directory in metadata:
        for tag in directory.Tags:
            exiftool_metadata[directory.Name +": " +tag.Name] = tag.Description

    return exiftool_metadata

# meta = read_image_metadata(r"F:\rawimagedb\repository\safe repo\presort\the witcher\ciri cosplay\ms1TAeO.jpg")

# print(meta)