# VLM container with NanoLLM
FROM dustynv/nano_llm:r36.4.0

# Install additional Python packages
RUN pip3 install --no-cache-dir \
    redis \
    Pillow

WORKDIR /app
