#  Copyright (c) 2023. Dynatrace LCC. All Rights Reserved.

#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied. See the License for the specific language governing
#  permissions and limitations under the License.

import numpy as np
import pytorch_lightning as pl
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from pytorch_lightning.callbacks import ModelCheckpoint
from sklearn import metrics as sk_metrics
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, TensorDataset

from sm_backend.models.surrogate_model import SurrogateModel


class PytorchLightningProbLogisticRegression(SurrogateModel):

    def __init__(self,
                 features=None,
                 labels=None) -> None:
        self.features = features
        self.labels = labels
        self.ann_model = None
        self.fold = 5
        self.all_metrics = None

    def apply(self, features, labels, fold=5):

        if features.equals(self.features) and labels.round(3).equals(
                self.labels.round(3)) and self.ann_model is not None and self.fold == fold:
            print('Model already trained')
            return self.all_metrics

        self.features = features
        self.labels = labels
        self.fold = fold

        # Transform the data
        features = torch.tensor(features.values, dtype=torch.float32)
        labels = torch.tensor(labels.values, dtype=torch.float32)

        # Define PyTorch Lightning Module
        # Prepare DataLoader
        train_dataset = TensorDataset(features, labels)
        train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

        # Instantiate LightningANN model
        input_size = features.size(1)
        hidden_size1 = 128
        hidden_size2 = 64
        output_size = len(labels[0])
        epochs = 15
        n_splits = self.fold

        # Initialize Stratified K-Fold
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        self.all_metrics = []  # Array to store metrics for each fold

        for fold, (train_idx, val_idx) in enumerate(skf.split(features, torch.argmax(labels, dim=-1).numpy())):
            print('Fold ' + str(fold))
            # Split data into train and validation sets
            train_features, train_labels = features[train_idx], labels[train_idx]
            val_features, val_labels = features[val_idx], labels[val_idx]

            # Prepare DataLoader
            train_dataset = TensorDataset(train_features, train_labels)
            train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

            val_dataset = TensorDataset(val_features, val_labels)
            val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

            # Instantiate LightningANN model
            self.ann_model = LightningANN(input_size, hidden_size1, hidden_size2, output_size)

            # Instantiate PyTorch Lightning Trainer
            checkpoint_callback = ModelCheckpoint(mode="max")
            trainer = pl.Trainer(
                devices="auto",
                accelerator="cpu",  # CPUs or GPUs
                max_epochs=epochs,
                logger=None,
                deterministic=True,
                callbacks=[checkpoint_callback],
            )

            # Train the model
            trainer.fit(self.ann_model, train_loader)

            # Validate the model on the validation set
            val_metrics = trainer.test(self.ann_model, val_loader)[0]
            self.all_metrics.append(val_metrics)

        # Finally fit all data
        # Prepare DataLoader
        train_dataset = TensorDataset(features, labels)
        train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

        # Instantiate LightningANN model
        self.ann_model = LightningANN(input_size, hidden_size1, hidden_size2, output_size)

        # Instantiate PyTorch Lightning Trainer
        checkpoint_callback = ModelCheckpoint(mode="max")
        trainer = pl.Trainer(
            devices="auto",
            accelerator="cpu",  # CPUs or GPUs
            max_epochs=epochs,
            logger=None,
            deterministic=True,
            callbacks=[checkpoint_callback],
        )

        # Train the model
        trainer.fit(self.ann_model, train_loader)

        print('Fitting Done')
        print(self.all_metrics)
        return self.all_metrics

    # def predict(self, features):
    #     features = torch.tensor(features.values, dtype=torch.float32)
    #
    #     # Evaluate the model
    #     self.ann_model.eval()
    #     with torch.no_grad():
    #         predictions = self.ann_model(features),
    #
    #     # Convert the predictions to numpy array
    #     predictions_np = predictions[0].numpy()
    #
    #     print(predictions_np[:5])
    #
    #     # For binary classification, you can get the predicted class (0 or 1) as follows:
    #     predicted_class = np.argmax(predictions_np, axis=1)
    #
    #     return predicted_class.tolist()

    def predict(self, features, num_samples=10):
        features = torch.tensor(features.values, dtype=torch.float32)
        predictions = []

        # Enable dropout during inference for Bayesian approximation
        self.ann_model.train()
        for _ in range(num_samples):
            with torch.no_grad():
                predictions.append(F.softmax(self.ann_model(features), dim=1).numpy())

        # Average the predictions from all samples
        mean_predictions = np.mean(predictions, axis=0)
        predicted_class = np.argmax(mean_predictions, axis=1)
        return predicted_class.tolist()


class LightningANN(pl.LightningModule):
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size, learning_rate=0.001):
        super(LightningANN, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_size, hidden_size1),
            nn.ReLU(),
            nn.Dropout(0.1),  # Dropout layer for Bayesian approximation
            nn.Linear(hidden_size1, hidden_size2),
            nn.ReLU(),
            nn.Dropout(0.1),  # Another Dropout layer
            nn.Linear(hidden_size2, output_size)
        )
        self.criterion = nn.CrossEntropyLoss()
        self.learning_rate = learning_rate

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_pred = self(x)
        loss = self.criterion(y_pred, y)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_pred = self(x)
        loss = self.criterion(y_pred, y)
        acc = sk_metrics.accuracy_score(y.cpu().numpy(), torch.argmax(y_pred, dim=-1).cpu().numpy())
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_acc', acc, prog_bar=True)
        return loss

    def test_step(self, batch, batch_idx):
        x, y = batch
        y_pred = self(x)
        loss = self.criterion(y_pred, y)

        # Convert predictions and labels to numpy arrays
        y_pred_np = torch.argmax(y_pred, dim=-1).cpu().numpy()
        y_np = torch.argmax(y, dim=-1).cpu().numpy()

        acc = sk_metrics.accuracy_score(y_np, y_pred_np)
        precision = sk_metrics.precision_score(y_np, y_pred_np, average='weighted')
        recall = sk_metrics.recall_score(y_np, y_pred_np, average='weighted')

        # Log metrics
        self.log('test_loss', loss, prog_bar=True)
        self.log('test_acc', acc, prog_bar=True)
        self.log('test_precision', precision, prog_bar=True)
        self.log('test_recall', recall, prog_bar=True)

        return loss

    def configure_optimizers(self):
        return optim.Adam(self.parameters(), lr=self.learning_rate)
