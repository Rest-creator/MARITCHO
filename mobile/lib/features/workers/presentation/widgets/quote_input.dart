/// The price a worker confirms on site: their work plus materials.
class QuoteInput {
  final double laborAmount;
  final double materialsAmount;

  const QuoteInput({required this.laborAmount, required this.materialsAmount});

  double get total => laborAmount + materialsAmount;
}
