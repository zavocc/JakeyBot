FROM python:3.12-slim
WORKDIR /jakeybot
ENV PATH="/jakeybot/.local/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

# Create a user account named "jakey"
RUN useradd -u 6969 --home-dir /jakeybot jakey

# Copy the source code
COPY . .

# Install C compiler and Nano text editor
RUN apt-get update
RUN apt-get install g++ nano --no-install-recommends --yes

# Correct ownership
RUN chown -R 6969:6969 /jakeybot

# Change the user
USER jakey

# Install base dependencies and optionally plugin dependencies
RUN pip install --no-cache-dir -r /jakeybot/requirements.txt && \
    if [ -f /jakeybot/plugins/requirements.txt ]; then \
      pip install --no-cache-dir -r /jakeybot/plugins/requirements.txt; \
    fi

# Start the bot
ENTRYPOINT ["/bin/bash", "/jakeybot/run.sh"]
