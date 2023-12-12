# Use a base Python image
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the poetry files to the working directory
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip3 install poetry

# Install project dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Copy the entire project directory to the working directory
COPY . .

EXPOSE 8000

# Set the entry point of the container
CMD ["python", "rpc-backend.py"]
