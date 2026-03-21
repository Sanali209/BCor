import fnmatch
import os
import time

from zipfile import ZipFile

import pyautogui
from PIL import Image

from SLM.files_data_cache.pool import PILPool


def getFiles(curDir, include_masc="*.jpg",file_ignore_masck="",dirignoreMasckifFileexist=""):
    SbsarFiles = []
    for root, dirs, files in os.walk(curDir):
        print(root)
        print(dirs)
        print(files)
        for file in files:
            if fnmatch.fnmatch(file, include_masc):
                SbsarFiles.append(os.path.join(root, file))
    return SbsarFiles

# function for overlaing one imageView to another imageView by tkinter graphics
# load background imageView and overlay imageView
# scale overlay imageView to fit 1/4 of background imageView
# end draw background imageView on right buttom corner of background imageView
def overlay(backgroundp, foregroundp):
    background = PILPool.get_pil_image(backgroundp)
    if(foregroundp.endswith(".psd")):
        return None
    else:
        foreground = PILPool.get_pil_image(foregroundp)
    foreground = foreground.resize((int(background.width / 4), int(background.height / 4)))
    background.paste(foreground, (background.width - foreground.width, background.height - foreground.height))
    #set background imageView max quality
    background.save(backgroundp.replace('.png', '_overlay.jpg'),quality=100)
    background.close()
    foreground.close()
    return backgroundp.replace('.png', '_overlay.jpg')


def main():
    heithPath = r'Y:\Art_and_Textures\tools\textures\JRO 390 Hard Surface Alphas VOL 2'
    fileIncext = '.tif'
    loadtime = 3
    savetime = 2
    Files_for_render = getFiles(heithPath, include_masc="*"+fileIncext)
    count = Files_for_render.__len__()
    counter = 0
    for file in Files_for_render:
        counter += 1
        print(str(counter) + " of " + str(count))
        checkpath = file.replace(fileIncext, '_overlay.jpg')
        if os.path.exists(checkpath):
            continue

        if fnmatch.fnmatch(file, '*_overlay.*'):
            continue

        print(file)
        ScTexturebut = pyautogui.locateOnScreen('scmapBut.png')
        if ScTexturebut is not None:
            pyautogui.click(ScTexturebut)
        time.sleep(0.2)

        from pyrect import Box
        pathbut:Box = pyautogui.locateOnScreen('mappathBut.png')
        pathbut = Box(pathbut.left, pathbut.top+15, pathbut.width, pathbut.height)
        if pathbut is not None:
            pyautogui.click(pathbut)
        time.sleep(0.2)

        # pres control+a
        pyautogui.keyDown('ctrl')
        pyautogui.press('a')
        pyautogui.keyUp('ctrl')
        time.sleep(0.2)

        #write file ProjectSettingsPath
        pyautogui.write(file)
        time.sleep(0.2)
        # press enter
        pyautogui.press('enter')
        time.sleep(loadtime)

        # save tumbnail
        tumbnailname = file.replace(fileIncext, '_tb.png')

        # wait for opened window of substance to be focused
        camerabut = pyautogui.locateOnScreen('cameraBut.png')


        pyautogui.click(camerabut)
        # set focus to substance window
        time.sleep(0.5)
        saveviewportimbutton = pyautogui.locateOnScreen('svpbutt.png')

        pyautogui.click(saveviewportimbutton)
        # wait for save viewport imageView button to be clicked

        time.sleep(0.5)
        pyautogui.write(tumbnailname)
        # pyautogui.write(os.ProjectSettingsPath.join(os.ProjectSettingsPath.dirname(substance)))

        # press enter
        pyautogui.press('enter')
        time.sleep(savetime)
        newthumbname = overlay(tumbnailname, file)
        if newthumbname is not None:
            os.remove(tumbnailname)

        # compress file to zip archive and delete original file no use pyaotogui use zip module
        with ZipFile(file.replace(fileIncext, '.zip'), 'w') as zip:
            # zip faile wizgout folder structure
            zip.write(file, os.path.basename(file))

        os.remove(file)





main()