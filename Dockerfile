FROM python:3.11

# Install espeak dependency
RUN apt-get update && apt-get install -y espeak \
    && ldconfig -p | grep espeak

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "app:app"]