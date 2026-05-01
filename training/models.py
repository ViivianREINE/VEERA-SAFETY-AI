import torch
import torch.nn as nn
import torchvision.models as models

class VideoSwinModel(nn.Module):
    def __init__(self, pretrained=True, embedding_dim=128):
        super(VideoSwinModel, self).__init__()
        self.backbone = models.video.r3d_18(pretrained=pretrained)
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        self.fc = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(512, embedding_dim),
        )

    def forward(self, x):
        features = self.backbone(x)
        embeddings = self.fc(features)
        return embeddings

class AudioCNNModel(nn.Module):
    def __init__(self, embedding_dim=128):
        super(AudioCNNModel, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(512, embedding_dim),
        )

    def forward(self, x):
        x = self.conv_layers(x)
        x = self.fc(x)
        return x

class MultimodalFusionModel(nn.Module):
    def __init__(self, video_model, audio_model, hidden_dim=128):
        super(MultimodalFusionModel, self).__init__()
        self.video_model = video_model
        self.audio_model = audio_model
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim * 2 if hasattr(video_model, 'fc') else 256, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.35),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, video_x, audio_x):
        vid_emb = self.video_model(video_x)
        aud_emb = self.audio_model(audio_x)
        combined = torch.cat((vid_emb, aud_emb), dim=1)
        out = self.classifier(combined)
        return out
