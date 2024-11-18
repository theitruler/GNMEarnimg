# Use the official Python 3.9 slim image instead of alpine for better compatibility
FROM python:3.9-alpine3.20



# Set the working directory in the container
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install waitress

# Copy the rest of your application code into the container
COPY . .

# Expose the port your app runs on
EXPOSE 5000

# Command to run your application using Waitress
CMD ["python", "app.py"]