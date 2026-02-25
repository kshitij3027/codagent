FROM python:3.12-slim
RUN pip install uv
WORKDIR /app
COPY . .
RUN uv pip install --system -e .
