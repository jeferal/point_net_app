# Start from a python image
FROM python:3.8.19-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Clone the repository
RUN git clone https://github.com/chisyliu/objectDetection_Pointnet_Pointnet2_pytorch.git

# Specify the command to run on container start
CMD ["python3", "./objectDetection_Pointnet_Pointnet2_pytorch/train_clf.py", "--model_name", "pointnet"]
