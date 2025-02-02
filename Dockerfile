# Start from a python image
FROM python:3.8.19-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Clone the repository
COPY src .

# We should add here a train, inference or test command (or pass what
# we want to do as an argument to the docker run command)
CMD ["python3", "main.py"]
