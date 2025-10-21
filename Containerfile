FROM quay.io/149segolte/fedora
# Install common tools
RUN dnf install -y \
    procps-ng \
    fish git neovim && \
    dnf clean all
# Copy configuration files
COPY files/ /tmp/
# Configure shell
RUN cat /tmp/bash_to_fish.sh >> /root/.bashrc
RUN cp /tmp/config.fish /root/.config/fish/