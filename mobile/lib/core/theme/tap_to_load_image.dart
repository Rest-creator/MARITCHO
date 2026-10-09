import 'package:flutter/material.dart';

class TapToLoadImage extends StatefulWidget {
  final String imageUrl;
  final String altText;

  const TapToLoadImage({
    super.key,
    required this.imageUrl,
    required this.altText,
  });

  @override
  State<TapToLoadImage> createState() => _TapToLoadImageState();
}

class _TapToLoadImageState extends State<TapToLoadImage> {
  bool _isLoaded = false;

  @override
  Widget build(BuildContext context) {
    if (_isLoaded) {
      return Image.network(
        widget.imageUrl,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) => const Icon(Icons.broken_image),
      );
    }

    return GestureDetector(
      onTap: () => setState(() => _isLoaded = true),
      child: Container(
        padding: const EdgeInsets.all(16.0),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          border: Border.all(color: Colors.grey[400]!),
          borderRadius: BorderRadius.circular(8.0),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.image, size: 32, color: Colors.grey),
            const SizedBox(height: 8),
            Text(
              'Tap to load: \${widget.altText}',
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
    );
  }
}
