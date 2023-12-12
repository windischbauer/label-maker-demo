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
import os
from sm_backend.models.surrogate_model import SurrogateModel
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class TorchLogisticRegression(SurrogateModel):
    
    def __init__(self,
                 features=None,
                 labels=None
                 ) -> None:
        self.features = features
        self.labels = labels
        self.ann_model = None
        
    def apply(self, features, labels):

        if features.equals(self.features) and labels.equals(self.labels) and self.ann_model is not None:
                return 'Model already trained'

        self.features = features
        self.labels = labels

        # Transform the data
        features = torch.tensor(features.values, dtype=torch.float32)
        labels = torch.tensor(labels.values, dtype=torch.float32)
        
        # Instantiate the model
        input_size = features.size(1)
        hidden_size1 = 128
        hidden_size2 = 64
        output_size = len(labels[0])

        self.ann_model = ANNModel(input_size, hidden_size1, hidden_size2, output_size)

        # Define the loss function and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.ann_model.parameters(), lr=0.001)

        # Train the model
        epochs = 200
        batch_size = 64
        validation_split = 0.2

        for epoch in range(epochs):
            if epoch % 20 == 0:
                print(epoch)
            permutation = torch.randperm(features.size()[0])

            for i in range(0, features.size()[0], batch_size):
                indices = permutation[i:i + batch_size]
                batch_x, batch_y = features[indices], labels[indices]

                optimizer.zero_grad()
                outputs = self.ann_model(batch_x)
                loss = criterion(outputs, torch.argmax(batch_y, dim=-1))
                loss.backward()
                optimizer.step()
        return 'Model trained'

    
    def predict(self, features):
        # Transform the data
        features = torch.tensor(features.values, dtype=torch.float32)

        print('predicting @ ' + str(datetime.datetime.now()))
        # Set the model to evaluation mode
        self.ann_model.eval()

        # Perform prediction
        with torch.no_grad():
            predictions = self.ann_model(features)

        # Convert the predictions to numpy array
        predictions_np = predictions.numpy()

        # For binary classification, you can get the predicted class (0 or 1) as follows:
        predicted_class = np.argmax(predictions_np, axis=1)
        
        return predicted_class.tolist()
        
        
# Define the neural network
class ANNModel(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size):
        super(ANNModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size1)
        self.fc2 = nn.Linear(hidden_size1, hidden_size2)
        self.dropout = nn.Dropout(0.1)
        self.fc3 = nn.Linear(hidden_size2, output_size)
        device = torch.device("cpu")    
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x