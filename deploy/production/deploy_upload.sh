#!/bin/bash
set -euo pipefail

# Resumable, compressed Docker image upload for a self-hosted VPS.
# MARICHO_VPS and MARICHO_REMOTE_DIR are set by deploy.sh.

SSH_OPTS=(-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o ConnectTimeout=20)
CHUNK_SIZE="${CHUNK_SIZE:-16M}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-5}"
LOCAL_UPLOAD_DIR="${LOCAL_UPLOAD_DIR:-${TMPDIR:-/tmp}/maricho-deploy}"
REMOTE_UPLOAD_DIR="${REMOTE_UPLOAD_DIR:-$MARICHO_REMOTE_DIR/.image-upload}"

retry() {
    local attempt=1
    until "$@"; do
        if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
            echo "giving up after $attempt attempts: $*" >&2
            return 1
        fi
        echo "attempt $attempt failed; retrying in $((attempt * 5))s..." >&2
        sleep $((attempt * 5))
        attempt=$((attempt + 1))
    done
}

remote() {
    ssh "${SSH_OPTS[@]}" "$MARICHO_VPS" "$@"
}

push_file() {
    scp "${SSH_OPTS[@]}" -q "$1" "$MARICHO_VPS:$2" < /dev/null
}

normalize_sums() {
    sed -E 's/^([0-9a-f]+) [ *]/\1 /'
}

upload_image() {
    local image="$1"
    local name="${image%%:*}"
    local_id="$(docker image inspect --format '{{.Id}}' "$image")"
    remote_id="$(retry remote "docker image inspect --format '{{.Id}}' '$image' 2>/dev/null || true")"

    if [ "$local_id" = "$remote_id" ]; then
        echo "$image: server already has this exact image; skipping upload."
        return 0
    fi

    local tag="${local_id#sha256:}"
    tag="${tag:0:12}"
    local work="$LOCAL_UPLOAD_DIR/$name-$tag"
    local remote_path="$REMOTE_UPLOAD_DIR/$name-$tag"

    if [ ! -s "$work/SHA256SUMS" ]; then
        rm -rf "$LOCAL_UPLOAD_DIR/$name-"*
        mkdir -p "$work"
        echo "$image: compressing..."
        docker save "$image" | gzip -1 -n | split -b "$CHUNK_SIZE" -d -a 3 - "$work/part."
        (cd "$work" && sha256sum part.* | normalize_sums > SHA256SUMS)
    fi

    local part_count
    part_count="$(wc -l < "$work/SHA256SUMS" | tr -d ' ')"
    echo "$image: $(du -sh "$work" | cut -f1) compressed, $part_count part(s)."

    retry remote "mkdir -p '$remote_path' && find '$REMOTE_UPLOAD_DIR' -mindepth 1 -maxdepth 1 -name '$name-*' ! -name '$name-$(basename "$work" | sed "s/^$name-//")' -exec rm -rf {} +"

    local already
    already="$(retry remote "cd '$remote_path' && sha256sum part.* 2>/dev/null || true" | normalize_sums)"

    local sum part index=0
    while read -r sum part; do
        index=$((index + 1))
        if grep -qx "$sum $part" <<< "$already"; then
            echo "[$index/$part_count] $part already on server"
            continue
        fi
        echo "[$index/$part_count] uploading $part"
        retry push_file "$work/$part" "$remote_path/$part"
    done < "$work/SHA256SUMS"

    retry push_file "$work/SHA256SUMS" "$remote_path/SHA256SUMS"
    remote "cd '$remote_path' && sha256sum -c --quiet SHA256SUMS && cat part.* | gunzip | docker load && cd .. && rm -rf '$remote_path'"
    rm -rf "$work"
}
