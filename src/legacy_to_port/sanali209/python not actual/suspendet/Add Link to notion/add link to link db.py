import os

from SLM.GPTAgents.app import AIChatAgent
from SLM.appGlue.DAL.DAL import GlueDataConverter
from dotenv import load_dotenv

from SLM.webtools.Notion.NotionAuto import NotionDBRecord, NotionDBManager, html_to_childs_text
from SLM.webtools.page_preview.web_page_preview import PreviewGenerator, get_first_words_count

import gradio as gr

load_dotenv()

NotionDBManager.notion_db_id = os.getenv('NOTION_DB_LINKS')
NotionDBManager.Notion_v2_token = os.getenv('NOTION_V2_TOKEN')


class dblink_to_notion_record(GlueDataConverter):

    def Convert(self, data) -> NotionDBRecord:
        link: Dblink = data
        notion_record = NotionDBRecord(self)
        notion_record.id = link.id
        notion_record.item_propertyes.set_url('URL', link.url)
        notion_record.item_propertyes.set_multi_select('Tags', link.tags)
        notion_record.item_propertyes.set_title('Name', link.name)
        notion_record.children = html_to_childs_text(link.text)
        return notion_record

    def ConvertBack(self, data) -> 'Dblink':
        notion_record = data
        link = Dblink()
        link.id = notion_record.id
        link.url = notion_record.item_propertyes['URL']['url']
        link.category = notion_record.item_propertyes['category']['select']['name']
        link.name = notion_record.item_propertyes['Name']['title'][0]['text']['content']
        # link.text = notion_record.children.to_html()
        return link


# todo: refactor for use pydantic
class Dblink:
    def __init__(self):
        self.id = ''
        self.url = ''
        self.category = ''
        self.name = ''
        self.description = ''
        self.text = ''
        self._tags = []

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    def OnTagsChanged(self):
        pass


ai = AIChatAgent()

rules = """extract tag list from text by rules: 
            1. separate tag by a comma
            2. on start of created list write 'tags:'
            3. Do not add any decorator to tag the start
            4. use only small letters
            5. sample of created text - tags:tag1, tag2, tag3
            6. give me only tags, not any other text
            """
ai.rules = rules
web_page_preview = PreviewGenerator()


def url_data_get(url):
    preview_data = web_page_preview.get_preview(url, use_cache=True)

    hashed_item = preview_data['hashed']
    # tags_text = ''
    # if not hashed_item:
    #     context = link.name + " " + link.description
    #     answer = ai.get_response("Text:"+promt+"End Text"+"/n"+context)
    #     tags_text = answer
    #     preview_data['tags'] = tags_text
    #     web_page_preview.update_hash_value(preview_data)
    # else:
    #     tags_text = preview_data['tags']
    fulltext = preview_data.get('full text', '')
    text = preview_data['title'] + " " + preview_data['description']+" " + fulltext

    text = get_first_words_count(text, 500)

    answer = ai.get_response_rules(text)
    tags_text = answer
    preview_data['tags'] = tags_text.replace('tags:', '')
    web_page_preview.update_hash_value(preview_data)
    if preview_data['image_url'] is None or preview_data['image_url'] == '':
        preview_data['image_url'] = 'https://static-00.iconduck.com/assets.00/no-image-icon-512x512-lfoanl0w.png'

    return preview_data['title'], preview_data['description'], preview_data['image_url'],preview_data['image_url'], preview_data['tags']


def send_to_notion(url,title, description, image, tags):
    link = Dblink()
    link.url = url
    link.name = title
    link.description = description
    link.text = f'<img src="{image}"><p>{link.description}</p>'
    link.tags = tags.split(',')
    converter = dblink_to_notion_record()
    notion_record = converter.Convert(link)
    notion_record.create_page_db()
    return "ok"

css_style = ".image_up {height: 300px !important} "

with gr.Blocks(css=css_style) as gui:
    gui.title = "Add link to notion"
    marckdown_descr = gr.Markdown(value="## Add link to notion. [link get service](https://my.linkpreview.net/access_keys)")
    link_url = gr.Textbox(label="link url")
    with gr.Row():
        with gr.Column():
            image = gr.Image(label="image",elem_id="image_up")
            image_url = gr.Textbox(label="image url")
        with gr.Column():
            title = gr.Textbox(label="title")
            description = gr.Textbox(label="description")
            tags = gr.Textbox(label="tags")

    get_link_data = gr.Button(value="get link data")
    get_link_data.click(fn=url_data_get, inputs=[link_url], outputs=[title, description, image_url,image, tags])
    send_to_notion_button = gr.Button(value="send to notion")
    log = gr.Textbox(label="log", lines=10, readonly=True)
    send_to_notion_button.click(fn=send_to_notion, inputs=[link_url,title, description, image_url, tags], outputs=[log])



url_data_get('https://cgpersia.com/2022/08/artstation-brick-bundle-185743.html')
