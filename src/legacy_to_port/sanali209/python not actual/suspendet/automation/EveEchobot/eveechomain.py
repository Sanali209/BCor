import cv2 as cv
import numpy as np
from PIL import ImageGrab


#https://github.com/splintered-reality/py_trees

# grab screen from game in certain area
def grab_screen():

    # grab screen
    screen = np.array(ImageGrab.grab())
    # convert to bgr
    screen = cv.cvtColor(screen, cv.COLOR_RGB2BGR)

    # return screen
    return screen

grabed_screen = grab_screen()

#fullscreenImage = cv.imread(r"D:\imageanalize\EveEchobot\shots\Screenshot_1.png")

machImage = cv.imread(r"D:\imageanalize\EveEchobot\shots\portrait.png")

result = cv.matchTemplate(grabed_screen, machImage, cv.TM_CCOEFF_NORMED)

#get best match
min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

treashold = 0.8
if max_val > treashold:
    cv.rectangle(grabed_screen, max_loc, (max_loc[0] + machImage.shape[1], max_loc[1] + machImage.shape[0]), (0, 0, 255), 2)
else:
    # print on imageView "not found"
    cv.putText(grabed_screen, "not found", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

cv.imshow("result", grabed_screen)

cv.waitKey(0)