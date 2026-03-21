import os
import subprocess
import time


import SLM


exiftool_exists = False
from loguru import logger

try:
    import exiftool

    exiftool_exists = True
except:
    logger.debug("load exiftool error")


class MDManager:

    # expected fields rating,tags

    # init
    def __init__(self, path):

        if exiftool_exists:
            self.backend = MDMManagerBackend()
        else:
            self.backend = None

        self.metadata = {}
        self.path = path
        self.time_stamp_format = '%Y:%m:%d %H:%M:%S'

    def Read(self):
        if self.backend is None:
            return None
        # get all metadata
        meta = self.backend.get_image_all_metadata(self.path)
        meta = self.backend.formate_meta(meta)
        if meta is None:
            return None
        try:
            self.metadata = meta[0]
        except:
            logger.error(f"Error reading metadata-{self.path}")
            return None
        return self.metadata

    def Save(self):
        if self.backend is None:
            return False
        self.metadata['XMP:ModifyDate'] = time.strftime(self.time_stamp_format)
        self.backend.set_image_all_metadata(self.path, self.metadata)

    def Clear(self):
        self.metadata = {}

    def CleanUp(self):
        pass

    # source_property Rating

    def is_meta_modified(self):
        val = self.metadata.get('XMP:ModifyDate', None)
        if val == time.strftime(self.time_stamp_format):
            return False
        return True


class MDMManagerBackend:
    def __init__(self):
        self.exiftool_path = SLM.__path__[0] + '\\exiftool.exe'
        self.fall_buck_enc = ['utf-8', 'ansi']

    def formate_meta(self, meta):
        return meta

    def get_image_all_metadata(self, path):
        return self.get_meta(path, fall_back_enc=self.fall_buck_enc)

    def get_meta(self, path, encoding=None, fall_back_enc=[]):

        with exiftool.ExifToolHelper(executable=self.exiftool_path, encoding=encoding) as et:
            try:
                metadata = et.get_metadata(path)

                return metadata
            except Exception as e:
                if len(fall_back_enc) == 0:
                    logger.error(f"Error reading metadata-{path}-with message:{str(e)}")
                    return [{'MDM:metadata_read_error': str(e)}]
                fall_back_list = [*fall_back_enc]
                cur_enc = fall_back_list.pop()
                logger.debug(f"faill! read metadata of:{path} try get metadata with encoding:{cur_enc}")
                return self.get_meta(path, cur_enc, fall_back_list)

    def set_image_all_metadata(self, filepath, metadata):

        with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
            try:
                res = et.set_tags(filepath, tags=metadata)
                if res.startswith('1 image files updated'):
                    if os.path.exists(filepath + "_original"):
                        # delete temporary file
                        os.remove(filepath + "_original")
                    return True
                else:
                    logger.warning(f"Error writing metadata-{filepath}: {res}")
                    return False

            except Exception as e:
                logger.error(f"Error writing metadata-{filepath}: {str(e)}")
                if os.path.exists(filepath + "_original"):
                    # delete temporary file
                    os.remove(filepath + "_original")
                return False

    def del_tag(self, filepath, tagkey):
        # work only with "EXIF:all" - tag group worck with bags "EXIF:subject" - tag
        # additional info https://exiftool.org/#running
        from exiftool import ExifTool
        with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
            try:
                res = et.execute(*["-" + tagkey + "="] + [filepath])
            except Exception as e:
                res = False
                logger.error(f"Error writing metadata-{filepath}-with message:{str(e)}")
            if os.path.exists(filepath + "_original"):
                # delete temporary file
                os.remove(filepath + "_original")
            return res


class MDMManagerColabBackend:
    def __init__(self):
        pass
        # !apt-get install libimage-exiftool-perl

    def get_image_all_metadata(self, path):
        command = ['exiftool', '-j', path]
        output = subprocess.check_output(command)
        metadata = output.decode('utf-8')
        return metadata

    def set_image_all_metadata(self, filepath, metadata):
        command = ['exiftool', '-j', '-overwrite_original', '-charset', 'filename=utf8']
        for key, value in metadata.items():
            command.append('-' + key + '=' + value)
        command.append(filepath)
        output = subprocess.check_output(command)
        return output
