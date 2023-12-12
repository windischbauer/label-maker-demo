#! /bin/bash

# Start the first process
cd label-generation-surrogate-model-backend
python rpc-backend.py &
cd ..

# Start the second process
cd label-generation-demo
streamlit run Home.py
cd ..