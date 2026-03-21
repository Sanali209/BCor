import fnmatch
import os
import time

import pyautogui

from SLM.FuncModule import get_files


#Worck directory: Y:\Art_and_Textures\substanceTextures\Substance materials\Leather_Plastic_Ruber\Leather




def main():

    listofsubstances = get_files(r'Y:\Art_and_Textures\substanceTextures', "*.sbsar")
    # and open substance filepath in externally programm
    # count of listofsubstances
    count = listofsubstances.__len__()
    counter = 0
    for substance in listofsubstances:
        counter += 1
        print(str(counter) + " of " + str(count))
        # check if substance file have tumbnail viz name of substance bat extension .png
        if os.path.exists(substance.replace('.sbsar', '.png')) or os.path.exists(substance.replace('.sbsar', '.jpg')):
            continue
        # open in substance filepath in externally programm viz view no paitogui
        tumbnailname = substance.replace('.sbsar', '.png')

        if (os.path.exists(tumbnailname)):
            print("tumbnail exist")
            print(tumbnailname)
            continue
        os.startfile(substance)
        time.sleep(15)
        # wait for substance filepath to open

        # wait for opened window of substance to be focused
        camerabut = pyautogui.locateOnScreen('CameraButton.png')
        print(camerabut)

        pyautogui.click(camerabut)
        # set focus to substance window
        time.sleep(0.5)
        saveviewportimbutton = pyautogui.locateOnScreen('SaveVIButton.png')

        pyautogui.click(saveviewportimbutton)
        # wait for save viewport imageView button to be clicked
       # create tumbnail name viz join substance directory and substance file name without extension
        print(substance)

        time.sleep(0.5)
        pyautogui.write(tumbnailname)
        #pyautogui.write(os.ProjectSettingsPath.join(os.ProjectSettingsPath.dirname(substance)))

        # press enter
        pyautogui.press('enter')


        # wait curent process 1 second
        time.sleep(2)

        try:
            pyautogui.getWindowsWithTitle("substance")[0].close()
        except:
            print ("no substance window")






        # wait for substance window to be focused




# execute main function
if __name__ == "__main__":
    main()




