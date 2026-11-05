import 'package:flutter/material.dart';
import 'package:aaru_play/main.dart';
import 'package:aaru_play/home_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('shows the Aaru Play home and fixed navigation', (tester) async {
    await tester.pumpWidget(const AaruPlayApp());

    expect(find.text('Aaru Play'), findsOneWidget);
    expect(find.text('Trending Music'), findsOneWidget);
    expect(find.text('YouTube Mix 1'), findsWidgets);
    expect(find.text('Main Rang Sharbaton Ka'), findsWidgets);
    expect(find.text('YouTube Mix 2'), findsWidgets);
    expect(find.text('Tum Hi Ho'), findsWidgets);
    expect(find.text('Gehra Hua'), findsWidgets);
    expect(find.text('Teri Meri Kahaani'), findsWidgets);
    expect(find.text('Quick play'), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Explore'), findsWidgets);
    expect(find.text('Library'), findsOneWidget);
    expect(find.text('Downloads'), findsOneWidget);
    expect(find.text('Made in India'), findsNothing);
  });

  testWidgets('search filters picks and category chips are interactive',
      (tester) async {
    await tester.pumpWidget(const AaruPlayApp());

    await tester.enterText(find.byType(TextField).first, 'Gehra Hua');
    await tester.pumpAndSettle();

    expect(find.text('Gehra Hua'), findsWidgets);
    expect(find.text('Tum Hi Ho'), findsNothing);

    await tester.tap(find.text('Music').first);
    await tester.pumpAndSettle();
    expect(find.text('Gehra Hua'), findsWidgets);
  });

  test('parses the supplied YouTube video and playlist URLs', () {
    PlayItem item(String url) => PlayItem(
          title: 'test',
          creator: 'test',
          performer: 'test',
          category: 'Music',
          duration: 'MUSIC',
          videoUrl: url,
          icon: Icons.music_note,
          colors: const [Colors.blue, Colors.purple],
        );

    expect(
      item('https://youtu.be/RNY1r6ovdTo?si=share').youtubeVideoId,
      'RNY1r6ovdTo',
    );
    expect(
      item('https://youtu.be/4kx4m52PVXs?si=share').youtubeVideoId,
      '4kx4m52PVXs',
    );
    expect(
      item('https://youtu.be/KQKmdCOUtpU?si=share').youtubeVideoId,
      'KQKmdCOUtpU',
    );
    expect(
      item('https://youtu.be/_nI7X7TvHjw?si=share').youtubeVideoId,
      '_nI7X7TvHjw',
    );
    expect(
      item('https://youtube.com/playlist?list=RDRuVsEx4mLcc&playnext=1')
          .youtubePlaylistId,
      'RDRuVsEx4mLcc',
    );
    expect(
      item('https://youtube.com/playlist?list=RDa9Hxkc9YxGE&playnext=1')
          .youtubePlaylistId,
      'RDa9Hxkc9YxGE',
    );
  });

  testWidgets('bottom navigation opens the app sections', (tester) async {
    await tester.pumpWidget(const AaruPlayApp());

    await tester.tap(find.text('Explore').last);
    await tester.pumpAndSettle();
    expect(find.text('Find your next favorite thing.'), findsOneWidget);

    await tester.tap(find.text('Downloads'));
    await tester.pumpAndSettle();
    expect(find.text('Nothing saved offline yet'), findsOneWidget);

    await tester.tap(find.text('Add'));
    await tester.pumpAndSettle();
    expect(find.text('Create your space'), findsOneWidget);
  });

  testWidgets('Made in India appears only in the internal about sheet',
      (tester) async {
    await tester.pumpWidget(const AaruPlayApp());

    await tester.tap(find.byTooltip('About and settings').first);
    await tester.pumpAndSettle();
    expect(find.text('Made in India'), findsOneWidget);
  });

  testWidgets('saved items appear in the library', (tester) async {
    await tester.pumpWidget(const AaruPlayApp());

    final saveButton = find.byTooltip('Save to library').first;
    await tester.ensureVisible(saveButton);
    await tester.pumpAndSettle();
    await tester.tap(saveButton);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Library'));
    await tester.pumpAndSettle();

    expect(find.text('YouTube Mix 1'), findsOneWidget);
  });

  testWidgets('home layout fits a narrow mobile viewport', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const AaruPlayApp());
    await tester.pumpAndSettle();

    expect(find.byType(MainNavigationShell), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
