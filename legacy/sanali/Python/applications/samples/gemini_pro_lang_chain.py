import langchain
from langchain_core.messages import HumanMessage

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)

import os




if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = 'AIzaSyB2n4fQmeKYpGId5qdWdClp1wHEnz0vQic'
# change models by need (gemini-pro, gemini-pro-vision)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-vision",maxOutputTokens=2048,safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,}
    )
messages = [HumanMessage(content=[
    {"type": "text",
     "text": "What's in this image?"},
    {"type": "image_url",
     "image_url": r"E:\rawimagedb\repository\nsfv repo\drawn\presort\_by races\Angelpic\mercy\00578.jpg"},
])]

result = llm.invoke(messages)
print(result.content)

