from tqdm import tqdm
from google.colab import drive
drive.mount('/content/drive')

import sys
sys.path.append('/content/drive/MyDrive/sanali209/Python'
from SLM.appGlue.DesignPaterns import allocator



from pyngrok import ngrok

!pip install pyngrok
# Authenticate ngrok with your token
!ngrok authtoken 2ZZAVvpErN4Mej39hJFSKYZy4pv_45ZWKZa7DXck2YiTRpzEh
# Expose the worker port (e.g., 8788)
public_url = ngrok.connect(8788)
print(f'Public URL: {public_url}')

config = allocator.Allocator.config
config.fileDataManager.path = r"D:\data\ImageDataManager"
config.mongoConfig.database_name = "files_db"
config.documentConfig.path = r"D:\data\ImageDataManager"
allocator.Allocator.init_services()

file_path = '/content/drive/MyDrive/rawdb/imcopy'
filelist = get_files(file_path, ['*.jpg', '*.png'])

tensor_cache = Embeddings_cache([CNN_Encoder_CLIP.format])
for file in tqdm(filelist):
    tensor_cache.get_by_path(file, CNN_Encoder_CLIP.format)
