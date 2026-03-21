import json
import os
import shutil
import webbrowser

import jinja2
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from SLM.FuncModule import getFolders
from notion.client import NotionClient


class UnityDescrFromAssetStoreGrabber:
    def __init__(self, url):
        self.url_curent = url
        self.driver = webdriver.Chrome()
        # set wait time 30 seconds
        self.driver.implicitly_wait(30)
        self.driver.get(self.url_curent)

    def getDetails(self):
        # wait 3 second before parce
        self.driver.implicitly_wait(5)

        Name = self.driver.find_element(By.CLASS_NAME, 'cfm2v').text
        Autor = self.driver.find_element(By.CLASS_NAME, 'U9Sw1').text
        price = self.driver.find_element(By.CLASS_NAME, 'mErEH').text
        price = price.replace('$', '')
        try:
            price = float(price)
        except:
            price = 0

        # faind element div viz class "_27124 product-size"
        File_size = self.driver.find_element(By.CLASS_NAME, 'product-size').text
        File_size = float(File_size.replace('DBRFile size\n', '').replace(' MB', '').replace(' GB', '').replace(' KB', ''))
        # get html of element
        description = self.driver.find_element(By.CLASS_NAME, '_1_3uP').get_attribute('innerHTML')

        categories = self.driver.find_element(By.CLASS_NAME, 'OMTxQ').text
        # convert categories to list
        categories = categories.split('\n')
        # remuve first end last element
        categories.pop(0)
        categories.pop(-1)

        # check if exist element with class = "gAs1z"
        self.driver.implicitly_wait(0.1)
        try:
            self.driver.find_element(By.CLASS_NAME, 'gAs1z')
            # if exist get PathLabelVal
            tags = self.driver.find_element(By.CLASS_NAME, 'gAs1z').text
            # convert tags to list
            tags = tags.split('\n')
        except:
            # if not exist set to None
            tags = None

        data = {'Name': Name, 'Autor': Autor, 'price': price, 'File_size': File_size, 'description': description,
                'categories': categories, 'tags': tags, 'imagesUrls': [], 'officialUrl': self.url_curent,
                'warezUrl': '',
                'localUrl': "", 'torrentUrl': '', 'version': ''}

        # parse images
        # get count of images
        imagescount_text = self.driver.find_element(By.CLASS_NAME, '_3FwS4').text
        # split PathLabelVal by / and get first and last part
        imagesallcount = imagescount_text.split('/')[1]
        # get next imageView button
        getnextimageelem = self.driver.find_element(By.CLASS_NAME, '_23uwk')
        imborder = self.driver.find_element(By.CLASS_NAME, '_2oOZ-')
        for i in range(1, int(imagesallcount)+1):
            # get imageView link
            try:
                image = self.driver.find_element(By.CLASS_NAME, '_8XPJN')
                # add imageView to data
                data['imagesUrls'].append(image.get_attribute('src'))

            except:
                print('error')
            # split PathLabelVal by / and get first and last part
            imagescount_text = self.driver.find_element(By.CLASS_NAME, '_3FwS4').text
            imagescount = int(imagescount_text.split('/')[0])
            if imagescount < int(imagesallcount):
                # muve mouse to next imageView button
                webdriver.ActionChains(self.driver).move_to_element(imborder).perform()
                # get next imageView
                try:
                    getnextimageelem.click()
                except:
                    print('error click')

        return data

    def closeBrowser(self):
        self.driver.close()

    def SavePackDetails(self, path, data):
        # create locl urls field if exist
        if 'imagesUrlsLocal' not in data:
            data['imagesUrlsLocal'] = []
        save_directory = path
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        # create local images
        for i in range(len(data['imagesUrls'])):
            # get imageView
            img_data = requests.get(data['imagesUrls'][i]).content
            # save imageView
            with open(save_directory + '/' + str(i) + '.jpg', 'wb') as handler:
                handler.write(img_data)
            # set local images
            data['imagesUrlsLocal'].append(str(i) + '.jpg')
        fileNamewe = data['Name'].replace(":", "")
        fileNamewe = fileNamewe.replace('|', '')
        fileNamewe = fileNamewe.replace('&', 'and')
        fileNamewe = fileNamewe.replace(',', ' ')
        # save json backcard
        fileName = os.path.join(save_directory, fileNamewe + '.json')
        # replace character not aloved in file name protect first :


        with open(fileName, 'w') as f:
            f.write(json.dumps(data, indent=4))

        # jinjia2 template
        html_template = """
        <html>
        <head>
        <title>{{Name}}</title>
        </head>
        <body>
        <h1>{{Name}}</h1>
        <img src="{{imagesUrlsLocal[0]}}" alt="imageView">
        <h2>{{Autor}}</h2>
        <h3>{{price}}</h3>
        <h3>{{File_size}}</h3>
        <h3>{{categories}}</h3>
        <h3>{{tags}}</h3>
        <p>{{description}}</p>
        <a href="{{url}}">url</a>
        <a href="{{warezUrl}}">warezUrl</a>
        <a href="{{torrentUrl}}">torrentUrl</a>
        <br>
        {% for imageView in imagesUrlsLocal %}
        <img src="{{imageView}}" alt="imageView">
        {% endfor %}
        </body>
        </html>"""

        # renderer template
        html = jinja2.Template(html_template).render(data)
        # save data to file
        fileName = os.path.join(save_directory,fileNamewe + '.html')

        with open(fileName, 'w', encoding='utf-8') as f:
            f.write(html)

        # create tumbnail imageView
        # copy first imageView with name 0.jpg to FileName+thumb.jpg
        shutil.copyfile(save_directory + '/' + '0.jpg',
                        save_directory + '/' + data['Name'].replace(":", "") + '.json' + '.thumb.jpg')


class NotionHelper:
    def __init__(self, token_v2, db_id):
        self.token_v2 = token_v2
        self.db_id = db_id
        self.propertyes = []
        self.PropertyesShema = []
        # request to notion db
        # sample
        # curl        'https://api.notion.com/v1/databases/668d797c-76fa-4934-9b05-ad288df2d136' \
        # - H        'Authorization: Bearer '"$NOTION_API_KEY"'' \
        # - H        'Notion-Version: 2022-06-28'
        self.header = {'Authorization': f'Bearer {self.token_v2}', 'Notion-Version': '2021-05-13'}
        requ = requests.get(f'https://api.notion.com/v1/databases/{self.db_id}',
                            headers={'Authorization': f'Bearer {self.token_v2}', 'Notion-Version': '2021-05-13'})

        jsondata = requ.json()
        title = requ.json()['title'][0]['PathLabelVal']['content']
        for propData in jsondata['properties']:
            self.propertyes.append(propData)

    def createPage(self, title):
        create_URL = f'https://api.notion.com/v1/pages'

        newPageData = {
            "parent": {"database_id": self.db_id},
            "properties": {

                "title": [{"PathLabelVal": {"content": title}}]

            }}
        requ = requests.post(create_URL, headers=self.header, json=newPageData)

        return requ.json()

    def createUAPage(self, data):
        create_URL = f'https://api.notion.com/v1/pages'

        catsJson = []
        for cat in data['categories']:
            catsJson.append({'name': cat})

        tagsJson = []
        if data['tags'] is not None:
            for tag in data['tags']:
                tagsJson.append({'name': tag})

        newPageData = {
            "parent": {"database_id": self.db_id},
            "properties": {

                "title": [{"PathLabelVal": {"content": data['Name']}}],

            },

        }
        data['Autor'] = data['Autor'].replace(',', '').replace('.', ' ')
        newPageData['properties']['Autor'] = {'name': data['Autor']}
        newPageData['properties']['price'] = data['price']
        newPageData['properties']['DBRFile size'] = data['File_size']
        newPageData['properties']['categories'] = catsJson
        if data['tags'] is not None:
            newPageData['properties']['tags'] = tagsJson
        if data['officialUrl'] != '':
            newPageData['properties']['officialUrl'] = data['officialUrl']
        if data['torrentUrl'] != '':
            newPageData['properties']['TorentUrl'] = data['torrentUrl']
        if data['warezUrl'] != '':
            newPageData['properties']['WarezUrl'] = data['warezUrl']
        if data['localUrl'] != '':
            newPageData['properties']['localUrl'] = data['localUrl']
        if data['version'] != '':
            newPageData['properties']['version'] = [{'PathLabelVal': {'content': data['version']}}]
        requ = requests.post(create_URL, headers=self.header, json=newPageData)

        json = requ.json()
        print(json)
        data['page_id'] = requ.json()['id']
        data['NotionPageUrl'] = requ.json()['url']
        return json, data

    def queryDb(self):
        query_URL = f'https://api.notion.com/v1/databases/{self.db_id}/query'
        requ = requests.post(query_URL, headers=self.header)
        print(requ.json())
        return requ.json()

    def getPage(self, page_id):
        query_URL = f'https://api.notion.com/v1/pages/{page_id}'
        requ = requests.get(query_URL, headers=self.header)
        print(requ.json())
        return requ.json()

    def getBlockChildren(self, block_id):
        query_URL = f'https://api.notion.com/v1/blocks/{block_id}/children'
        requ = requests.get(query_URL, headers=self.header)
        print(requ.json())
        return requ.json()

    def append_child_block(self, parent_id: str, children: []):
        query_URL = f'https://api.notion.com/v1/blocks/{parent_id}/children'
        requ = requests.patch(query_URL, headers=self.header, json={"children": children})
        print(requ.json())
        return requ.json()

    def text_append(self, block_id, text):
        query_URL = f'https://api.notion.com/v1/blocks/{block_id}/children'
        requ = requests.patch(query_URL, headers=self.header, json={"children": [
            {"object": "block", "type": "paragraph",
             "paragraph": {"PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": text}}]}}]})
        print(requ.json())
        return requ.json()

    def image_append(self, block_id, source):
        query_URL = f'https://api.notion.com/v1/blocks/{block_id}/children'
        requ = requests.patch(query_URL, headers=self.header, json=
        {"children": [{"object": "block", "type": "imageView",
                       "imageView": {"type": "external", 'external': {'url': source}}}
                      ]}
                              )
        print(requ.json())
        return requ.json()

    def html_to_notion_rich_text(self, html):
        rich_text = []
        soup = BeautifulSoup(html, 'html.parser')
        # if html not contain <p> tag add it
        if not soup.find('p'):
            soup = BeautifulSoup(f'<p>{html}</p>', 'html.parser')

        for tag in soup.find_all():
            if tag.name == 'p':
                # if hes sub tag <strong> or <em> or <u> or <s> anotate as strong
                if tag.find('strong') or tag.find('em') or tag.find('u') or tag.find('s'):
                    rich_text.append({"object": "block", "type": "paragraph", "paragraph": {"PathLabelVal": [{"type": "PathLabelVal",
                                                                                                      "PathLabelVal": {
                                                                                                          "content": tag.text,
                                                                                                          "link": None,
                                                                                                          "annotations": {
                                                                                                              "bold": True,
                                                                                                              "italic": False,
                                                                                                              "strikethrough": False,
                                                                                                              "underline": False}}}]}})
                else:
                    rich_text.append({"object": "block", "type": "paragraph",
                                      "paragraph": {"PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": tag.text}}]}})
            if tag.name == 'img':
                rich_text.append({"object": "block", "type": "imageView", "imageView": {"file": {"url": tag['src']}}})
            if tag.name == 'h1':
                rich_text.append({"object": "block", "type": "heading_1",
                                  "heading_1": {"PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": tag.text}}]}})
            if tag.name == 'h2':
                rich_text.append({"object": "block", "type": "heading_2",
                                  "heading_2": {"PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": tag.text}}]}})
            if tag.name == 'h3':
                rich_text.append({"object": "block", "type": "heading_3",
                                  "heading_3": {"PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": tag.text}}]}})
            if tag.name == 'a':
                rich_text.append({"object": "block", "type": "paragraph", "paragraph": {
                    "PathLabelVal": [{"type": "PathLabelVal", "PathLabelVal": {"content": tag.text, "link": {"url": tag['href']}}}]}})

        return rich_text


class UnityPackInfoParser:
    def __init__(self, packPath):

        self.version = ''
        if not os.path.exists(packPath):
            print('pack not found')
            return
        # if pack is not unity package file
        if not packPath.endswith('.unitypackage'):
            print('pack is not unity package file')
            return
        # read first 1000 bytes of file to string
        with open(packPath, 'rb') as f:
            fileData = f.read(1000)
        # get data from '\x01{' to '\xec' and decode it to utf-8 get it without \x01 and \xec
        fileData = fileData[fileData.find(b'\x01{'):fileData.find(b'\xec')]
        fileData = fileData.decode('utf-8')
        # remove \x01
        fileData = fileData[1:]
        if fileData != '':
            filedatajson = json.loads(fileData)
            print(filedatajson)
            self.version = filedatajson['version']
        else:
            print('file is empty')


if __name__ == '__main__':
    unityPackPath = input('Enter unity pack location: ')
    unityPackFileName = ''
    # find unity package file in folder
    for file in os.listdir(unityPackPath):
        if file.endswith('.unitypackage'):
            unityPackFileName = file
            break

    unityPackFileNameVizgouthExt = unityPackFileName.replace('.unitypackage', '')

    unityPackFileNameFullPath = os.path.join(unityPackPath, unityPackFileName)

    unityPackInfoParser = UnityPackInfoParser(unityPackFileNameFullPath)

    # if file exist pack.txt read url from it
    if os.path.exists(unityPackPath + '\pack.txt'):
        with open(unityPackPath + '\pack.txt', 'r') as f:
            unityPackUrl = f.read()
    else:
        # open browser by comand line for unity pack search  url is 'https://assetstore.unity.com/?q=searchTerm&orderBy=1'
        # webbrowser.open('https://assetstore.unity.com/?q=' + unityPackFileNameVizgouthExt + '&orderBy=1', new=0)
        # get unity pack url from console input
        unityPackUrl = input('Enter unity pack url: ')

    # create grabber for unity pack
    grabber = UnityDescrFromAssetStoreGrabber(unityPackUrl)
    data = grabber.getDetails()
    # close browser
    # grabber.closeBrowser()
    data['localUrl'] = unityPackPath
    data['version'] = unityPackInfoParser.version

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    Notion_v2_token = os.getenv('NOTION_TOKEN', '')
    notion_db_id = 'bb9eeb6555994df4810ee2fc99b37a22'

    nh = NotionHelper(Notion_v2_token, notion_db_id)

    page, pagedata = nh.createUAPage(data)
    pageid = page['id']
    nh.image_append(pageid, data['imagesUrls'][0])
    print('__________________________')
    notionBlocks = nh.html_to_notion_rich_text(data['description'])

    text_appendPage = nh.append_child_block(pageid, notionBlocks)
    # append all images
    for image in data['imagesUrls']:
        nh.image_append(pageid, image)

    grabber.SavePackDetails(unityPackPath, data)
