FROM python:3.13.5-slim

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy the rest of the application
COPY . .

# Install dependencies
RUN poetry install

# Command to run the application
# Replace with your actual entry point
CMD ["poetry", "run", "npmsync"]
