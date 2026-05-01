import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
import numpy as np

from dataset_loader import MultimodalPanicDataset
from models import VideoSwinModel, AudioCNNModel, MultimodalFusionModel

# ----------------------------
# Weighted Focal Loss for Imbalance
# ----------------------------
class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, reduce=True):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduce = reduce

    def forward(self, inputs, targets):
        # inputs are probabilities from sigmoid
        BCE_loss = nn.BCELoss(reduction='none')(inputs, targets.view(-1, 1))
        pt = torch.exp(-BCE_loss)
        F_loss = self.alpha * (1-pt)**self.gamma * BCE_loss

        if self.reduce:
            return torch.mean(F_loss)
        else:
            return F_loss

def train_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Dummy data structure for illustration - Replace with actual globbing of datasets
    train_data_list = [
        {'video_path': 'data/video/v1.mp4', 'audio_path': 'data/audio/a1.wav', 'label': 1},
        {'video_path': 'data/video/v2.mp4', 'audio_path': 'data/audio/a2.wav', 'label': 0},
    ] * 10 # Mock expansion

    # Calculate class weights for oversampling
    labels = [d['label'] for d in train_data_list]
    class_sample_count = np.array([len(np.where(labels == t)[0]) for t in np.unique(labels)])
    weight = 1. / class_sample_count
    samples_weight = np.array([weight[t] for t in labels])
    samples_weight = torch.from_numpy(samples_weight).double()
    sampler = WeightedRandomSampler(samples_weight, len(samples_weight))

    # Dataset and Loader
    dataset = MultimodalPanicDataset(train_data_list)
    dataloader = DataLoader(dataset, batch_size=4, sampler=sampler, num_workers=2)

    # Initialize Models
    vid_model = VideoSwinModel(pretrained=True)
    aud_model = AudioCNNModel()
    model = MultimodalFusionModel(vid_model, aud_model).to(device)

    # Optimizer & Loss
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    criterion = FocalLoss(alpha=0.75, gamma=2)

    # Training Loop
    epochs = 10
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        correct = 0
        total = 0
        
        for batch in dataloader:
            video = batch['video'].to(device)
            audio = batch['audio'].to(device)
            labels = batch['label'].to(device)

            optimizer.zero_grad()
            outputs = model(video, audio)
            
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            preds = (outputs >= 0.5).float()
            correct += (preds.view(-1) == labels.view(-1)).sum().item()
            total += labels.size(0)
            
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {epoch_loss/len(dataloader):.4f}, Accuracy: {100*correct/total:.2f}%")

    print("Training complete. Saving model...")
    torch.save(model.state_dict(), 'multimodal_panic_model.pth')

if __name__ == '__main__':
    # train_model()
    print("Training script ready. Point 'train_data_list' to your actual downloaded dataset paths to run.")
