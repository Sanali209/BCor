# Adapted from OpenAI's Vision example
import time

from openai import OpenAI
import base64
import requests

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Ask the user for a path on the filesystem:
path = r"E:\rawimagedb\repository\nsfv repo\drawn\_site rip\Reiq.ws + Jigglygirls.com\mix\Akame Ga Kill! - Esdeath 01 Clean.jpg"

# Read the image and encode it to base64:
base64_image = ""
try:
    image = open(path.replace("'", ""), "rb").read()
    base64_image = base64.b64encode(image).decode("utf-8")
except:
    print("Couldn't read the image. Make sure the path is correct and the file exists.")
    exit()
template = "This is a chat between a user and an assistant."
template1 = ("This is a chat between a user and an assistant. The assistant answers thu question in form"
             "XML file. where each question is a tag and the answer is the text inside the tag.")
completion = client.chat.completions.create(
    model="llava-v1.5-7b",
    messages=[
        {
            "role": "system",
            "content": template,
        },
        {
            "role": "user",
            "content": [

                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                }, {"type": "text", "text":
                    (r"chose one of category: 'not NSFW','NSFW','Ero','violent','gore' answer in JSON format:"
                        r"{'category':'chosen category'}"
                        r"{'description':'describe the image'}"
                        r"{'probability':'probability of the category'}")
                    },
            ],
        }
    ],
    max_tokens=1000,
    stream=True
)
start_time = time.time()
for chunk in completion:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print(f"Time taken: {time.time() - start_time:.2f} seconds")
