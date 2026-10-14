import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/workers/presentation/widgets/quote_input.dart';
import 'package:mobile/features/workers/presentation/widgets/quote_sheet.dart';

/// Opens the sheet from a button and records what it popped with.
class _Harness extends StatefulWidget {
  final double? offeredAmount;

  const _Harness({this.offeredAmount});

  @override
  State<_Harness> createState() => _HarnessState();
}

class _HarnessState extends State<_Harness> {
  QuoteInput? result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          onPressed: () async {
            final QuoteInput? input = await showModalBottomSheet<QuoteInput>(
              context: context,
              isScrollControlled: true,
              builder: (BuildContext _) =>
                  QuoteSheet(offeredAmount: widget.offeredAmount),
            );
            if (!mounted) return;
            setState(() => result = input);
          },
          child: const Text('open'),
        ),
      ),
    );
  }
}

Future<_HarnessState> _open(
  WidgetTester tester, {
  double? offeredAmount,
}) async {
  await tester.pumpWidget(
    MaterialApp(home: _Harness(offeredAmount: offeredAmount)),
  );
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
  return tester.state<_HarnessState>(find.byType(_Harness));
}

void main() {
  test('parseAmount reads what people type on a phone keypad', () {
    expect(QuoteSheet.parseAmount('45'), 45);
    expect(QuoteSheet.parseAmount('45,50'), 45.5);
    expect(QuoteSheet.parseAmount(' 12.25 '), 12.25);
    expect(QuoteSheet.parseAmount(''), isNull);
    expect(QuoteSheet.parseAmount('-3'), isNull);
    expect(QuoteSheet.parseAmount('abc'), isNull);
  });

  testWidgets('starts from the offer and sends work plus materials', (
    WidgetTester tester,
  ) async {
    final _HarnessState harness = await _open(tester, offeredAmount: 40);

    expect(find.textContaining('You offered \$40'), findsOneWidget);
    expect(find.text('Send price · \$40'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, 'Materials'), '5.5');
    await tester.pump();
    expect(find.text('Send price · \$45.50'), findsOneWidget);

    await tester.tap(find.text('Send price · \$45.50'));
    await tester.pumpAndSettle();

    expect(harness.result?.laborAmount, 40);
    expect(harness.result?.materialsAmount, 5.5);
  });

  testWidgets('asks for a price instead of sending nothing', (
    WidgetTester tester,
  ) async {
    final _HarnessState harness = await _open(tester);

    await tester.tap(find.text('Send price'));
    await tester.pump();

    expect(
      find.text('Enter what your work costs, in US dollars.'),
      findsOneWidget,
    );
    expect(harness.result, isNull);
    expect(
      find.byType(QuoteSheet),
      findsOneWidget,
      reason: 'the sheet stays open',
    );
  });
}
