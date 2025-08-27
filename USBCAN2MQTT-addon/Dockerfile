# https://developers.home-assistant.io/docs/add-ons/configuration#add-on-dockerfile
ARG BUILD_FROM
FROM $BUILD_FROM

# Install python3
RUN apk add --no-cache \
    python3 \
    py3-pip

# Copy root filesystem
COPY rootfs /

# Install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --ignore-installed -r /usr/bin/requirements.txt

# Set permissions
RUN chmod a+x /usr/bin/driver_can.py

# Add additional packages needed for USB/CAN support
RUN apk add --no-cache \
    udev \
    eudev \
    libusb