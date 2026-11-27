import 'package:flutter/material.dart';

import 'package:mobile/core/theme/app_theme.dart';

class ReviewDraft {
  int rating;
  List<String> tags;
  String comment;

  ReviewDraft({this.rating = 5, List<String>? tags, this.comment = ''})
    : tags = tags ?? [];
}

class ReviewPanel extends StatelessWidget {
  final ReviewDraft draft;
  final ValueChanged<ReviewDraft> onChanged;
  final bool isWorkerReviewingEmployer;

  /// Employer -> Worker tags (quality & execution)
  static const List<(String, String)> employerToWorkerTags = [
    ('On time', 'ON_TIME'),
    ('Quality work', 'QUALITY_WORK'),
    ('Cleaned up', 'CLEAN'),
    ('Professional', 'PROFESSIONAL'),
    ('Good communication', 'GOOD_COMMUNICATION'),
    ('Fair price', 'FAIR_PRICE'),
    ('Reliable', 'RELIABLE'),
  ];

  /// Worker -> Employer tags (respect, safety, and prompt payment, ADR-011)
  static const List<(String, String)> workerToEmployerTags = [
    ('Paid on time', 'PAID_ON_TIME'),
    ('Job as described', 'JOB_AS_DESCRIBED'),
    ('Respectful', 'RESPECTFUL'),
    ('Safe workplace', 'SAFE_WORKPLACE'),
    ('Good communication', 'GOOD_COMMUNICATION'),
  ];

  const ReviewPanel({
    super.key,
    required this.draft,
    required this.onChanged,
    this.isWorkerReviewingEmployer = false,
  });

  @override
  Widget build(BuildContext context) {
    final tagOptions = isWorkerReviewingEmployer
        ? workerToEmployerTags
        : employerToWorkerTags;

    final title = isWorkerReviewingEmployer
        ? 'How was working with this client?'
        : 'How was their work?';

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Reviews are double-blind: ratings stay private until both sides submit or 14 days elapse.',
              style: TextStyle(fontSize: 12, color: Colors.black54),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (index) {
                final starValue = index + 1;
                final isSelected = starValue <= draft.rating;
                return IconButton(
                  icon: Icon(
                    isSelected ? Icons.star : Icons.star_border,
                    size: 32,
                    color: Colors.amber.shade700,
                  ),
                  onPressed: () {
                    draft.rating = starValue;
                    onChanged(draft);
                  },
                );
              }),
            ),
            const SizedBox(height: 12),
            const Text(
              'Choose what went well (up to 3):',
              style: TextStyle(fontSize: 13, color: Colors.black54),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: tagOptions.map((option) {
                final (label, code) = option;
                final isSelected = draft.tags.contains(code);

                return FilterChip(
                  label: Text(label),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      if (draft.tags.length < 3) {
                        draft.tags.add(code);
                      }
                    } else {
                      draft.tags.remove(code);
                    }
                    onChanged(draft);
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}
