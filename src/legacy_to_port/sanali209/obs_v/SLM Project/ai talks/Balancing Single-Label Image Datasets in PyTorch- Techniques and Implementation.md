#image_clasification #vision #resarch #dataset

  
Image dataset imbalance poses significant challenges for machine learning models, often leading to biased predictions favoring majority classes. This is particularly problematic when training models on single-label image datasets, where certain classes may be severely underrepresented. This report explores comprehensive approaches to balance image datasets in PyTorch, providing detailed implementation strategies and code examples for each technique.  
  
## Understanding Dataset Imbalance  
  
Imbalance in image datasets occurs when there is an unequal distribution of classes, typically with some classes being heavily overrepresented while others are underrepresented. This imbalance can significantly impact model performance, as the algorithm tends to be biased toward the majority class[1]. For example, in a dataset with 950 potato images and only 50 carrot images, a model that classifies all images as potatoes would still achieve 95% accuracy despite completely failing to identify carrots[1][8].  
  
This scenario demonstrates why accuracy alone is an insufficient metric for evaluating models trained on imbalanced datasets. Other metrics such as precision, recall, F1-score, and area under the ROC curve provide more meaningful insights into model performance across all classes[4].  
  
## Sampling-Based Techniques  
  
### Undersampling  
  
Undersampling reduces the number of instances in majority classes to balance the distribution. This technique works by selecting a subset of images from overrepresented classes and discarding the rest[1][8].  
  
Random undersampling is the simplest implementation, where images to be kept are chosen randomly. This approach is computationally efficient since it doesn't require complex calculations:  
  
```python  
# Using RandomUnderSampler from imblearn  
from imblearn.under_sampling import RandomUnderSampler  
import numpy as np  
  
# Reshape images for undersampling  
X_reshaped = X.reshape(X.shape[0], -1)  # Flatten images  
rus = RandomUnderSampler(random_state=42)  
X_resampled, y_resampled = rus.fit_resample(X_reshaped, y)  
  
# Reshape back to original dimensions  
X_resampled = X_resampled.reshape(-1, original_height, original_width, channels)  
```  
  
Undersampling is most effective when you have a very large dataset with similar images within each class. However, it comes with the risk of losing potentially valuable information from the discarded samples[1][8].  
  
### Oversampling  
  
Oversampling increases the representation of minority classes by duplicating existing images[1][8]. Unlike undersampling, this approach preserves all original data while adding duplicates of underrepresented classes.  
  
Random oversampling is straightforward to implement but may lead to overfitting since exact duplicates are added to the training set:  
  
```python  
# Using RandomOverSampler from imblearn  
from imblearn.over_sampling import RandomOverSampler  
  
# Reshape images for oversampling  
X_reshaped = X.reshape(X.shape[0], -1)  # Flatten images  
ros = RandomOverSampler(random_state=42)  
X_resampled, y_resampled = ros.fit_resample(X_reshaped, y)  
  
# Reshape back to original dimensions  
X_resampled = X_resampled.reshape(-1, original_height, original_width, channels)  
```  
  
This technique is best suited for datasets with a modest disparity between class sizes and where the minority class images are relatively similar to each other[8].  
  
### Weighted Random Sampling in PyTorch  
  
PyTorch provides the WeightedRandomSampler class, which assigns sampling probabilities inversely proportional to class frequencies:  
  
```python  
from torch.utils.data import DataLoader, WeightedRandomSampler  
import torch  
  
# Calculate class weights (inverse frequency)  
class_counts = [970, 3308, 2407, 212, 4422, 11424, 286, 594, 272]  # Example counts  
weights = 1.0 / (torch.FloatTensor(class_counts) + 1e-5)  # Adding small epsilon to avoid division by zero  
  
# Assign weight to each sample based on its class  
sample_weights = [weights[label] for label in train_dataset.targets]  
  
# Create the sampler  
sampler = WeightedRandomSampler(  
    weights=sample_weights,  
    num_samples=len(sample_weights),  
    replacement=True  
)  
  
# Create DataLoader with the sampler  
train_loader = DataLoader(  
    train_dataset,  
    batch_size=32,  
    sampler=sampler,  
    num_workers=4  
)  
```  
  
The "replacement" parameter determines whether sampling is done with replacement (allowing the same sample to be drawn multiple times) or without replacement[5].  
  
### ImbalancedDatasetSampler  
  
The ImbalancedDatasetSampler is a custom PyTorch sampler specifically designed to handle imbalanced datasets by automatically estimating sampling weights:  
  
```python  
from imbalanced_dataset_sampler import ImbalancedDatasetSampler  
  
train_loader = torch.utils.data.DataLoader(  
    train_dataset,  
    sampler=ImbalancedDatasetSampler(train_dataset),  
    batch_size=32,  
    num_workers=4  
)  
```  
  
This sampler offers several advantages:  
- Automatically rebalances class distributions during sampling  
- Estimates sampling weights without manual calculation  
- Avoids creating a new balanced dataset in memory  
- Mitigates overfitting when used alongside data augmentation techniques[7]  
  
## Data Augmentation Techniques  
  
### Spatial Augmentation  
  
Spatial augmentation transforms the geometry of images while preserving class semantics. These techniques include flipping, rotating, cropping, and scaling[8]:  
  
```python  
import torchvision.transforms as transforms  
  
transform = transforms.Compose([  
    transforms.RandomResizedCrop(size=224, scale=(0.4, 1.6), ratio=(0.9, 1.1)),  
    transforms.RandomVerticalFlip(),  
    transforms.RandomHorizontalFlip(),  
    transforms.RandomRotation(15),  
    transforms.ToTensor()  
])  
  
# Apply to minority classes  
augmented_dataset = YourDataset(root_dir, transform=transform)  
```  
  
### Pixel Augmentation  
  
Pixel augmentation modifies color properties and pixel values, creating variations that help the model generalize better:  
  
```python  
transform = transforms.Compose([  
    transforms.ColorJitter(brightness=0.1, saturation=0.1, contrast=0.1, hue=0.3),  
    transforms.GaussianBlur(kernel_size=3),  
    transforms.ToTensor()  
])  
```  
  
When combined with oversampling, augmentation creates more diverse synthetic examples instead of exact duplicates, reducing the risk of overfitting[5][8].  
  
## Loss Function Modifications  
  
### Focal Loss  
  
Focal Loss is designed specifically for imbalanced datasets by modifying the cross-entropy loss to focus on hard-to-classify examples:  
  
```python  
class FocalLoss(nn.Module):  
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):  
        super(FocalLoss, self).__init__()  
        self.alpha = alpha  # Class weight parameter  
        self.gamma = gamma  # Focusing parameter  
        self.reduction = reduction  
  
    def forward(self, inputs, targets):  
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')  
        pt = torch.exp(-ce_loss)  
        focal_loss = (1 - pt) ** self.gamma * ce_loss  
  
        if self.alpha is not None:  
            alpha_weight = self.alpha[targets]  
            focal_loss = alpha_weight * focal_loss  
  
        if self.reduction == 'mean':  
            return focal_loss.mean()  
        elif self.reduction == 'sum':  
            return focal_loss.sum()  
        else:  
            return focal_loss  
```  
  
Focal Loss introduces two key parameters:  
- Gamma (γ): Reduces the loss contribution from well-classified examples  
- Alpha (α): Adjusts the weight of each class based on frequency[6]  
  
This loss function works effectively for binary, multi-class, and multi-label classification tasks[6].  
  
### Class-Weighted Loss Functions  
  
Standard loss functions can be modified by introducing class weights:  
  
```python  
# Calculate class weights (inverse frequency)  
class_counts = torch.tensor([970, 3308, 2407, 212, 4422, 11424, 286, 594, 272])  
class_weights = 1.0 / (class_counts / class_counts.sum())  
class_weights = class_weights / class_weights.sum()  # Normalize  
  
# Create weighted loss function  
criterion = nn.CrossEntropyLoss(weight=class_weights)  
```  
  
## Advanced Synthetic Sample Generation  
  
### SMOTE for Image Data  
  
Synthetic Minority Oversampling Technique (SMOTE) generates synthetic examples for minority classes by interpolating between existing samples. Since SMOTE works with feature vectors rather than directly with images, the image data must be reshaped:  
  
```python  
from imblearn.over_sampling import SMOTE  
  
# Reshape images to 2D format (samples, features)  
X_reshaped = X.reshape(X.shape[0], -1)  
  
# Apply SMOTE  
smote = SMOTE(random_state=42)  
X_resampled, y_resampled = smote.fit_resample(X_reshaped, y)  
  
# Reshape back to image format  
X_resampled = X_resampled.reshape(-1, height, width, channels)  
```  
  
SMOTE works by creating synthetic samples along the line segments connecting minority class instances[2][3]. For image data, this can create plausible new examples without exact duplication.  
  
### GAN-Based Approaches  
  
Generative Adversarial Networks (GANs) can generate entirely new synthetic images for minority classes:  
  
```python  
# Using a pre-trained GAN to generate synthetic minority class examples  
# This is a simplified representation  
generator = YourPretrainedGenerator()  
synthetic_images = generator.generate(num_samples=1000, target_class=minority_class_id)  
  
# Combine with original dataset  
augmented_dataset = CombinedDataset(original_dataset, synthetic_images)  
```  
  
While more complex to implement, GANs can produce high-quality, diverse synthetic examples that may be more realistic than simple augmentations. However, research suggests that traditional methods like SMOTE and random oversampling may still perform better in many cases and are computationally less expensive[4].  
  
## Ensemble Learning Approaches  
  
Ensemble methods combine multiple models to improve performance on imbalanced datasets:  
  
```python  
# Training an ensemble of models with different sampling strategies  
models = []  
  
# Model with undersampling  
train_loader_under = DataLoader(dataset, sampler=UnderSamplingSampler(...))  
model_under = YourModel()  
train_model(model_under, train_loader_under)  
models.append(model_under)  
  
# Model with oversampling  
train_loader_over = DataLoader(dataset, sampler=OverSamplingSampler(...))  
model_over = YourModel()  
train_model(model_over, train_loader_over)  
models.append(model_over)  
  
# Ensemble prediction  
def ensemble_predict(models, input):  
    predictions = [model(input) for model in models]  
    return torch.mean(torch.stack(predictions), dim=0)  
```  
  
## Conclusion  
  
Balancing single-label image datasets is crucial for developing unbiased models with strong performance across all classes. PyTorch offers various tools and techniques to address class imbalance issues effectively.  
  
The choice of method depends on several factors, including dataset size, degree of imbalance, and computational resources. For large datasets with similar images within classes, undersampling can be effective. For smaller datasets where data loss is a concern, oversampling combined with augmentation provides good results. Loss function modifications like Focal Loss offer an alternative approach that doesn't require changing the dataset itself.  
  
In practice, combining multiple techniques often yields the best results. For example, using ImbalancedDatasetSampler with data augmentation can provide balanced batches of diverse images, while Focal Loss can further focus the learning on challenging examples. The optimal solution typically requires experimentation with different approaches and careful evaluation using metrics beyond accuracy.  
  
Citations:  
[1] https://www.advancinganalytics.co.uk/blog/2023/2/2/image-classification-dealing-with-imbalance-in-datasets  
[2] https://stackoverflow.com/questions/48532069/how-to-oversample-image-dataset-using-python  
[3] https://datascience.stackexchange.com/questions/62759/how-do-i-run-smote-on-image-data-using-the-packages-available  
[4] https://www.sciencedirect.com/science/article/pii/S0957417423032803  
[5] https://discuss.pytorch.org/t/proper-way-of-using-weightedrandomsampler/73147  
[6] https://github.com/itakurah/Focal-loss-PyTorch  
[7] https://github.com/dakomura/imbalanced_dataset_sampler  
[8] https://www.advancinganalytics.co.uk/blog/2023/2/2/image-classification-dealing-with-imbalance-in-datasets  
[9] https://github.com/moskomule/mixup.pytorch  
[10] https://github.com/hysts/pytorch_cutmix  
[11] https://github.com/63days/augmix  
[12] https://pytorch.org/vision/stable/generated/torchvision.transforms.RandAugment.html  
[13] https://wandb.ai/authors/class-imbalance/reports/Simple-Ways-to-Tackle-Class-Imbalance--VmlldzoxODA3NTk  
[14] https://discuss.pytorch.org/t/how-to-use-weightedrandomsampler-for-imbalanced-data/110578  
[15] https://www.maskaravivek.com/post/pytorch-weighted-random-sampler/  
[16] https://pytorch.org/vision/main/generated/torchvision.transforms.v2.MixUp.html  
[17] https://www.picsellia.com/post/improve-imbalanced-datasets-in-computer-vision  
[18] https://www.maskaravivek.com/post/pytorch-weighted-random-sampler/  
[19] https://blog.paperspace.com/class-imbalance-in-image-datasets/  
[20] https://pytorch.org/vision/master/auto_examples/transforms/plot_cutmix_mixup.html  
[21] https://www.tensorflow.org/tutorials/structured_data/imbalanced_data  
[22] https://github.com/open-mmlab/mmsegmentation/issues/3104  
[23] https://blog.paperspace.com/class-imbalance-in-image-datasets/  
[24] https://www.maskaravivek.com/post/pytorch-weighted-random-sampler/  
[25] https://discuss.pytorch.org/t/are-the-class-weights-of-the-ce-loss-optimizble/178893  
[26] https://pypi.org/project/focal-loss-pytorch/  
[27] https://proceedings.mlr.press/v154/nazari21a/nazari21a.pdf  
[28] https://www.linkedin.com/pulse/some-tricks-handling-imbalanced-dataset-image-m-farhan-tandia  
[29] https://github.com/Bushramjad/Image-classification-with-unbalanced-classes  
[30] https://www.reddit.com/r/Python/comments/nrx8fv/how_to_apply_smote_function_to_my_image_dataset/  
[31] https://pmc.ncbi.nlm.nih.gov/articles/PMC11300732/  
[32] https://discuss.pytorch.org/t/proper-way-of-using-weightedrandomsampler/73147  
[33] https://www.reddit.com/r/pytorch/comments/1ehyxib/q_weighted_loss_function_pytorchs/  
[34] https://pypi.org/project/focal-loss-torch/  
[35] https://www.sciencedirect.com/science/article/abs/pii/S0952197624000927  
[36] https://www.kaggle.com/general/304848  
[37] https://discuss.pytorch.org/t/how-does-weightedrandomsampler-work/8089  
[38] https://discuss.pytorch.org/t/is-this-a-correct-implementation-for-focal-loss-in-pytorch/43327  
[39] https://discuss.pytorch.org/t/how-to-implement-oversampling-in-cifar-10/16964  
[40] https://github.com/chingisooinar/SMOTE-Pytorch  
[41] https://stackoverflow.com/questions/60812032/using-weightedrandomsampler-in-pytorch  
[42] https://discuss.pytorch.org/t/passing-the-weights-to-crossentropyloss-correctly/14731  
[43] https://pypi.org/project/unified-focal-loss-pytorch/  
[44] https://stackoverflow.com/questions/65017452/oversampling-the-dataset-with-pytorch  
[45] https://discuss.pytorch.org/t/performance-of-smote-on-cifar10-dataset/112541  
[46] https://www.youtube.com/watch?v=3GVUzwXXihs  
[47] https://github.com/justinengelmann/GANbasedOversampling  
[48] https://www.restack.io/p/data-augmentation-mixup-answer-cat-ai  
[49] https://pytorch.org/vision/0.16/generated/torchvision.transforms.v2.CutMix.html  
[50] https://pytorch.org/vision/main/generated/torchvision.transforms.AutoAugment.html  
[51] https://pytorch.org/vision/main/generated/torchvision.transforms.AugMix.html  
[52] https://www.youtube.com/watch?v=4JFVhJyTZ44  
[53] https://www.youtube.com/watch?v=hGAKHKqmXdY  
[54] https://pytorch.org/vision/master/generated/torchvision.transforms.v2.CutMix.html  
[55] https://pytorch.org/vision/main/generated/torchvision.transforms.v2.AutoAugment.html  
[56] https://torchaug.readthedocs.io/en/latest/generated/torchaug.transforms.AugMix.html  
[57] https://www.baeldung.com/cs/pytorch-generative-adversarial-networks  
[58] https://paperswithcode.com/paper/mixup-beyond-empirical-risk-minimization  
[59] https://dev.to/hyperkai/randaugment-in-pytorch-3-54k2  
[60] https://github.com/ildoonet/pytorch-randaugment/blob/master/RandAugment/data.py  
[61] https://timm.fast.ai/RandAugment  
[62] https://imgaug.readthedocs.io/en/latest/source/overview/collections.html  
[63] https://dev.to/hyperkai/randaugment-in-pytorch-4-5cnh  
[64] https://paperswithcode.com/paper/randaugment-practical-data-augmentation-with  
[65] https://github.com/locuslab/convmixer-cifar10/issues/1  
[66] https://pytorch.org/vision/main/transforms.html  
[67] https://pytorchvideo.readthedocs.io/en/latest/_modules/pytorchvideo/transforms/rand_augment.html  
[68] https://github.com/adam-mehdi/MuarAugment/blob/master/RandAugmentTutorial.ipynb  
[69] https://github.com/leehomyc/mixup_pytorch  
[70] https://www.restack.io/p/pytorch-mixup-answer-deep-learning-cat-ai  
[71] https://pytorch.ac.cn/vision/stable/generated/torchvision.transforms.AutoAugment.html  
[72] https://pytorch.org/vision/main/generated/torchvision.transforms.v2.RandAugment.html  
[73] https://github.com/ildoonet/pytorch-randaugment  
[74] https://sebastianraschka.com/blog/2023/data-augmentation-pytorch.html  
[75] https://pytorch.ac.cn/vision/0.20/generated/torchvision.transforms.RandAugment.html  
[76] https://pytorch.org/vision/main/generated/torchvision.transforms.RandAugment.html  
[77] https://dev.to/hyperkai/randaugment-in-pytorch-1-4dpn  
[78] https://docs.mosaicml.com/projects/composer/en/stable/method_cards/randaugment.html  
  
---  
Answer from Perplexity: pplx.ai/share  
  
To address class imbalance in multi-label classification with PyTorch, implement these key strategies:  
  
## **Sampling Techniques**  
1. **Label-Based Resampling**  
   Use `ML-ROS` (oversampling instances with rare labels) or `ML-RUS` (undersampling instances with frequent labels) based on label frequencies rather than full label combinations[1][2]. Implement via:  
  
```python  
# Using PyTorch's WeightedRandomSampler  
class_weights = 1.0 / torch.tensor(label_frequencies)  
sample_weights = [class_weights[labels[i].bool()].mean() for i in range(len(data))]  
sampler = WeightedRandomSampler(sample_weights, num_samples=len(data), replacement=True)  
```  
  
2. **Balanced Multi-Label Samplers**  
   Leverage specialized PyTorch packages like `pytorch-multilabel-balanced-sampler`, offering:  
   - `ClassCycleSampler`: Cycles through each class for balanced coverage[4]  
   - `LeastSampledClassSampler`: Prioritizes underrepresented labels[4]  
  
## **Loss Modifications**  
1. **Distribution-Balanced Loss**  
   Combines re-weighting and negative-tolerant regularization:  
```python  
class DistributionBalancedLoss(nn.Module):  
    def __init__(self, class_freq):  
        super().__init__()  
        self.weights = 1.0 / (class_freq ** 0.5)  # Square root dampening  
  
    def forward(self, inputs, targets):  
        loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')  
        return (loss * self.weights.to(inputs.device)).mean()  
```  
  
2. **Focal Loss Adaptation**  
   Applies focus parameter γ to hard examples:  
```python  
class MultiLabelFocalLoss(nn.Module):  
    def __init__(self, gamma=2):  
        super().__init__()  
        self.gamma = gamma  
  
    def forward(self, inputs, targets):  
        BCE_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')  
        pt = torch.exp(-BCE_loss)  
        return ((1-pt)**self.gamma * BCE_loss).mean()  
```  
  
## **Synthetic Generation**  
- **Label-Specific SMOTE**: Generate synthetic samples for rare labels after converting images to feature vectors[1][3]. Use `imblearn`'s `SMOTE` with flattened image features.  
  
## **Ensemble Strategies**  
Combine multiple models trained with different balancing approaches:  
```python  
# Example ensemble using varied samplers  
models = {  
    'oversampled': Model(train_loader=oversampled_loader),  
    'focal_loss': Model(loss=MultiLabelFocalLoss()),  
    'weighted': Model(loss=DistributionBalancedLoss())  
}  
  
def ensemble_predict(input):  
    return torch.stack([m(input) for m in models.values()]).mean(0)  
```  
  
## **Key Considerations**  
- Use `MeanIR` or `CVIR` metrics to quantify imbalance severity[1][2]  
- Prefer heuristic undersampling (e.g., `MLeNN`) over random when possible[1]  
- For extreme imbalance (>1:1000), combine synthetic generation with loss re-weighting[6][7]  
  
These techniques address multi-label imbalance by simultaneously considering individual label frequencies and label co-occurrence patterns[1][6]. Implementation choices should be guided by dataset characteristics and computational constraints.  
  
Citations:  
[1] https://www.sciencedirect.com/science/article/abs/pii/S0031320321001527  
[2] https://sci-hub.se/downloads/2021-06-30/88/tarekegn2021.pdf  
[3] https://stackoverflow.com/questions/76498233/balancing-a-multilabel-dataset  
[4] https://github.com/issamemari/pytorch-multilabel-balanced-sampler  
[5] https://discuss.pytorch.org/t/multilabel-classification-with-class-imbalance/57345  
[6] https://www.kdnuggets.com/2023/03/multilabel-nlp-analysis-class-imbalance-loss-function-approaches.html  
[7] https://arxiv.org/pdf/1810.11612.pdf  
[8] https://stackoverflow.com/questions/58206286/multilabel-classification-with-class-imbalance-in-pytorch  
[9] https://stackoverflow.com/questions/72666962/how-to-handle-imbalanced-multi-label-dataset  
[10] https://paperswithcode.com/paper/balancing-methods-for-multi-label-text  
[11] https://annolive.com/how-to-build-balanced-datasets-for-multi-label-classification/  
[12] https://discuss.pytorch.org/t/multi-label-multi-class-class-imbalance/37573  
[13] https://discuss.pytorch.org/t/what-kind-of-loss-is-better-to-use-in-multilabel-classification/32203  
[14] https://pieriantraining.com/multilabel-image-classification-in-pytorch-a-guide/  
[15] https://github.com/Alibaba-MIIL/ASL  
[16] https://ojs.aaai.org/index.php/AAAI/article/view/10908/10767  
[17] https://www.kaggle.com/general/220189  
[18] https://discuss.pytorch.org/t/balancing-a-multilabel-dataset/182321  
[19] https://discuss.pytorch.org/t/balance-multilabel/117253  
[20] https://www.reddit.com/r/MachineLearning/comments/1ehyv6b/p_weighted_loss_function_pytorchs/  
[21] https://debuggercafe.com/deep-learning-architectures-for-multi-label-classification-using-pytorch/  
  
---  
Answer from Perplexity: pplx.ai/share