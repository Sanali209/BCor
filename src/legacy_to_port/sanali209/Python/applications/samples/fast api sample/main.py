import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import base64
import uuid
from PIL import Image

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/generate_image")
def generate_image():
    # Generate an image
    img = Image.new("RGB", (100, 100), "blue")

    # Save the image with a unique ID
    image_id = str(uuid.uuid4())
    img_path = f"static/images/{image_id}.png"
    img.save(img_path)

    # Convert the image to base64
    with open(img_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Return JSON response with image ID and base64 encoded image
    return JSONResponse(content={"image_id": image_id, "image_data": encoded_image})



if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="127.0.0.1")
