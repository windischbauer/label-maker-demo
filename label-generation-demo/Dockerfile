# Use a base image with Python installed
FROM python:3.11.6-slim

# Set the working directory
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

EXPOSE 8501

# Set the entry point
CMD ["/bin/sh", "startup.sh"]

