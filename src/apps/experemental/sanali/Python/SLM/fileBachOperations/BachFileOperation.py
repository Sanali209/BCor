import fnmatch
import os
import cv2
import PIL
import send2trash
from PIL.Image import Image
from loguru import logger
from tqdm import tqdm

from SLM.NLPSimple.NLPPipline import NLPPipline
from SLM.NLPSimple.whoshMach import matches_subscription
from SLM.appGlue.iotools.pathtools import get_files, move_file_ifExist
from SLM.files_data_cache.pool import PILPool
from SLM.metadata.MDManager.mdmanager import MDManager


def get_empty_folders(path):
    empty_folders = []
    for root, dirs, files in os.walk(path):
        if len(dirs) == 0 and len(files) == 0:
            empty_folders.append(root)
    return empty_folders


def delete_empty_folders(path):
    empty_folders = get_empty_folders(path)
    for folder in empty_folders:
        os.rmdir(folder)


def deleteFilesByExt(path, exts):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(exts):
                os.remove(os.path.join(root, file))


class ProcessFile:
    def __init__(self):
        self.path = ""
        self.data = {}


class BachOperation:
    def __init__(self):
        self.result = None
        self.item = None
        self.argDict = {}

    def CheckDependencies(self):
        return True

    def run(self, bachManager: 'BachOperationPipeline'):
        pass


class BachOperationPipeline:
    """
    base class for bach operations with files

    Sample:
    batch_operation = BachOperationPipeline()
    batch_operation.createFileList(r'G:\path\to\files')

    zerosizedelete = DeleteZeroSizeFiles()
    batch_operation.bachManager.operations.append(zerosizedelete)

    extr = ExtensionReport()
    batch_operation.operations.append(extr)

    batch_operation.run()

    print(extr.report)
    """

    def __init__(self):
        self.operations = []
        self.files = []
        self.root_path = ""
        self.data = {}

    def run(self):
        tqi = tqdm(self.files)
        for image in tqi:
            tqi.set_postfix_str("process image {}".format(image.path))
            curent_item = image
            for batch_operation in self.operations:
                batch_operation.item = curent_item
                batch_operation.run(self)
                curent_item = batch_operation.item
                if batch_operation.result == 'break':
                    break

    def createFileList(self, base_path, exts=None):
        if exts is None:
            exts = ['*']
        self.root_path = base_path
        paths = get_files(base_path, exts)
        for path in paths:
            image = ProcessFile()
            image.path = path
            self.files.append(image)


class DeleteZeroSizeFiles(BachOperation):

    def run(self, bachManager: 'BachOperationPipeline'):
        if os.path.getsize(self.item.path) == 0:
            logger.debug("delete zero file: " + self.item.path)
            os.remove(self.item.path)
            return 'break'


class FixNoLowerCaseExtension(BachOperation):

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        ext = os.path.splitext(path)[1]
        if ext != ext.lower():
            new_path = os.path.splitext(path)[0] + ext.lower()
            logger.debug("rename file: " + path + " to " + new_path)
            os.rename(path, new_path)
            self.item.path = new_path
            return 'break'


class DeleteSmallImages(BachOperation):
    def __init__(self, size=233):
        super().__init__()
        self.size = size

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        try:
            image = PILPool.get_pil_image(path)
        except Exception as e:
            logger.error(f'error: {path} {str(e)}')
            return 'false'
        size = image.size
        image.close()
        # if imageView is smaller than 234x234 delete it
        if size[0] < self.size or size[1] < self.size:
            logger.debug("imageView {} is smaller than {}x{}".format(path, self.size, self.size))
            send2trash.send2trash(path)
            return 'break'


class DeleteFilesWithNoExtension(BachOperation):

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        if os.path.splitext(path)[1] == "":
            logger.debug("delete file with no extension: " + path)
            send2trash.send2trash(path)
            return 'break'


class DeleteFilesByMasck2(BachOperation):
    def __init__(self):
        super().__init__()
        self.mascks = []

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        for masck in self.mascks:
            if fnmatch.fnmatch(path, masck):
                logger.debug("delete file by masck: " + path)
                send2trash.send2trash(path)
                return 'break'


class DeleteFilesByMasck(BachOperation):
    def __init__(self):
        super().__init__()
        self.masck = ""

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        if fnmatch.fnmatch(path, self.masck):
            logger.debug("delete file by masck: " + path)
            os.remove(path)
            return 'break'


class SeparateFilesByMascks(BachOperation):
    def __init__(self):
        super().__init__()
        self.sepPath = ""
        self.mascks = []

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        for masck in self.mascks:
            if fnmatch.fnmatch(path, masck):
                # get relative ProjectSettingsPath
                relPath = os.path.relpath(path, bachManager.root_path)
                newPath = os.path.join(self.sepPath, relPath)
                # muve file
                os.makedirs(os.path.dirname(newPath), exist_ok=True)
                logger.debug("separate file by masck: " + newPath)
                if os.path.exists(newPath):
                    os.remove(newPath)
                os.rename(path, newPath)
                self.item.path = newPath
                return 'ok'


class ResizeImageBiggerThan(BachOperation):
    def __init__(self, size=4096, by_biger_edge=True):
        super().__init__()
        self.size = size
        self.by_biger_edge = by_biger_edge

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        try:
            image = PILPool.get_pil_image(path)
        except Exception as e:
            logger.error(f'error: {path} {str(e)}')
            return 'false'
        # get imageView size
        width, height = image.size
        desired_size = self.size
        aspect_ratio = width / float(height)
        if self.by_biger_edge:
            if width > height:
                if width <= desired_size:
                    return ''
                width = desired_size
                height = int(width / aspect_ratio)
            else:
                if height <= desired_size:
                    return ''
                height = desired_size
                width = int(height * aspect_ratio)
        else:
            if width < height:
                if width <= desired_size:
                    return ''
                width = desired_size
                height = int(width / aspect_ratio)
            else:
                if height <= desired_size:
                    return ''
                height = desired_size
                width = int(height * aspect_ratio)

        # resize imageView
        image = image.resize((width, height), PIL.Image.ANTIALIAS)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(path)
        image.close()
        logger.debug("resize imageView: " + path)
        return ''


class validateImage(BachOperation):
    def __init__(self):
        super().__init__()

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        try:
            image = PILPool.get_pil_image(path)
            image.close()
        except Exception as e:
            logger.error('error: ' + path + ' ' + str(e))
            # if extension is jpg or png
            # read and show imageView by opencv
            if os.path.splitext(path)[1] in ['.jpg', '.png']:
                try:
                    img = cv2.imread(path)
                    cv2.imshow('imageView', img)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                except Exception as e:
                    print('error: ' + path + ' ' + str(e))
                    # delete file
                    os.remove(path)
                    return 'false'

                # add to file with errors
                with open('errors.txt', 'a') as f:
                    # write ProjectSettingsPath end error on new line
                    f.write(path + ' ' + str(e) + '\n')
                return 'false'

        return 'ok'


class convertImageToJpg(BachOperation):

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        # get extension
        ext = os.path.splitext(path)[1]
        if ext == '.bmp' or ext == '.jpe' or ext == '.png' or ext == '.gif' or ext == '.tiff' or ext == '.tif':
            try:
                image = PILPool.get_pil_image(path)
                new_path = os.path.splitext(path)[0] + '.jpg'
                image.save(new_path, "JPEG", quality=100)
                image.close()
                os.remove(path)

                print("convert imageView to jpg: " + path)
                self.item.path = new_path
                return 'change source'
            except Exception as e:
                print('error: ' + path + ' ' + str(e))
                return 'false'

        return 'ok'


class MoveFilesByNLPTokens(BachOperation):
    def __init__(self):
        super().__init__()
        self.move_dictionary = []  # sample_dict = [{'mach pattern': 'mass AND effect', 'destination': 'mass effect'}]
        self.nlp_pipline: NLPPipline = None

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        file_name = os.path.basename(path)
        self.nlp_pipline.text = file_name
        self.nlp_pipline.run()
        tokens = self.nlp_pipline.tokens
        tokens_text = ' '.join(tokens)
        print(tokens_text)
        for move_dict_item in self.move_dictionary:
            mach = matches_subscription(tokens_text, move_dict_item['mach pattern'])
            if mach:
                file_path = self.item.path
                file_parent_dir = os.path.dirname(file_path)
                parent_dir_name = os.path.basename(file_parent_dir)
                if parent_dir_name == move_dict_item['destination']:
                    continue
                newPath = os.path.join(file_parent_dir, move_dict_item['destination'], file_name)
                # move file
                os.makedirs(os.path.dirname(newPath), exist_ok=True)
                print("move file by tokens: " + newPath)
                if os.path.exists(newPath):
                    os.remove(newPath)
                os.rename(path, newPath)
                self.item.path = newPath
        return 'ok'


class EmbedNLPTokensToXMP(BachOperation):
    def __init__(self):
        super().__init__()
        self.nlp_pipline: NLPPipline = None

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        file_name = os.path.basename(path)
        self.nlp_pipline.text = file_name
        self.nlp_pipline.run()
        tokens = self.nlp_pipline.tokens

        metadata = MDManager(path)
        metadata.Read()
        # xmpKeywords = metadata.getXMPKeywords()
        # if xmpKeywords is None:
        # xmpKeywords = []
        # xmpKeywords.extend([("name|" + name) for name in tokens])
        # xmpKeywords = list(dict.fromkeys(xmpKeywords))
        metadata.Clear()
        # metadata.setXMPKeywords(xmpKeywords)
        metadata.Save()


class move_files_to(BachOperation):
    def __init__(self, path):
        super().__init__()
        self.destination_path = path

    def run(self, bachManager: 'BachOperationPipeline'):
        path = self.item.path
        newPath = os.path.join(self.destination_path, os.path.basename(path))
        # move file
        os.makedirs(os.path.dirname(newPath), exist_ok=True)
        newPath = move_file_ifExist(path, newPath)
        self.item.path = newPath
        return 'ok'


batch_operation = BachOperationPipeline()
batch_operation.createFileList(r'F:\rawimagedb\repository\nsfv repo\drawn\drawn xxx autors\1\Palcomix\2017')
op = move_files_to(r'F:\rawimagedb\repository\nsfv repo\drawn\drawn xxx autors\1\Palcomix\_mix')
batch_operation.operations.append(op)
batch_operation.run()
