import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/core/security/quick_login_service.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/quick_login_page.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

import '../../helpers/fakes.dart';

void main() {
  testWidgets(
    'uses a full background and an in-app keypad without system keyboard',
    (tester) async {
      final storage = FakeSecureStorage();
      await QuickLoginService(
        storage,
      ).enable('1234', displayName: 'Mohamed Arafat');
      await tester.pumpWidget(
        ProviderScope(
          overrides: [secureStorageProvider.overrideWithValue(storage)],
          child: const MaterialApp(home: QuickLoginPage()),
        ),
      );
      await tester.pump();

      expect(find.byType(BrandedPageBackground), findsOneWidget);
      expect(find.byType(EditableText), findsNothing);
      expect(find.byType(GridView), findsOneWidget);
      expect(find.text('1'), findsOneWidget);
      expect(find.text('Mohamed Arafat'), findsOneWidget);
      expect(find.text('NNEXORIS'), findsNothing);
      expect(
        Directionality.of(tester.element(find.byType(GridView))),
        TextDirection.ltr,
      );

      await tester.tap(find.text('1'));
      await tester.pump();
      expect(find.byType(EditableText), findsNothing);
    },
  );
}
