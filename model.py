import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from params import *


class ContrastiveLoss(nn.Module):
    def __init__(self, margin=2.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, y):
        euclidean_distance = F.pairwise_distance(output1, output2)
        loss_contrastive = torch.mean((1 - y) * torch.pow(euclidean_distance, 2) +
                                       y * torch.pow(torch.clamp(self.margin -
                                        euclidean_distance, min=0., max=np.inf), 2))
        return loss_contrastive


class SiameseNetwork(nn.Module):
    def __init__(self):
        super(SiameseNetwork, self).__init__()
        self.cnn1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(2, stride=2),
            # 32x32
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(2, stride=2),
            # 16x16
            nn.Conv2d(64, 128, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(2, stride=2)
            # 6x6
        )

        self.fc1 = nn.Sequential(
            nn.Linear(128 * 6 * 6, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, 32)
        )

    def forward_once(self, x):
        output = self.cnn1(x)
        output = output.view(output.size()[0], -1)
        output = self.fc1(output)
        return output

    def forward(self, input1, input2):
        output1 = self.forward_once(input1)
        output2 = self.forward_once(input2)
        return output1, output2


class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.cnn1 = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=5, padding=2),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(16),
            nn.Conv2d(16, 16, kernel_size=5, padding=2),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(16),
            nn.Conv2d(16, 16, kernel_size=5, padding=2),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(16),
            nn.MaxPool2d(2, stride=2),
            # 48x48
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(2, stride=2),
            # 24x24
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(2, stride=2),
            # 12x12
            nn.Conv2d(64, 128, kernel_size=3),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=3),
            nn.SELU(inplace=True),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(2, stride=2),
            # 4x4

        )

        self.fc1 = nn.Sequential(
            nn.Linear(128 * 4 * 4, 512),
            nn.SELU(inplace=True),
            nn.Linear(512, 512),
            nn.SELU(inplace=True),
            nn.Linear(512, 2 * 27),
        )

    def forward(self, x):
        output = self.cnn1(x)
        output = output.view(output.size()[0], -1)
        output = self.fc1(output)
        return output


class AutoEncoder(nn.Module):
    def __init__(self):
        super(AutoEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(64 * 64 * 3, 256),
            nn.ReLU(True),
            nn.Linear(256, 64),
            nn.ReLU(True),
            nn.Linear(64, 32),
        )
        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(True),
            nn.Linear(64, 256),
            nn.ReLU(True),
            nn.Linear(256, 64 * 64 * 3)
        )

    def encode(self, x):
        x = self.encoder(x)
        return x

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x


class ConvolutionalAutoEncoder(nn.Module):
    def __init__(self):
        super(ConvolutionalAutoEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(True),
            nn.Conv2d(32, 32, 3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=2),
            # 12x12
            nn.Conv2d(32, 16, 3, padding=1),
            nn.ReLU(True),
            nn.Conv2d(16, 16, 3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=2),
            # 6x6
            nn.Conv2d(16, 8, 3, padding=1),
            nn.ReLU(True),
            nn.Conv2d(8, 8, 3, padding=1),
            # nn.ReLU(True),
            nn.MaxPool2d(2, stride=2)
            # 3x3
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(8, 16, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(True),
            # 6x6
            nn.Conv2d(16, 16, 3, padding=1),
            nn.ReLU(True),
            nn.ConvTranspose2d(16, 32, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(True),
            # 12x12
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 64, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(True),
            # 24x24
            nn.Conv2d(64, 3, 1),
            nn.ReLU(True),
        )

    def encode(self, x):
        x = self.encoder(x)
        return x

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x