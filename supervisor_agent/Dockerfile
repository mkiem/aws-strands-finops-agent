# Use AWS Lambda Python 3.11 base image (following project rules for Python 3.10+)
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt first for better Docker layer caching
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}
COPY llm_router_simple.py ${LAMBDA_TASK_ROOT}
COPY __init__.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_handler.handler" ]
