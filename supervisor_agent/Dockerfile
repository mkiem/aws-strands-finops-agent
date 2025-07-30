# FinOps Supervisor Agent - Container Image
# Multi-stage build for optimized container size

# Build stage
FROM public.ecr.aws/lambda/python:3.11 as builder

# Set working directory
WORKDIR /var/task

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --target /var/task -r requirements.txt

# Production stage
FROM public.ecr.aws/lambda/python:3.11

# Copy installed dependencies from builder stage
COPY --from=builder /var/task /var/task

# Copy application code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY llm_router_simple.py ${LAMBDA_TASK_ROOT}/
COPY intelligent_finops_supervisor.py ${LAMBDA_TASK_ROOT}/
COPY strands_supervisor_agent.py ${LAMBDA_TASK_ROOT}/
COPY finops_agent_tools.py ${LAMBDA_TASK_ROOT}/
COPY __init__.py ${LAMBDA_TASK_ROOT}/

# Set environment variables for better performance
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Add labels for better container management
LABEL maintainer="FinOps Agent Team"
LABEL project="FinOpsAgent"
LABEL component="SupervisorAgent"
LABEL version="1.0"

# Set the CMD to the Lambda handler
CMD ["lambda_handler.lambda_handler"]
