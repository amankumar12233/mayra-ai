import 'package:flutter/material.dart';

import 'config.dart';
import 'home_screen.dart';

void main() {
  runApp(const AaruPlayApp());
}

class AaruPlayApp extends StatelessWidget {
  const AaruPlayApp({super.key});

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF55DDF5);
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF050811),
        colorScheme: ColorScheme.fromSeed(
          seedColor: accent,
          brightness: Brightness.dark,
          surface: const Color(0xFF0D1423),
        ),
        useMaterial3: true,
        fontFamily: 'Arial',
      ),
      home: const MainNavigationShell(),
    );
  }
}
