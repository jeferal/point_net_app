import torch.nn as nn
from pointnet import PointNetClassification, PointNetLossForClassification

import torch
import numpy as np
import torch.nn.functional as F


class get_model(nn.Module):
    def __init__(self, num_points=1024, k=40, dropout=0.4):
        super(get_model, self).__init__()
        self.classificator = PointNetClassification(num_points, k, dropout)

    def forward(self, x):
        return self.classificator(x)


class get_loss(nn.Module):
    def __init__(self, regularization_weight=0.001, gamma=1):
        super(get_loss, self).__init__()
        self.loss_calculator = PointNetLossForClassification(regularization_weight=regularization_weight, gamma=gamma)
    
    def forward(self, pred, target, trans_feat):
        return self.loss_calculator(pred, target, trans_feat)
