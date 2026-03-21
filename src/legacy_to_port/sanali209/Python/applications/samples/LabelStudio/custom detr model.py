# sample for training custom object detection model from custom cocoa dataset
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision
from torchvision.transforms import ToTensor
from torchvision.models import resnet18
from torchvision.models import resnet50
from pytorch_lightning import LightningModule, Trainer
import pytorch_lightning as pl
from PIL import Image
from datasets import load_from_disk
import json
from torch.utils.data import Dataset
from torchvision.transforms import ToTensor, Resize
from datasets import load_from_disk
import datasets
from PIL import Image
from pytorch_lightning import Trainer
from sklearn.model_selection import train_test_split
import random
import os
from torch.optim import Adam
import torch
from transformers import DetrForObjectDetection, DetrImageProcessor

HOME = os.getcwd()
# settings
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
CHECKPOINT = 'facebook/detr-resnet-50'
CONFIDENCE_TRESHOLD = 0.5
IOU_TRESHOLD = 0.8
# settings
MAX_EPOCHS = 50


image_processor = DetrImageProcessor.from_pretrained(CHECKPOINT)
model = DetrForObjectDetection.from_pretrained(CHECKPOINT)
model.to(DEVICE)

# Загрузка датасета
dataset_path = '/content/drive/MyDrive/rawdb/fraces/images'


class MyCDataset(torchvision.datasets.CocoDetection):
    def __init__(
            self,
            image_directory_path: str,
            image_processor,
            train: bool = True

    ):
        self.annotationFilename = 'result.json'
        annotation_file_path = os.path.join(image_directory_path, self.annotationFilename)
        super().__init__(image_directory_path, annotation_file_path)
        self.image_processor = image_processor

    def __getitem__(self, idx):
        images, annotations = super().__getitem__(idx)
        image_id = self.ids[idx]
        annotations = {'image_id': image_id, 'annotations': annotations}
        encoding = self.image_processor(images=images, annotations=annotations, return_tensors="pt")
        pixel_values = encoding["pixel_values"].squeeze()
        target = encoding["labels"][0]

        return pixel_values, target


my_dataset = MyCDataset(dataset_path,image_processor=image_processor)

# Получение списка индексов для разделения
num_samples = len(my_dataset)
indices = list(range(num_samples))

# Задание случайного семени (seed) для воспроизводимости
random.seed(42)

# Разделение на тренировочный и валидационный наборы данных
train_indices, val_indices = train_test_split(indices, test_size=0.1, random_state=42)

# Создание тренировочного и валидационного поднаборов
train_ds = torch.utils.data.Subset(my_dataset, train_indices)
val_ds = torch.utils.data.Subset(my_dataset, val_indices)


def collate_fn(batch):
    # DETR authors employ various imageView sizes during training, making it not possible
    # to directly batch together images. Hence they pad the images to the biggest
    # resolution in a given batch, and create a corresponding binary pixel_mask
    # which indicates which pixels are real/which are padding
    pixel_values = [item[0] for item in batch]
    encoding = image_processor.pad(pixel_values, return_tensors="pt")
    labels = [item[1] for item in batch]
    return {
        'pixel_values': encoding['pixel_values'],
        'pixel_mask': encoding['pixel_mask'],
        'labels': labels
    }


train_loader = DataLoader(train_ds, collate_fn=collate_fn, batch_size=4, shuffle=True)
val_loader = DataLoader(val_ds, collate_fn=collate_fn, batch_size=4)

# we will use id2label function for training
categories = my_dataset.coco.cats
id2label = {k: v['name'] for k, v in categories.items()}
label2id = {v: k for k, v in id2label.items()}


class Detr(pl.LightningModule):

    def __init__(self, lr, lr_backbone, weight_decay):
        super().__init__()
        self.model = DetrForObjectDetection.from_pretrained(
            pretrained_model_name_or_path=CHECKPOINT,
            num_labels=len(id2label),
            ignore_mismatched_sizes=True
        )

        self.lr = lr
        self.lr_backbone = lr_backbone
        self.weight_decay = weight_decay

    def forward(self, pixel_values, pixel_mask):
        return self.model(pixel_values=pixel_values, pixel_mask=pixel_mask)

    def common_step(self, batch, batch_idx):
        pixel_values = batch["pixel_values"]
        pixel_mask = batch["pixel_mask"]
        labels = [{k: v.to(self.device) for k, v in t.items()} for t in batch["labels"]]

        outputs = self.model(pixel_values=pixel_values, pixel_mask=pixel_mask, labels=labels)

        loss = outputs.loss
        loss_dict = outputs.loss_dict

        return loss, loss_dict

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        # logs metrics for each training_step, and the average across the epoch
        self.log("training_loss", loss)
        for k, v in loss_dict.items():
            self.log("train_" + k, v.item())

        return loss

    def validation_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        self.log("validation/loss", loss)
        for k, v in loss_dict.items():
            self.log("validation_" + k, v.item())

        return loss

    def configure_optimizers(self):
        # DETR authors decided to use different learning rate for backbone
        # you can learn more about it here:
        # - https://github.com/facebookresearch/detr/blob/3af9fa878e73b6894ce3596450a8d9b89d918ca9/main.py#L22-L23
        # - https://github.com/facebookresearch/detr/blob/3af9fa878e73b6894ce3596450a8d9b89d918ca9/main.py#L131-L139
        param_dicts = [
            {
                "params": [p for n, p in self.named_parameters() if "backbone" not in n and p.requires_grad]},
            {
                "params": [p for n, p in self.named_parameters() if "backbone" in n and p.requires_grad],
                "lr": self.lr_backbone,
            },
        ]
        return torch.optim.AdamW(param_dicts, lr=self.lr, weight_decay=self.weight_decay)

    def train_dataloader(self):
        return train_loader

    def val_dataloader(self):
        return val_loader


model = Detr(lr=1e-4, lr_backbone=1e-5, weight_decay=1e-4)
trainer = Trainer(devices=1, accelerator="gpu", max_epochs=MAX_EPOCHS, gradient_clip_val=0.1, accumulate_grad_batches=8, log_every_n_steps=5)

trainer.fit(model)


model.model.save_pretrained("detr_model")
# change labels config

filepath = '/content/model/config.json'

jsond = json.load(open(filepath))
jsond['id2label'] = id2label
jsond['label2id'] = label2id

with open(filepath, 'w') as f:
    json.dump(jsond, f , indent=4)





