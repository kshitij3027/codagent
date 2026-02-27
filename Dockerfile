FROM python:3.12-slim
ENV TERM=xterm-256color
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv
WORKDIR /app
COPY . .
RUN uv pip install --system -e .

# tini as PID 1 ensures proper signal forwarding to the Python process.
# Without it, the Python process IS PID 1, which has special Linux signal
# semantics that can prevent SIGINT (Ctrl-C) from being delivered.
ENTRYPOINT ["tini", "--"]
CMD ["codagent"]
