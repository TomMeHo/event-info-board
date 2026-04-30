# Stage 1: Base build stage
FROM python:3.12-slim AS builder
 
# Create the workdir inside the container
RUN mkdir /app
WORKDIR /app
 
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Upgrade pip and install pipenv
RUN pip uninstall -y setuptools
RUN pip cache purge
RUN pip install --upgrade pip
RUN pip install pipenv

# install dependencies
COPY Pipfile Pipfile.lock ./
RUN pipenv clean
RUN pipenv install --system --deploy

# Stage 2: Production stage
FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

#Copy application code
COPY --chown=appuser:appuser . .
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Copy the Django project to the container
#COPY . /app/

EXPOSE 8000

# Run entrypoint script
CMD ["/app/entrypoint.sh"]