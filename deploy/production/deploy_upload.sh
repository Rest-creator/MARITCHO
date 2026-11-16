#!/bin/bash
set -euo pipefail

# Resumable, compressed Docker image upload for a self-hosted VPS.
#
# `docker save | ssh docker load` sends the whole uncompressed image in one
# stream: slow, and a single dropped connection means starting over. Instead:
#   1. skip the image entirely if the server already has this exact image ID;
#   2. gzip it and split it into CHUNK_SIZE parts, with a checksum per part;
#   3. upload only the parts the server doesn't already have (so re-running an
#      interrupted deploy picks up where it stopped), retrying each part;
#   4. verify every checksum on the server, then `docker load` from the parts.
#
# Expects MARICHO_VPS and MARICHO_REMOTE_DIR to be set by deploy.sh.

SSH_OPTS=(-o ServerAliveInterval=15 -o ServerAliveCountMax=8 -o ConnectTimeout=20)
CHUNK_SIZE="${CHUNK_SIZE:-16M}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-5}"
LOCAL_UPLOAD_DIR="${LOCAL_UPLOAD_DIR:-${TMPDIR:-/tmp}/maricho-deploy}"
REMOTE_UPLOAD_DIR="${REMOTE_UPLOAD_DIR:-$MARICHO_REMOTE_DIR/.image-upload}"

# retry <command...>: run a command up to MAX_ATTEMPTS times with a growing pause.
retry() {
    local attempt=1
    until "$@"; do
        if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
            echo "  giving up after $attempt attempts: $*" >&2
            return 1
        fi
        echo "  attempt $attempt failed, retrying in $((attempt * 5))s..." >&2
        sleep $((attempt * 5))
        attempt=$((attempt + 1))
    done
}

remote() {
    ssh "${SSH_OPTS[@]}" "$MARICHO_VPS" "$@"
}

push_file() {
    # </dev/null: called inside `while read` loops, and ssh/scp would
    # otherwise swallow the rest of the loop's input.
    scp "${SSH_OPTS[@]}" -q "$1" "$MARICHO_VPS:$2" < /dev/null
}

# "sum  name" / "sum *name" (Windows coreutils) -> "sum name"
_normalize_sums() {
    sed -E 's/^([0-9a-f]+) [ *]/\1 /'
}

upload_image() {
    local image="$1"
    local name="${image%%:*}"
    local local_id remote_id tag work remote_path

    local_id=$(docker image inspect --format '{{.Id}}' "$image") || return 1
    remote_id=$(retry remote "docker image inspect --format '{{.Id}}' '$image' 2>/dev/null || true") || return 1
    if [ "$local_id" = "$remote_id" ]; then
        echo "  $image: server already has this exact image, skipping upload."
        return 0
    fi

    tag="${local_id#sha256:}"
    tag="${tag:0:12}"
    work="$LOCAL_UPLOAD_DIR/$name-$tag"
    remote_path="$REMOTE_UPLOAD_DIR/$name-$tag"

    # Parts are kept locally until the load succeeds, so a re-run after a
    # failure reuses them instead of re-compressing.
    if [ ! -s "$work/SHA256SUMS" ]; then
        rm -rf "$LOCAL_UPLOAD_DIR/$name-"*
        mkdir -p "$work"
        echo "  $image: compressing..."
        docker save "$image" | gzip -1 -n | split -b "$CHUNK_SIZE" -d -a 3 - "$work/part." || return 1
        (cd "$work" && sha256sum part.* | _normalize_sums > SHA256SUMS) || return 1
    fi
    local part_count
    part_count=$(wc -l < "$work/SHA256SUMS" | tr -d ' ')
    echo "  $image: $(du -sh "$work" | cut -f1) compressed, $part_count part(s)."

    # Clear leftovers from uploads of older builds, keep this build's parts.
    retry remote "mkdir -p '$remote_path' && find '$REMOTE_UPLOAD_DIR' -mindepth 1 -maxdepth 1 -name '$name-*' ! -name '$name-$tag' -exec rm -rf {} +" || return 1

    local already
    already=$(retry remote "cd '$remote_path' && sha256sum part.* 2>/dev/null || true" | _normalize_sums) || return 1

    local sum part index=0
    while read -r sum part; do
        index=$((index + 1))
        if grep -qx "$sum $part" <<< "$already"; then
            echo "  [$index/$part_count] $part already on server"
            continue
        fi
        echo "  [$index/$part_count] uploading $part"
        retry push_file "$work/$part" "$remote_path/$part" || return 1
    done < "$work/SHA256SUMS"

    retry push_file "$work/SHA256SUMS" "$remote_path/SHA256SUMS" || return 1

    echo "  $image: verifying and loading on server..."
    remote "cd '$remote_path' && sha256sum -c --quiet SHA256SUMS && cat part.* | gunzip | docker load && cd .. && rm -rf '$remote_path'" || {
        echo "  $image: load failed. Re-run the deploy; parts already uploaded will be skipped." >&2
        return 1
    }
    rm -rf "$work"
}
