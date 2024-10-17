FROM python:3.12-slim
WORKDIR /jakeybot
ENV PATH="/jakeybot/.local/bin:${PATH}"

# Create a user account named "jakey"
RUN useradd -u 6969 --home-dir /jakeybot jakey

# Copy the source code
COPY . .

# Correct ownership
RUN chown -R 6969:6969 /jakeybot

# Change the user
USER jakey

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install wavelink and remove pycord/discord.py only leaving pycord, and other dependencies
RUN <<EOL
pip install pillow
pip install wavelink
pip uninstall -y discord.py py-cord
pip install -U py-cord
EOL

# Install additional dependencies, comment to disable
RUN pip install gradio_client

# Start the bot
CMD ["python", "main.py"]