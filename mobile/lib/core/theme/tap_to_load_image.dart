import 'package:flutter/material.dart';

/// Light Mode: an image costs data, so it only downloads when the person
/// taps for it (APP-003). Backend media paths (`/media/...`) need the
/// session, so callers pass [headers] (see `MediaUrl`).
class TapToLoadImage extends StatefulWidget {
  final String imageUrl;
  final String altText;
  final Map<String, String>? headers;

  const TapToLoadImage({
    super.key,
    required this.imageUrl,
    required this.altText,
    this.headers,
  });

  @override
  State<TapToLoadImage> createState() => _TapToLoadImageState();
}

class _TapToLoadImageState extends State<TapToLoadImage> {
  bool _isLoaded = false;

  @override
  Widget build(BuildContext context) {
    if (_isLoaded) {
      return Semantics(
        image: true,
        label: widget.altText,
        child: Image.network(
          widget.imageUrl,
          headers: widget.headers,
          fit: BoxFit.cover,
          errorBuilder: (
            BuildContext context,
            Object error,
            StackTrace? stackTrace,
          ) => const Icon(Icons.broken_image),
        ),
      );
    }

    return Material(
      color: Colors.grey[200],
      shape: RoundedRectangleBorder(
        side: BorderSide(color: Colors.grey[400]!),
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8.0),
        onTap: () => setState(() => _isLoaded = true),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.image, size: 32, color: Colors.grey),
              const SizedBox(height: 8),
              Text(
                'Tap to load: ${widget.altText}',
                style: const TextStyle(color: Colors.black87),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              const Text(
                '(Saves data)',
                style: TextStyle(fontSize: 12, color: Colors.black54),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
