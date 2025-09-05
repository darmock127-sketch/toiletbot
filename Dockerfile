# Use Python 3.10 base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Run the bot
CMD ["python", "toilet_bot.py"]
