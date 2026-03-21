import PySimpleGUI as sg

from SLM.FuncModule import get_files
from SLM.vision.huginface.ImageGenreToTags import AiFolderQuickSort

analizepath = r"F:\rawimagedb\repository\nsfv repo\drawn\presort\Bride\mix"
piplaineName = "sanali209/reitBF"
tagPrefix = "ai|bf|reiting"
ignorePrefix = "manual|reitfilter|"

layout = [[sg.Text('worck ProjectSettingsPath'), sg.InputText(analizepath)],
          [sg.Text('piplain'), sg.InputText(piplaineName)],
          [sg.Text('tag prefix'), sg.InputText(tagPrefix)],
          [sg.Text('ignorePrefix'), sg.InputText(ignorePrefix)],
          [sg.Button('Ok'), sg.Button('Cancel')]
          ]

window = sg.Window('NeuralN label to XMPTag', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
    if event == 'Ok':
        analizepath = values[0]
        piplaineName = values[1]
        tagPrefix = values[2]
        ignorePrefix = values[3]
        sorter = AiFolderQuickSort()
        sorter.piplaineName = piplaineName
        sorter.tagPrefix = tagPrefix
        sorter.ignoreXmpTagPrefixExist = ignorePrefix
        sorter.Inith()
        imagelist = get_files(analizepath, [r"*.jpg", r"*.png"])
        sorter.Sort(imagelist)

window.close()
