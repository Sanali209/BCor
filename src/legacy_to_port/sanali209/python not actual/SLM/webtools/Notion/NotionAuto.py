import os

import requests
from bs4 import BeautifulSoup
from notion_database.properties import Properties
from SLM.appGlue.DAL.DAL import GlueDataConverter
from notion_database.children import Children
from notion_database.page import Page


def html_to_childs_text(html):
    childs = Children()
    soup = BeautifulSoup(html, 'html.parser')
    # if html not contain <p> tag add it
    if not soup.find('p'):
        soup = BeautifulSoup(f'<p>{html}</p>', 'html.parser')

    for tag in soup.find_all():
        if tag.name == 'p':
            childs.set_paragraph(tag.text)

        if tag.name == 'img':
            childs.set_external_image(tag['src'])
        if tag.name == 'h1':
            childs.set_heading_1(tag.text)
        if tag.name == 'h2':
            childs.set_heading_2(tag.text)
        if tag.name == 'h3':
            childs.set_heading_3(tag.text)
        if tag.name == 'a':
            childs.set_bookmark(tag['href'])

    return childs



class NotionHelper:
    def __init__(self, token_v2, db_id):
        self.token_v2 = token_v2
        self.db_id = db_id
        self.propertyes = []
        self.PropertyesShema = []
        self.header = {'Authorization': f'Bearer {self.token_v2}', 'Notion-Version': '2021-05-13'}

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

    @staticmethod
    def record_from_object(obj, converter: GlueDataConverter):
        notion_record = converter.Convert(obj)
        return notion_record


class NotionDBManager:
    notion_db_id = ''
    Notion_v2_token = os.getenv('NOTION_V2_TOKEN')

class NotionDBRecord:
    def __init__(self, converter):
        self.id = ''
        self.converter = converter
        self.item_propertyes = Properties()
        self.children = Children()
        self.raw_children = []

    def create_page_db(self):
        npage = Page(NotionDBManager.Notion_v2_token)
        npage.create_page(database_id=NotionDBManager.notion_db_id, properties=self.item_propertyes, children=self.children)
        self.id = npage.result['id']

    def get_from_db(self, id, page, page_id):
        npage = Page(NotionDBManager.Notion_v2_token)
        npage.retrieve_page(page_id=id)
        helper = NotionHelper(NotionDBManager.Notion_v2_token, NotionDBManager.notion_db_id)
        self.id = page.result['id']
        item_propertyes = page.result['properties']
        self.raw_children = helper.getBlockChildren(page_id)['results']
        for property_key in item_propertyes:
            proptype = item_propertyes[property_key]['type']
            if proptype == 'title':
                self.item_propertyes.set_title(property_key,
                                               item_propertyes[property_key]['title'][0]['text']['content'])
            if proptype == 'select':
                self.item_propertyes.set_select(property_key, item_propertyes[property_key]['select']['name'])
            if proptype == 'url':
                self.item_propertyes.set_url(property_key, item_propertyes[property_key]['url'])
            if proptype == 'multi_select':
                self.item_propertyes.set_multi_select(property_key, item_propertyes[property_key]['multi_select'])
            if proptype == 'number':
                self.item_propertyes.set_number(property_key, item_propertyes[property_key]['number'])
            if proptype == 'date':
                self.item_propertyes.set_date(property_key, item_propertyes[property_key]['date']['start'])
            if proptype == 'checkbox':
                self.item_propertyes.set_checkbox(property_key, item_propertyes[property_key]['checkbox'])
            if proptype == 'email':
                self.item_propertyes.set_email(property_key, item_propertyes[property_key]['email'])
            if proptype == 'phone_number':
                self.item_propertyes.set_phone_number(property_key, item_propertyes[property_key]['phone_number'])
