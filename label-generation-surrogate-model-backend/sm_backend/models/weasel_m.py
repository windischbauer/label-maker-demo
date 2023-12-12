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

import datetime

import numpy as np
import pytorch_lightning as pl
import torch
import torch.nn as nn
from pytorch_lightning.callbacks import ModelCheckpoint
from weasel.datamodules.base_datamodule import BasicWeaselDataModule
from weasel.models import Weasel
from weasel.models.downstream_models.MLP import MLPNet
from weasel.models.downstream_models.base_model import DownstreamBaseModel

from sm_backend.models.surrogate_model import SurrogateModel


class WeaselM(SurrogateModel):
    def __init__(self,
                 features=None,
                 labels=None
                 ) -> None:
        self.features = features
        self.labels = labels
        self.final_cnn_model = None

    def apply(self, features, labels, fold=0):
        if features.equals(self.features) \
                and labels.equals(self.labels) \
                and self.final_cnn_model is not None:
            print('Model already trained')
            return 'Model already trained'

        self.features = features
        self.labels = labels

        print('Starting WEASEL Model')
        # print(features)
        # print(labels)
        # print(labels.shape[1])
        classes = np.unique(labels.to_numpy())
        n_classes = len(classes[classes >= 0])

        endmodel = MLPNet(dropout=0.3, net_norm='none', activation_func='ReLU', input_dim=features.shape[1],
                          hidden_dims=[10, 10, 5], output_dim=n_classes)

        print('Created End Model')

        weasel = Weasel(
            num_LFs=labels.shape[1],
            n_classes=n_classes,
            temperature=2.0,
            accuracy_scaler='sqrt',
            use_aux_input_for_encoder=True,
            class_conditional_accuracies=True,
            encoder={"hidden_dims": [32, 10]},
            optim_encoder={"name": "Adam", "lr": 1e-4},
            optim_end_model={"name": "Adam", "lr": 1e-4},
            scheduler=None,
            end_model=endmodel,
        )

        print('Created Weasel Model')

        features = features.to_numpy()
        # print(features)
        print('Converted features to numpy')

        weasel_datamodule = BasicWeaselDataModule(
            X_train=features,
            X_test=np.ndarray(shape=(0, 0)),
            Y_test=np.ndarray(shape=(0, 0)),
            label_matrix=labels.to_numpy(),
            batch_size=32,
        )

        print('Created Weasel Data Module')

        checkpoint_callback = ModelCheckpoint(mode="max")
        trainer = pl.Trainer(
            devices="auto",
            accelerator="cpu",  # CPUs or GPUs
            max_epochs=15,
            logger=None,
            deterministic=True,
            callbacks=[checkpoint_callback],
        )

        trainer.fit(weasel, weasel_datamodule)

        print('Fitting Done')

        try:
            self.final_cnn_model = weasel.load_from_checkpoint(
                trainer.checkpoint_callback.best_model_path
            ).end_model
            print('Loaded from Checkpoint')
        except:
            print('Error loading from checkpoint')

        return 'Model Trained'

    def predict(self, features):
        # Transform the data
        features = torch.tensor(features.values, dtype=torch.float32)

        print('predicting @ ' + str(datetime.datetime.now()))
        # Set the model to evaluation mode
        self.final_cnn_model.eval()

        # Perform prediction
        with torch.no_grad():
            predictions = self.final_cnn_model(features)

        # Convert the predictions to numpy array
        predictions_np = predictions.numpy()

        print(predictions_np[:5])

        # For binary classification, you can get the predicted class (0 or 1) as follows:
        predicted_class = np.argmax(predictions_np, axis=1)

        return predicted_class.tolist()


# NOT yet adapted to the project
class MyCNN(DownstreamBaseModel):
    def __init__(self, in_channels,
                 hidden_dim,
                 conv_layers: int,
                 n_classes: int,
                 kernel_size=(3, 3),
                 *args, **kwargs):
        super().__init__()
        # Good practice:
        self.out_dim = n_classes
        self.example_input_array = torch.randn((1, in_channels, height, width))

        cnn_modules = []

        in_dim = in_channels
        for layer in range(conv_layers):
            cnn_modules += [
                nn.Conv2d(in_dim, hidden_dim, kernel_size),
                nn.GELU(),
                nn.MaxPool2d(2, 2)
            ]
            in_dim = hidden_dim

        self.convs = nn.Sequential(*cnn_modules)

        self.flattened_dim = torch.flatten(
            self.convs(self.example_input_array), start_dim=1
        ).shape[1]

        mlp_modules = [
            nn.Linear(self.flattened_dim, int(self.flattened_dim / 2)),
            nn.GELU()
        ]
        mlp_modules += [nn.Linear(int(self.flattened_dim / 2), n_classes)]
        self.readout = nn.Sequential(*mlp_modules)

    def forward(self, X: torch.Tensor, readout=True):
        conv_out = self.convs(X)
        flattened = torch.flatten(conv_out, start_dim=1)
        if not readout:
            return flattened
        logits = self.readout(flattened)
        return logits  # We predict the raw logits in forward!
