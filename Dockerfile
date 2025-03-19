FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    espeak \
    espeak-ng \
    libespeak1 \
    libespeak-ng1 \
    libportaudio2 \
    python3-espeak \
    alsa-utils \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for espeak libraries
RUN ln -s /usr/lib/x86_64-linux-gnu/libespeak.so.1 /usr/lib/libespeak.so.1 && \
    ln -s /usr/lib/x86_64-linux-gnu/libespeak-ng.so.1 /usr/lib/libespeak-ng.so.1

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
ENV PATH=/usr/local/bin:$PATH

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==20.1.0

# Verify installations
RUN espeak --version && \
    gunicorn --version

EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV TEMPLATES_AUTO_RELOAD=False
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]