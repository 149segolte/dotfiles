FROM quay.io/149segolte/fedora
# Install required packages
RUN dnf install -y \
    procps-ng \
    fish git \
    bat zoxide ripgrep fzf fd-find && \
    dnf clean all
# Fetch eza (not in repos)
RUN curl -sL https://github.com/eza-community/eza/releases/latest/download/eza_x86_64-unknown-linux-gnu.tar.gz | tar -xzvf - -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/eza
# Copy configuration files
COPY files/ /tmp/
# Configure shell
RUN cat /tmp/bash_to_fish.sh >> /root/.bashrc
RUN fish -c "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher"
RUN fish -c "fisher install IlanCosman/tide@v6" && \
    fish -c "fisher install PatrickF1/fzf.fish"
RUN mkdir -p /root/.config/fish/ && cp /tmp/config.fish /root/.config/fish/
RUN fish -c "tide configure --auto --style=Lean --prompt_colors='True color' --show_time='24-hour format' --lean_prompt_height='One line' --prompt_spacing=Compact --icons='Few icons' --transient=No"
