FROM python:3.13.5-slim

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml README.md poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy only the npmsync folder
COPY ./npmsync ./npmsync

# Set proper ownership of the application directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Install dependencies
RUN poetry install

# Command to run the application
CMD ["poetry", "run", "npmsync"]
