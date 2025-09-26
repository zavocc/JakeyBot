FROM python:3.12-slim
WORKDIR /jakeybot
ENV PATH="/jakeybot/.local/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

# Create a user account named "jakey"
RUN useradd -u 6969 --home-dir /jakeybot jakey

# Copy the source code
COPY . .

# Install clang compiler
RUN apt-get update
RUN apt-get install clang --no-install-recommends --yes

# Correct ownership
RUN chown -R 6969:6969 /jakeybot

# Change the user
USER jakey

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python", "main.py"]
