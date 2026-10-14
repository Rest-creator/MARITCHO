import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/workers/presentation/widgets/quote_input.dart';

/// "I've arrived — confirm the price". Pops with a [QuoteInput], or null
/// if the worker backs out.
class QuoteSheet extends StatefulWidget {
  /// What the worker offered, used as the starting price for their work.
  final double? offeredAmount;

  const QuoteSheet({super.key, this.offeredAmount});

  /// Parses money typed on a phone keypad ("45", "45.50", "45,5").
  static double? parseAmount(String text) {
    final String cleaned = text.trim().replaceAll(',', '.');
    if (cleaned.isEmpty) return null;
    final double? value = double.tryParse(cleaned);
    if (value == null || !value.isFinite || value < 0) return null;
    return value;
  }

  @override
  State<QuoteSheet> createState() => _QuoteSheetState();
}

class _QuoteSheetState extends State<QuoteSheet> {
  late final TextEditingController _labor = TextEditingController(
    text: widget.offeredAmount == null ? '' : _plain(widget.offeredAmount!),
  );
  final TextEditingController _materials = TextEditingController(text: '0');
  String? _error;

  static String _plain(double amount) => amount == amount.roundToDouble()
      ? amount.toStringAsFixed(0)
      : amount.toStringAsFixed(2);

  @override
  void initState() {
    super.initState();
    _labor.addListener(_onChanged);
    _materials.addListener(_onChanged);
  }

  void _onChanged() => setState(() => _error = null);

  QuoteInput? get _input {
    final double? labor = QuoteSheet.parseAmount(_labor.text);
    final double? materials = QuoteSheet.parseAmount(
      _materials.text.isEmpty ? '0' : _materials.text,
    );
    if (labor == null || labor <= 0 || materials == null) return null;
    return QuoteInput(laborAmount: labor, materialsAmount: materials);
  }

  void _submit() {
    final QuoteInput? input = _input;
    if (input == null) {
      setState(() => _error = 'Enter what your work costs, in US dollars.');
      return;
    }
    Navigator.of(context).pop(input);
  }

  @override
  Widget build(BuildContext context) {
    final QuoteInput? input = _input;
    final List<TextInputFormatter> money = <TextInputFormatter>[
      FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]')),
    ];
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        16,
        20,
        20 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            'Confirm the price',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            widget.offeredAmount == null
                ? 'Now that you have seen the job, confirm what it will cost. '
                      'The client pays it when they sign the job off.'
                : 'Now that you have seen the job, confirm what it will cost. '
                      'You offered \$${_plain(widget.offeredAmount!)}.',
            style: const TextStyle(color: AppTheme.coolGray, height: 1.4),
          ),
          const SizedBox(height: 16),
          Row(
            children: <Widget>[
              Expanded(
                child: TextField(
                  controller: _labor,
                  autofocus: true,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  inputFormatters: money,
                  decoration: const InputDecoration(
                    labelText: 'Your work',
                    prefixText: '\$ ',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _materials,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  inputFormatters: money,
                  decoration: const InputDecoration(
                    labelText: 'Materials',
                    prefixText: '\$ ',
                  ),
                  onSubmitted: (String _) => _submit(),
                ),
              ),
            ],
          ),
          if (_error != null) ...<Widget>[
            const SizedBox(height: 8),
            Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _submit,
            child: Text(
              input == null
                  ? 'Send price'
                  : 'Send price · \$${_plain(input.total)}',
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            "No signal? It's saved on your phone and sends by itself.",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: AppTheme.coolGray),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _labor.removeListener(_onChanged);
    _materials.removeListener(_onChanged);
    _labor.dispose();
    _materials.dispose();
    super.dispose();
  }
}
