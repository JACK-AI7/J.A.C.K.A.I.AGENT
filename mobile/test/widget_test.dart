// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:jack_mobile/main.dart';

void main() {
  testWidgets('Dashboard UI smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const JackUltraApp());

    // Verify that the title exists.
    expect(find.text('J.A.C.K.'), findsOneWidget);
    
    // Verify that the metrics exist.
    expect(find.text('NEURAL LOAD'), findsOneWidget);
    expect(find.text('MEMORY SWARM'), findsOneWidget);
  });
}
