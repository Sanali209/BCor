import os.path
import shutil

from flask import Flask, render_template, request

from SLM.FuncModule import get_files

from SLM.vision.dubFileHelper import DuplicateFindHelper

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

# register static instance
worckpath = r"F:\adaulth\_by theme\_mix\buties"
dupFinder = DuplicateFindHelper()
filesList = get_files(worckpath, ["*.jpg", "*.png", "*.jpeg", "*.bmp"])
encodings = dupFinder.CreateCNNEncoding(filesList)
idublicates = dupFinder.FaindCNNDubs(encodings, similarity=0.85)
dupFinder.ClearEmptyDubsGroup(idublicates)
dupFinder.ClearFullCollidedDubsGroup(idublicates)

b64hash = {}


@app.context_processor
def utility_processor():
    def imagePathTobase64Embed(imagepath):
        import base64
        if imagepath in b64hash:
            # print("imagepath: " + imagepath + " from cache")
            return b64hash[imagepath]
        with open(imagepath, "rb") as image_file:
            # print("imagepath: " + imagepath)
            encoded_string = base64.b64encode(image_file.read())
        # convert for embeding in html imageView src="data:imageView/png;base64,{{imagePathTobase64Embed(imagepath)}}"
        b64hash[imagepath] = encoded_string.decode("utf-8")
        return b64hash[imagepath]

    return dict(imagePathTobase64Embed=imagePathTobase64Embed)


@app.route('/', methods=['GET'])
def index():
    dublicates = None
    if dublicates is None: dublicates = idublicates
    # get param from url metod get - ?mode=dubsearch
    mode = request.args.get('mode')
    similarity = request.args.get('similarity')
    directory = request.args.get('directory')
    if directory is not None:
        worckdir= directory
    print("mode: " + str(mode))

    if mode == "gr_in_folders":
        for dublicate in dublicates:
            baseimagepath = dublicate
            # Filename without extension
            imageName = os.path.basename(baseimagepath)
            newfolder = os.path.splitext(imageName)[0]
            fpath = os.path.join(worckpath, newfolder)
            # muve base imageView to new folder
            if not os.path.exists(fpath):
                os.makedirs(fpath)
            newimagepath = os.path.join(fpath, imageName)
            shutil.move(baseimagepath, newimagepath)
            for dub in dublicates[dublicate]:
                imageName = os.path.basename(dub[0])
                newimagepath = os.path.join(fpath, imageName)
                if os.path.exists(dub[0]):
                    shutil.move(dub[0], newimagepath)
        mode = "refresh_dubs"

    if "refresh_dubs" == mode:
        similarity = float(similarity)
        filesList = get_files(worckpath, ["*.jpg", "*.png", "*.jpeg", "*.bmp"])
        encodings = dupFinder.CreateCNNEncoding(filesList)
        dublicates = dupFinder.FaindCNNDubs(encodings, similarity=similarity)
        dupFinder.ClearEmptyDubsGroup(dublicates)
        dupFinder.ClearFullCollidedDubsGroup(dublicates)

    sliceosdubs = {}
    fcounter = 0
    itemsget = 10
    for dublicate in dublicates:
        if fcounter < itemsget:
            sliceosdubs[dublicate] = dublicates[dublicate]
            fcounter += 1
        else:
            break



    return render_template('index.html', dublicates=sliceosdubs, worckpath=worckpath + "\\", similarity=similarity,
                           mode=mode)


if __name__ == '__main__':

    app.run(debug=True)
