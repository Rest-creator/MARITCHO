# Media uploads

`POST /media/upload` accepts authenticated JPEG/WebP images and Ogg Opus,
AAC, and M4A voice notes. Photos are capped at 2 MB and audio at 1 MB.
Files are written beneath `MEDIA_STORAGE_PATH` (default `storage/media`)
using server-generated names; the original filename is never used.
`Idempotency-Key` replays the existing owner-scoped upload. Downloads require
the owner (or OPS); broader job-party access remains a follow-up once media
references are converted from free-form URLs to persisted relationships.

Image metadata stripping and thumbnail generation are intentionally not
implemented here: the backend has no approved image-processing dependency,
and accepting an unsafe speculative native/cloud pipeline would be worse than
retaining the validated original. Add a vetted Pillow/libvips worker before
enabling transformations.
