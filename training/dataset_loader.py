import json
import os
import random
from pathlib import Path

import cv2
import torch
import torchaudio
import torchvision.transforms as transforms
from torch.utils.data import Dataset

LABEL_KEYWORDS = {
    "panic": 1,
    "fight": 1,
    "violence": 1,
    "assault": 1,
    "riot": 1,
    "abuse": 1,
    "crowd": 1,
    "normal": 0,
    "non-violence": 0,
    "safe": 0,
    "calm": 0,
    "none": 0,
}

VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
AUDIO_EXTENSIONS = {"wav", "mp3", "flac", "ogg", "m4a", "aac"}

class MultimodalPanicDataset(Dataset):
    def __init__(
        self,
        data_list,
        num_frames=16,
        img_size=224,
        sample_rate=16000,
        max_audio_len=64000,
    ):
        self.data_list = data_list
        self.num_frames = num_frames
        self.img_size = img_size
        self.sample_rate = sample_rate
        self.max_audio_len = max_audio_len

        self.video_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((self.img_size, self.img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.mel_spectrogram = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=1024,
            hop_length=512,
            n_mels=64,
        )
        self.amplitude_to_db = torchaudio.transforms.AmplitudeToDB()

    def __len__(self):
        return len(self.data_list)

    def _load_video_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        frames = []
        total_frames = max(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
        step = max(total_frames // self.num_frames, 1)

        index = 0
        while cap.isOpened() and len(frames) < self.num_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if index % step == 0:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = self.video_transform(frame)
                frames.append(frame)
            index += 1
        cap.release()

        while len(frames) < self.num_frames:
            frames.append(frames[-1] if frames else torch.zeros(3, self.img_size, self.img_size))

        frames = torch.stack(frames).permute(1, 0, 2, 3)
        return frames

    def _load_audio(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return torch.zeros(1, 64, 126)

        waveform, sr = torchaudio.load(audio_path)
        if sr != self.sample_rate:
            waveform = torchaudio.functional.resample(waveform, orig_freq=sr, new_freq=self.sample_rate)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if waveform.shape[1] > self.max_audio_len:
            waveform = waveform[:, : self.max_audio_len]
        else:
            padding = self.max_audio_len - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))

        mel = self.mel_spectrogram(waveform)
        mel = self.amplitude_to_db(mel)
        return mel

    def __getitem__(self, idx):
        item = self.data_list[idx]
        video_tensor = self._load_video_frames(item["video_path"])
        audio_tensor = self._load_audio(item.get("audio_path"))
        label = torch.tensor(item["label"], dtype=torch.float32)
        return {"video": video_tensor, "audio": audio_tensor, "label": label}

    @staticmethod
    def extract_files(root_dir, extensions):
        root = Path(root_dir)
        files = []
        for ext in extensions:
            files.extend(root.rglob(f"*.{ext}"))
        return [str(f) for f in sorted(files)]

    @classmethod
    def infer_label_from_path(cls, path):
        lowered = path.lower()
        for keyword, label in LABEL_KEYWORDS.items():
            if keyword in lowered:
                return label
        return 0

    @classmethod
    def build_manifest(cls, video_dirs, audio_dirs=None, output_path=None, max_samples=None):
        video_paths = []
        for directory in video_dirs:
            video_paths.extend(cls.extract_files(directory, VIDEO_EXTENSIONS))

        audio_paths = []
        if audio_dirs:
            for directory in audio_dirs:
                audio_paths.extend(cls.extract_files(directory, AUDIO_EXTENSIONS))

        manifest = []
        for idx, video_path in enumerate(video_paths):
            label = cls.infer_label_from_path(video_path)
            audio_path = None
            if audio_paths:
                audio_path = audio_paths[min(idx, len(audio_paths) - 1)]
            manifest.append({"video_path": video_path, "audio_path": audio_path, "label": label})
            if max_samples and len(manifest) >= max_samples:
                break

        random.shuffle(manifest)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle, indent=2)
        return manifest

    @staticmethod
    def load_manifest(json_path):
        with open(json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
