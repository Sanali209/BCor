"""
XMP Writer - Writes LLM-generated tags to image XMP metadata
Uses PIL/Pillow for native XMP read/write operations on all supported formats
Includes disk caching to avoid reprocessing already tagged images
"""
import sys
import os
import hashlib

from numba.scripts.generate_lower_listing import description

# Add Python directory to path to access SLM framework
python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from diskcache import Cache
from loguru import logger

# Import comprehensive logging
from SLM.logging import (
    image_logger,
    ProcessingPhase,
    LogLevel,
    get_image_context
)

from PIL import Image
import xml.etree.ElementTree as ET

import pyexiv2
from typing import Optional, List, Dict, Any


class XMPMetadataHandler:
    """Handles XMP metadata for images using pyexiv2 (Windows-compatible)."""

    def write_metadata(self, image_path: str, title: Optional[str] = None,
                       description: Optional[str] = None, rating: Optional[int] = None,
                       subjects: Optional[List[str]] = None):
        """Write XMP metadata directly to image file."""
        with pyexiv2.Image(image_path) as img:
            if title is not None:
                img.modify_xmp({"Xmp.dc.title": title})
            if description is not None:
                img.modify_xmp({"Xmp.dc.description": description})
            if rating is not None:
                img.modify_xmp({"Xmp.xmp.Rating": str(rating)})
            if subjects:
                img.modify_xmp({"Xmp.dc.subject": subjects})

            print(f"Wrote XMP metadata to {image_path}")
            data = self.read_metadata(image_path)
            print(data)

    def read_metadata(self, image_path: str) -> Dict[str, Any]:
        """Read XMP metadata from image file."""
        with pyexiv2.Image(image_path) as img:
            xmp = img.read_xmp()

        title = xmp.get('Xmp.dc.title')
        if isinstance(title, dict):
            title = title.get('lang="x-default"')

        description = xmp.get('Xmp.dc.description')
        if isinstance(description, dict):
            description = description.get('lang="x-default"')

        subject = xmp.get('Xmp.dc.subject')

        rating = xmp.get('Xmp.xmp.Rating', ['0'])[0] if xmp.get('Xmp.xmp.Rating') else '0'
        data = {
            'title': title,
            'description': description,
            'subjects': subject,
            'rating': int(rating) if rating.isdigit() else 0,
        }

        return data

class XMPWriter:
    """Handles writing LLM tags to XMP metadata using XMPMetadataHandler"""

    WD_TAG_PREFIXES = ["auto/wd_tag/", "auto/wd_characters/", "auto/wd_rating/"]
    CACHE_VERSION = "2.0"  # Increment when switching to PIL implementation

    # XMP namespaces
    XMP_NS = "http://ns.adobe.com/xap/1.0/"
    DC_NS = "http://purl.org/dc/elements/1.1/"
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

    def __init__(self):
        self.xmp_handler = XMPMetadataHandler()
        self._processed_cache = None
        self._init_cache()

    def _generate_xmp_xml(self, tags: list) -> str:
        """Generate XMP XML from tag list"""
        if not tags:
            return ""

        # Create root RDF element
        rdf = ET.Element("rdf:RDF")
        rdf.set("xmlns:rdf", self.RDF_NS)

        # Create description element
        desc = ET.SubElement(rdf, "rdf:Description")
        desc.set("xmlns:dc", self.DC_NS)
        desc.set("xmlns:xmp", self.XMP_NS)
        desc.set("xmp:CreatorTool", "LLM XMP Tagger")

        # Add subject (tags)
        subject = ET.SubElement(desc, "dc:subject")
        bag = ET.SubElement(subject, "rdf:Bag")

        for tag in tags:
            li = ET.SubElement(bag, "rdf:li")
            li.text = tag

        # Convert to string
        xml_str = ET.tostring(rdf, encoding='unicode', method='xml')
        return xml_str

    def _parse_xmp_xml(self, xmp_data) -> list:
        """Parse XMP data to extract tags - handles different PIL return types"""
        if not xmp_data:
            return []

        try:
            # PIL's getxmp() can return different types
            if isinstance(xmp_data, dict):
                # Sometimes returns a dict - look for XML in common keys
                xmp_xml = None
                for key in ['xmp', 'XMP', 'xml']:
                    if key in xmp_data and isinstance(xmp_data[key], (str, bytes)):
                        xmp_xml = xmp_data[key]
                        break
                if xmp_xml is None:
                    return []  # No XML found in dict
            elif isinstance(xmp_data, bytes):
                xmp_xml = xmp_data.decode('utf-8', errors='ignore')
            elif isinstance(xmp_data, str):
                xmp_xml = xmp_data
            else:
                return []  # Unknown type

            # Parse the XML
            root = ET.fromstring(xmp_xml)
            tags = []

            # Find all dc:subject/rdf:Bag/rdf:li elements
            for subject in root.findall(".//{http://purl.org/dc/elements/1.1/}subject"):
                for bag in subject:
                    if bag.tag.endswith("Bag"):
                        for li in bag:
                            if li.tag.endswith("li") and li.text:
                                tags.append(li.text.strip())

            return tags
        except Exception as e:
            logger.warning(f"Failed to parse XMP data: {e}")
            return []

    def _init_cache(self):
        """Initialize the disk cache for tracking processed images"""
        try:
            # Use local cache directory relative to this script
            cache_dir = os.path.join(os.path.dirname(__file__), "cache", "xmp_processed")

            # Initialize diskcache.Cache
            self._processed_cache = Cache(cache_dir)

            # Check cache version and clear if outdated
            cached_version = self._processed_cache.get("version", self.CACHE_VERSION)
            if cached_version != self.CACHE_VERSION:
                logger.info(
                    f"XMP processing cache version mismatch ({cached_version} vs {self.CACHE_VERSION}), clearing cache")
                self._processed_cache.clear()
                self._processed_cache["version"] = self.CACHE_VERSION

        except Exception as e:
            logger.warning(f"Failed to initialize XMP processing cache: {e}")
            self._processed_cache = None

    def _get_cache_key(self, image_path: str) -> str:
        """Generate a cache key for the image path"""
        # Use absolute path to ensure uniqueness
        abs_path = os.path.abspath(image_path)
        # Create MD5 hash of the path for consistent key length
        return hashlib.md5(abs_path.encode()).hexdigest()

    def readXMPTags(self, image_path: str) -> list:
        """Read XMP tags from image using XMPMetadataHandler"""
        try:
            metadata = self.xmp_handler.read_metadata(image_path)
            subject = metadata.get('subjects', [])
            if subject is None:
                return []
            return subject
        except Exception as e:
            logger.warning(f"Failed to read XMP tags from {image_path}: {e}")
            return []

    def writeXMPTags(self, image_path: str, tags: list) -> bool:
        """Write XMP tags to image using XMPMetadataHandler"""
        try:

            # Write metadata using XMPMetadataHandler
            self.xmp_handler.write_metadata(image_path,subjects=tags)


            return True

        except Exception as e:
            logger.error(f"Failed to write XMP tags to {image_path}: {e}")
            return False

    def has_wd_tags(self, image_path: str) -> bool:
        """Check if image already has WD tagger tags using cache-first approach"""
        # Check cache first for performance
        if self._processed_cache is not None:
            cache_key = self._get_cache_key(image_path)
            cached_result = self._processed_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Cache miss - read XMP tags using XMPMetadataHandler
        try:
            current_tags = self.readXMPTags(image_path)

            # Check if any tags start with WD tagger prefixes
            has_tags = False
            if current_tags is None:
                pass
            for tag in current_tags:
                if isinstance(tag, str):
                    for prefix in self.WD_TAG_PREFIXES:
                        if tag.startswith(prefix):
                            has_tags = True
                            break
                    if has_tags:
                        break

            # Cache the result for future lookups
            if self._processed_cache is not None:
                cache_key = self._get_cache_key(image_path)
                self._processed_cache[cache_key] = has_tags

            return has_tags

        except Exception as e:
            logger.error(f"Error checking WD tags for {image_path}: {e}")
            return False

    def write_tags(self, image_path: str, general_tags: list, character_tags: list, rating: str,
                   batch_id: str = None) -> tuple:
        """
        Write tags to XMP metadata with prefixes and comprehensive logging

        Args:
            image_path: Path to image file
            general_tags: List of general tags
            character_tags: List of character tags
            rating: Rating string (e.g., 'safe', 'questionable', 'explicit')
            batch_id: Optional batch identifier for logging

        Returns:
            tuple: (success: bool, tags_added: int, error: str)
        """
        # Create image context for logging
        image_context = get_image_context(image_path, batch_id,
                                          general_tags_count=len(general_tags),
                                          character_tags_count=len(character_tags),
                                          rating=rating)

        with image_logger.operation_context(ProcessingPhase.STORAGE, "xmp_write", image_context):
            try:
                # Phase 1: Read existing metadata using XMPMetadataHandler
                with image_logger.operation_context(ProcessingPhase.VALIDATION, "metadata_read", image_context):
                    current_tags = self.readXMPTags(image_path)
                    existing_tags_count = len(current_tags)

                    image_logger.log_event(
                        ProcessingPhase.VALIDATION,
                        LogLevel.DEBUG,
                        image_context,
                        "metadata_read_complete",
                        f"Read {existing_tags_count} existing tags from XMP metadata",
                        performance_metrics={'existing_tags_count': existing_tags_count}
                    )

                # Phase 2: Prepare new tags with prefixes
                with image_logger.operation_context(ProcessingPhase.PREPROCESSING, "tag_preparation", image_context):
                    new_tags = []

                    # Add general tags with prefix
                    for tag in general_tags:
                        tag_clean = tag.strip().replace(" ", "_")
                        prefixed_tag = f"auto/wd_tag/{tag_clean}"
                        new_tags.append(prefixed_tag)

                    # Add character tags with prefix
                    for character in character_tags:
                        char_clean = character.strip().replace(" ", "_")
                        prefixed_char = f"auto/wd_characters/{char_clean}"
                        new_tags.append(prefixed_char)

                    # Add rating tag with prefix
                    if rating:
                        rating_tag = f"auto/wd_rating/{rating}"
                        new_tags.append(rating_tag)

                    # Check for duplicates
                    duplicate_tags = set(current_tags) & set(new_tags)
                    unique_new_tags = [tag for tag in new_tags if tag not in current_tags]

                    preparation_metrics = {
                        'new_tags_prepared': len(new_tags),
                        'unique_new_tags': len(unique_new_tags),
                        'duplicate_tags': len(duplicate_tags),
                        'general_tags': len(general_tags),
                        'character_tags': len(character_tags),
                        'rating_provided': rating is not None
                    }

                    image_logger.log_event(
                        ProcessingPhase.PREPROCESSING,
                        LogLevel.DEBUG,
                        image_context,
                        "tag_preparation_complete",
                        f"Prepared {len(unique_new_tags)} unique new tags ({len(duplicate_tags)} duplicates skipped)",
                        performance_metrics=preparation_metrics
                    )

                # Phase 3: Merge and deduplicate tags
                with image_logger.operation_context(ProcessingPhase.POST_PROCESSING, "tag_merge", image_context):
                    all_tags = list(set(current_tags + new_tags))
                    tags_added = len(unique_new_tags)

                    merge_metrics = {
                        'total_tags_before': len(current_tags),
                        'total_tags_after': len(all_tags),
                        'tags_added': tags_added,
                        'duplicates_removed': len(current_tags + new_tags) - len(all_tags)
                    }

                    image_logger.log_event(
                        ProcessingPhase.POST_PROCESSING,
                        LogLevel.DEBUG,
                        image_context,
                        "tag_merge_complete",
                        f"Merged tags: {len(current_tags)} -> {len(all_tags)} total ({tags_added} added)",
                        performance_metrics=merge_metrics
                    )

                # Phase 4: Write to XMP metadata using XMPMetadataHandler
                with image_logger.operation_context(ProcessingPhase.STORAGE, "xmp_save", image_context):
                    try:
                        # Check if image format supports XMP metadata
                        with Image.open(image_path) as img:
                            xmp_supported_formats = {'JPEG', 'PNG', 'TIFF', 'WEBP'}

                            if img.format not in xmp_supported_formats:
                                # Format doesn't support XMP - skip writing but report success
                                logger.info(
                                    f"Skipping XMP writing for {img.format} format (not supported): {image_path}")

                                image_logger.log_event(
                                    ProcessingPhase.STORAGE,
                                    LogLevel.INFO,
                                    image_context,
                                    "xmp_write_skipped",
                                    f"XMP writing skipped for {img.format} format (not supported)",
                                    performance_metrics={
                                        'tags_skipped': len(all_tags),
                                        'reason': 'format_not_supported'
                                    }
                                )
                                # Still mark as processed in cache since we "processed" it
                                if self._processed_cache is not None and tags_added > 0:
                                    cache_key = self._get_cache_key(image_path)
                                    self._processed_cache[cache_key] = True
                                return (True, tags_added, None)

                        # Format supports XMP - write using XMPMetadataHandler
                        success = self.writeXMPTags(image_path, all_tags)
                        if not success:
                            error_msg = f"Failed to write XMP tags to {image_path}"
                            image_logger.log_event(
                                ProcessingPhase.STORAGE,
                                LogLevel.ERROR,
                                image_context,
                                "xmp_write_failed",
                                error_msg
                            )
                            return (False, 0, error_msg)

                        # Verify XMP was written correctly by reading it back
                        verification_tags = self.readXMPTags(image_path)

                        # Check if our WD tags are present in the written XMP
                        wd_tags_written = [tag for tag in verification_tags if
                                           any(tag.startswith(prefix) for prefix in self.WD_TAG_PREFIXES)]
                        verification_passed = len(wd_tags_written) >= len(unique_new_tags)

                        save_metrics = {
                            'final_tag_count': len(all_tags),
                            'tags_added': tags_added,
                            'wd_tags_verified': len(wd_tags_written),
                            'verification_passed': verification_passed,
                            'operation': 'xmp_metadata_update'
                        }

                        if verification_passed:
                            image_logger.log_event(
                                ProcessingPhase.STORAGE,
                                LogLevel.INFO,
                                image_context,
                                "xmp_write_complete",
                                f"Successfully wrote {tags_added} tags to XMP metadata (verified: {len(wd_tags_written)} WD tags)",
                                performance_metrics=save_metrics
                            )
                        else:
                            logger.warning(
                                f"XMP verification failed for {image_path}: expected {len(unique_new_tags)} WD tags, found {len(wd_tags_written)}")
                            image_logger.log_event(
                                ProcessingPhase.STORAGE,
                                LogLevel.WARNING,
                                image_context,
                                "xmp_write_complete_unverified",
                                f"Wrote {tags_added} tags to XMP metadata (verification inconclusive)",
                                performance_metrics=save_metrics
                            )

                    except Exception as save_error:
                        # XMP writing failed
                        error_msg = f"Failed to write XMP metadata to {image_path}: {str(save_error)}"
                        image_logger.log_event(
                            ProcessingPhase.STORAGE,
                            LogLevel.ERROR,
                            image_context,
                            "xmp_write_failed",
                            error_msg,
                            error_details=str(save_error)
                        )
                        return (False, 0, error_msg)

                # Mark image as processed in cache only on successful save
                if self._processed_cache is not None and tags_added > 0:
                    cache_key = self._get_cache_key(image_path)
                    self._processed_cache[cache_key] = True

                return (True, tags_added, None)

            except Exception as e:
                error_msg = f"Error writing tags to {image_path}: {str(e)}"
                logger.error(error_msg)

                # Log the failure with comprehensive context
                image_logger.log_event(
                    ProcessingPhase.STORAGE,
                    LogLevel.ERROR,
                    image_context,
                    "xmp_write_failed",
                    f"Failed to write XMP tags: {str(e)}",
                    error_details=str(e)
                )

                return (False, 0, str(e))


if __name__ == "__main__":
    """Test XMP read/write functionality with compatibility checks"""
    import sys
    import os

    # Add path for SLM imports
    python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if python_dir not in sys.path:
        sys.path.insert(0, python_dir)

    from SLM.metadata.functions import pil_read_xmp
    from SLM.metadata.MDManager.mdmanager import MDManager

    print("🧪 XMP Read/Write Compatibility Test")
    print("=" * 50)

    # Test data
    test_tags = [
        "auto/wd_tag/dragon_horns",
        "auto/wd_tag/fantasy_art",
        "auto/wd_characters/elf_girl",
        "auto/wd_rating/safe"
    ]

    # Find a test image (use the first JPEG/PNG found in samples)
    test_image = None
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    if os.path.exists(samples_dir):
        for file in os.listdir(samples_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_image = os.path.join(samples_dir, file)
                break

    if not test_image:
        print("❌ No test image found in samples directory")
        sys.exit(1)

    print(f"📁 Test image: {test_image}")

    # Initialize XMPWriter
    writer = XMPWriter()
    try:
        initial_tags = writer.readXMPTags(test_image)
        print(f"   ✅ Initial tags: {len(initial_tags)} tags")
        if initial_tags:
            print(f"   📋 Sample: {initial_tags[:3]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n2️⃣ Testing XMPWriter.writeXMPTags()...")
    try:
        success = writer.writeXMPTags(test_image, test_tags)
        if success:
            print("   ✅ Write successful")
        else:
            print("   ❌ Write failed")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n3️⃣ Testing XMPWriter.readXMPTags() after write...")
    try:
        written_tags = writer.readXMPTags(test_image)
        print(f"   📖 Read back: {len(written_tags)} tags")
        if written_tags:
            print(f"   📋 Sample: {written_tags[:3]}")

        # Check if our test tags are present
        test_tags_found = [tag for tag in written_tags if tag in test_tags]
        print(f"   ✅ Test tags found: {len(test_tags_found)}/{len(test_tags)}")
        if len(test_tags_found) != len(test_tags):
            print(f"   ⚠️  Missing: {[tag for tag in test_tags if tag not in written_tags]}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n4️⃣ Compatibility: PIL functions.pil_read_xmp()...")
    try:
        pil_xmp = pil_read_xmp(test_image)
        if pil_xmp:
            print("   ✅ PIL XMP data found")
            # Try to extract tags from PIL XMP
            try:
                from SLM.metadata.functions import IPTC_get_keywords

                iptc_tags = IPTC_get_keywords(test_image)
                if iptc_tags:
                    print(f"   📖 IPTC tags: {len(iptc_tags)} tags")
                else:
                    print("   📖 No IPTC tags")
            except:
                print("   📖 IPTC read failed")
        else:
            print("   ⚠️  No PIL XMP data")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n5️⃣ Compatibility: MDManager XMP reading...")
    try:
        md_manager = MDManager(test_image)
        metadata = md_manager.Read()
        if metadata:
            print("   ✅ MDManager metadata found")
            # Check for XMP-related fields
            xmp_fields = [k for k in metadata.keys() if 'xmp' in k.lower() or 'subject' in k.lower()]
            if xmp_fields:
                print(f"   📋 XMP fields: {xmp_fields[:3]}")
            else:
                print("   📋 No XMP fields found")
        else:
            print("   ⚠️  No MDManager metadata")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n6️⃣ Testing XMPWriter.has_wd_tags()...")
    try:
        has_wd = writer.has_wd_tags(test_image)
        print(f"   ✅ WD tags detected: {has_wd}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n🎉 Test completed!")
    print("💡 Note: This test modifies the test image. Restore from backup if needed.")
