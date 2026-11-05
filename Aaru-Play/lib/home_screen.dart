import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';

import 'config.dart';

const _background = Color(0xFF050811);
const _surface = Color(0xA6101827);
const _surfaceRaised = Color(0xCC111B2B);
const _muted = Color(0xFF9AA9C1);
const _cyan = Color(0xFF55DDF5);
const _blue = Color(0xFF548CFF);
const _purple = Color(0xFFB178FF);

class _SciFiBackdrop extends StatelessWidget {
  const _SciFiBackdrop();

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF050811), Color(0xFF0B1020), _background],
            ),
          ),
        ),
        Positioned(
          top: -150,
          right: -120,
          child: _GlowOrb(color: _blue.withValues(alpha: 0.13), size: 360),
        ),
        Positioned(
          top: 280,
          left: -190,
          child: _GlowOrb(color: _purple.withValues(alpha: 0.11), size: 390),
        ),
        Positioned(
          bottom: -240,
          right: -70,
          child: _GlowOrb(color: _cyan.withValues(alpha: 0.08), size: 420),
        ),
      ],
    );
  }
}

class _GlowOrb extends StatelessWidget {
  const _GlowOrb({required this.color, required this.size});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return ImageFiltered(
      imageFilter: ui.ImageFilter.blur(sigmaX: 70, sigmaY: 70),
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color,
        ),
      ),
    );
  }
}

class _GlassPanel extends StatelessWidget {
  const _GlassPanel({
    required this.child,
    this.padding = EdgeInsets.zero,
    this.radius = 18,
    this.glow = _cyan,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final Color glow;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ui.ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: _surface.withValues(alpha: 0.72),
            borderRadius: BorderRadius.circular(radius),
            border: Border.all(color: glow.withValues(alpha: 0.3)),
            boxShadow: [
              BoxShadow(
                color: glow.withValues(alpha: 0.09),
                blurRadius: 22,
                spreadRadius: 0,
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }
}

class PlayItem {
  const PlayItem({
    required this.title,
    required this.creator,
    required this.performer,
    required this.category,
    required this.duration,
    required this.videoUrl,
    required this.icon,
    required this.colors,
  });

  final String title;
  final String creator;
  final String performer;
  final String category;
  final String duration;
  final String videoUrl;
  final IconData icon;
  final List<Color> colors;

  String? get youtubeVideoId {
    final uri = Uri.tryParse(videoUrl);
    if (uri == null) return null;

    final host = uri.host.toLowerCase();
    if (host == 'youtu.be') {
      return uri.pathSegments.isEmpty ? null : uri.pathSegments.first;
    }
    if (host != 'youtube.com' &&
        host != 'www.youtube.com' &&
        host != 'm.youtube.com') {
      return null;
    }
    if (uri.path == '/watch') return uri.queryParameters['v'];
    if (uri.pathSegments.length >= 2 &&
        {'embed', 'shorts', 'live'}.contains(uri.pathSegments.first)) {
      return uri.pathSegments[1];
    }
    return null;
  }

  String? get youtubePlaylistId {
    final uri = Uri.tryParse(videoUrl);
    if (uri == null) return null;

    final host = uri.host.toLowerCase();
    if (host != 'youtube.com' &&
        host != 'www.youtube.com' &&
        host != 'm.youtube.com') {
      return null;
    }
    return uri.path == '/playlist' ? uri.queryParameters['list'] : null;
  }
}

const _catalog = <PlayItem>[
  PlayItem(
    title: 'YouTube Mix 1',
    creator: 'YouTube playlist',
    performer: 'Radio mix',
    category: 'Music',
    duration: 'MIX',
    videoUrl:
        'https://youtube.com/playlist?list=RDRuVsEx4mLcc&playnext=1&si=gAyFcMsTwfd_uMPj',
    icon: Icons.favorite_rounded,
    colors: [Color(0xFF4F3A9D), Color(0xFF171D45)],
  ),
  PlayItem(
    title: 'Main Rang Sharbaton Ka',
    creator: 'Bollywood Rewind Songs',
    performer: 'Arijit Singh',
    category: 'Music',
    duration: 'MUSIC',
    videoUrl: 'https://youtu.be/RNY1r6ovdTo?si=JegghE7ASVi2RtXG',
    icon: Icons.music_note_rounded,
    colors: [Color(0xFF176B72), Color(0xFF122C48)],
  ),
  PlayItem(
    title: 'YouTube Mix 2',
    creator: 'YouTube playlist',
    performer: 'Radio mix',
    category: 'Music',
    duration: 'MIX',
    videoUrl:
        'https://youtube.com/playlist?list=RDa9Hxkc9YxGE&playnext=1&si=jBU1xFskSWAWTzvC',
    icon: Icons.graphic_eq_rounded,
    colors: [Color(0xFF9B527D), Color(0xFF39284F)],
  ),
  PlayItem(
    title: 'Tum Hi Ho',
    creator: '🖤broken lofi',
    performer: 'Aashiqui 2',
    category: 'Music',
    duration: 'MUSIC',
    videoUrl: 'https://youtu.be/4kx4m52PVXs?si=2WjQZ5xzaZwFp3IA',
    icon: Icons.auto_awesome_rounded,
    colors: [Color(0xFF287A72), Color(0xFF173944)],
  ),
  PlayItem(
    title: 'Gehra Hua',
    creator: 'AIdream house',
    performer: 'Dhurandhar',
    category: 'Music',
    duration: 'MUSIC',
    videoUrl: 'https://youtu.be/KQKmdCOUtpU?si=DxWvOBTdb2AuG9AL',
    icon: Icons.graphic_eq_rounded,
    colors: [Color(0xFF9B527D), Color(0xFF39284F)],
  ),
  PlayItem(
    title: 'Teri Meri Kahaani',
    creator: 'Bollywood Soulful Beats',
    performer: 'Arijit Singh • Gabbar Is Back',
    category: 'Music',
    duration: 'MUSIC',
    videoUrl: 'https://youtu.be/_nI7X7TvHjw?si=vi5gCcY8Y9PaOwBM',
    icon: Icons.favorite_rounded,
    colors: [Color(0xFF287A72), Color(0xFF173944)],
  ),
];

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;
  final Set<String> _library = {};
  final Set<String> _downloads = {};

  void _toggleLibrary(PlayItem item) {
    setState(() {
      if (!_library.add(item.title)) {
        _library.remove(item.title);
      }
    });
  }

  void _toggleDownload(PlayItem item) {
    setState(() {
      if (!_downloads.add(item.title)) {
        _downloads.remove(item.title);
      }
    });
    _showMessage(
      _downloads.contains(item.title)
          ? 'Added to your offline list'
          : 'Removed from your offline list',
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
  }

  void _playItem(PlayItem item) {
    final videoId = item.youtubeVideoId;
    final playlistId = item.youtubePlaylistId;
    if (videoId == null && playlistId == null) {
      _showMessage(
        'This YouTube link does not contain a video or playlist ID.',
      );
      return;
    }
    showDialog<void>(
      context: context,
      builder: (context) => _YoutubePlayerDialog(
        item: item,
        videoId: videoId,
        playlistId: playlistId,
      ),
    );
  }

  void _showAbout() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: _surface,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'About ${AppConfig.appName}',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              const Text(
                'A little place for music, play, and discovery.',
                style: TextStyle(color: _muted, height: 1.5),
              ),
              const SizedBox(height: 20),
              const Divider(color: Colors.white12),
              const SizedBox(height: 10),
              const Row(
                children: [
                  Icon(Icons.favorite_rounded, color: _purple, size: 18),
                  SizedBox(width: 10),
                  Text('Made in India', style: TextStyle(color: _muted)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screens = <Widget>[
      HomeScreen(
        onAbout: _showAbout,
        onExplore: () => setState(() => _currentIndex = 1),
        onPlay: _playItem,
        onLibrary: _toggleLibrary,
        onDownload: _toggleDownload,
        library: _library,
        downloads: _downloads,
      ),
      ExploreScreen(
        onPlay: _playItem,
        onLibrary: _toggleLibrary,
        library: _library,
      ),
      const AddContentScreen(),
      CollectionScreen(
        title: 'Your Library',
        subtitle: 'Your saved picks, all in one place.',
        icon: Icons.favorite_border_rounded,
        items: _catalog.where((item) => _library.contains(item.title)).toList(),
        emptyTitle: 'Your library is waiting',
        emptyDetail: 'Save something you like and it will show up here.',
        onPlay: _playItem,
        onLibrary: _toggleLibrary,
      ),
      CollectionScreen(
        title: 'Downloads',
        subtitle: 'Keep your chosen picks close by.',
        icon: Icons.download_for_offline_outlined,
        items:
            _catalog.where((item) => _downloads.contains(item.title)).toList(),
        emptyTitle: 'Nothing saved offline yet',
        emptyDetail: 'Use the download option on a pick to add it here.',
        onPlay: _playItem,
        onLibrary: _toggleLibrary,
      ),
    ];

    return Scaffold(
      backgroundColor: _background,
      body: Stack(
        children: [
          const Positioned.fill(child: _SciFiBackdrop()),
          IndexedStack(index: _currentIndex, children: screens),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xF2141B2B), Color(0xFF080D18)],
          ),
          border: Border(top: BorderSide(color: Color(0x6655DDF5))),
          boxShadow: [
            BoxShadow(
              color: Color(0x3355DDF5),
              blurRadius: 22,
              offset: Offset(0, -5),
            ),
          ],
        ),
        child: SafeArea(
          top: false,
          child: BottomNavigationBar(
            type: BottomNavigationBarType.fixed,
            backgroundColor: Colors.transparent,
            elevation: 0,
            currentIndex: _currentIndex,
            selectedItemColor: _cyan,
            unselectedItemColor: _muted,
            selectedIconTheme: const IconThemeData(
              color: _cyan,
              shadows: [Shadow(color: _cyan, blurRadius: 14)],
            ),
            unselectedIconTheme: const IconThemeData(color: _muted),
            selectedFontSize: 11,
            unselectedFontSize: 11,
            onTap: (index) => setState(() => _currentIndex = index),
            items: const [
              BottomNavigationBarItem(
                icon: Icon(Icons.home_rounded),
                label: 'Home',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.explore_outlined),
                label: 'Explore',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.add_circle_rounded, size: 34, color: _purple),
                label: 'Add',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.video_library_outlined),
                label: 'Library',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.download_for_offline_outlined),
                label: 'Downloads',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _YoutubePlayerDialog extends StatefulWidget {
  const _YoutubePlayerDialog({
    required this.item,
    required this.videoId,
    required this.playlistId,
  });

  final PlayItem item;
  final String? videoId;
  final String? playlistId;

  @override
  State<_YoutubePlayerDialog> createState() => _YoutubePlayerDialogState();
}

class _YoutubePlayerDialogState extends State<_YoutubePlayerDialog> {
  late final YoutubePlayerController _controller;

  @override
  void initState() {
    super.initState();
    _controller = YoutubePlayerController(
      params: const YoutubePlayerParams(
        showControls: true,
        showFullscreenButton: true,
      ),
    );
    if (widget.videoId case final videoId?) {
      _controller.loadVideoById(videoId: videoId);
    } else if (widget.playlistId case final playlistId?) {
      _controller.loadPlaylist(list: [playlistId]);
    }
  }

  @override
  void dispose() {
    _controller.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF0B1020),
      insetPadding: const EdgeInsets.all(20),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 820),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.item.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Close player',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close_rounded),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: YoutubePlayer(
                  controller: _controller,
                  aspectRatio: 16 / 9,
                ),
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: () async {
                    final messenger = ScaffoldMessenger.of(context);
                    final opened = await launchUrl(
                      Uri.parse(widget.item.videoUrl),
                    );
                    if (!opened && mounted) {
                      messenger.showSnackBar(
                        const SnackBar(
                          content: Text('Could not open YouTube.'),
                        ),
                      );
                    }
                  },
                  icon: const Icon(Icons.open_in_new_rounded),
                  label: const Text('Open on YouTube'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    required this.onAbout,
    required this.onExplore,
    required this.onPlay,
    required this.onLibrary,
    required this.onDownload,
    required this.library,
    required this.downloads,
    super.key,
  });

  final VoidCallback onAbout;
  final VoidCallback onExplore;
  final ValueChanged<PlayItem> onPlay;
  final ValueChanged<PlayItem> onLibrary;
  final ValueChanged<PlayItem> onDownload;
  final Set<String> library;
  final Set<String> downloads;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const _categories = ['All', 'Music', 'Trending', 'Gaming', 'Live'];
  final _searchController = TextEditingController();
  String _selectedCategory = 'All';
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<PlayItem> get _filteredItems => _catalog.where((item) {
        final matchesCategory =
            _selectedCategory == 'All' || item.category == _selectedCategory;
        final searchable =
            '${item.title} ${item.creator} ${item.category}'.toLowerCase();
        return matchesCategory && searchable.contains(_query.toLowerCase());
      }).toList();

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      key: const PageStorageKey('home-scroll'),
      slivers: [
        SliverToBoxAdapter(
          child: _PageFrame(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _TopBar(onAbout: widget.onAbout),
                const SizedBox(height: 24),
                _SearchField(
                  controller: _searchController,
                  onChanged: (value) => setState(() => _query = value.trim()),
                ),
                const SizedBox(height: 18),
                SizedBox(
                  height: 42,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _categories.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 9),
                    itemBuilder: (context, index) {
                      final category = _categories[index];
                      final selected = category == _selectedCategory;
                      return _CategoryChip(
                        label: category,
                        selected: selected,
                        onTap: () =>
                            setState(() => _selectedCategory = category),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 28),
                _SectionHeading(
                  title: _query.isEmpty ? 'Trending Music' : 'Search results',
                  action: 'See all',
                  onAction: widget.onExplore,
                ),
                const SizedBox(height: 15),
                SizedBox(
                  height: 222,
                  child: _filteredItems.isEmpty
                      ? const _EmptyInline(
                          message: 'No picks match that search.')
                      : ListView.separated(
                          scrollDirection: Axis.horizontal,
                          itemCount: _filteredItems.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(width: 13),
                          itemBuilder: (context, index) {
                            final item = _filteredItems[index];
                            return _TrendingCard(
                              item: item,
                              onTap: () => widget.onPlay(item),
                            );
                          },
                        ),
                ),
                const SizedBox(height: 27),
                _SectionHeading(
                  title: 'Quick play',
                  action: 'Explore',
                  onAction: widget.onExplore,
                ),
                const SizedBox(height: 8),
                ..._filteredItems.map(
                  (item) => _QuickPlayTile(
                    item: item,
                    isSaved: widget.library.contains(item.title),
                    isDownloaded: widget.downloads.contains(item.title),
                    onPlay: () => widget.onPlay(item),
                    onLibrary: () => widget.onLibrary(item),
                    onDownload: () => widget.onDownload(item),
                  ),
                ),
                const SizedBox(height: 22),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class ExploreScreen extends StatefulWidget {
  const ExploreScreen({
    required this.onPlay,
    required this.onLibrary,
    required this.library,
    super.key,
  });

  final ValueChanged<PlayItem> onPlay;
  final ValueChanged<PlayItem> onLibrary;
  final Set<String> library;

  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final results = _catalog
        .where(
          (item) => '${item.title} ${item.creator} ${item.category}'
              .toLowerCase()
              .contains(_query.toLowerCase()),
        )
        .toList();
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: _PageFrame(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _TopBar(),
                const SizedBox(height: 26),
                const Text(
                  'Explore',
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Find your next favorite thing.',
                  style: TextStyle(color: _muted),
                ),
                const SizedBox(height: 20),
                _SearchField(
                  hint: 'Search music, creators, and more',
                  onChanged: (value) => setState(() => _query = value.trim()),
                ),
                const SizedBox(height: 18),
                ...results.map(
                  (item) => _QuickPlayTile(
                    item: item,
                    isSaved: widget.library.contains(item.title),
                    onPlay: () => widget.onPlay(item),
                    onLibrary: () => widget.onLibrary(item),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class CollectionScreen extends StatelessWidget {
  const CollectionScreen({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.items,
    required this.emptyTitle,
    required this.emptyDetail,
    required this.onPlay,
    required this.onLibrary,
    super.key,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final List<PlayItem> items;
  final String emptyTitle;
  final String emptyDetail;
  final ValueChanged<PlayItem> onPlay;
  final ValueChanged<PlayItem> onLibrary;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: _PageFrame(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _TopBar(),
                const SizedBox(height: 26),
                Text(title,
                    style: const TextStyle(
                        fontSize: 30, fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                Text(subtitle, style: const TextStyle(color: _muted)),
                const SizedBox(height: 26),
                if (items.isEmpty)
                  _EmptyCollection(
                    icon: icon,
                    title: emptyTitle,
                    detail: emptyDetail,
                  )
                else
                  ...items.map(
                    (item) => _QuickPlayTile(
                      item: item,
                      isSaved: true,
                      onPlay: () => onPlay(item),
                      onLibrary: () => onLibrary(item),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class AddContentScreen extends StatelessWidget {
  const AddContentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        SliverFillRemaining(
          hasScrollBody: false,
          child: _PageFrame(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _TopBar(),
                const SizedBox(height: 28),
                const Text(
                  'Create your space',
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Choose what you would like to add.',
                  style: TextStyle(color: _muted),
                ),
                const SizedBox(height: 24),
                const _CreateOption(
                  icon: Icons.playlist_add_rounded,
                  title: 'Make a playlist',
                  detail: 'Collect the picks you love in one place.',
                ),
                const SizedBox(height: 12),
                const _CreateOption(
                  icon: Icons.queue_music_rounded,
                  title: 'Start a mix',
                  detail: 'A personal mix feature is coming soon.',
                ),
                const Spacer(),
                const Padding(
                  padding: EdgeInsets.only(bottom: 24),
                  child: Text(
                    'Your own uploads and playback sources can be connected '
                    'when a supported provider is configured.',
                    style: TextStyle(color: _muted, height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({this.onAbout});

  final VoidCallback? onAbout;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const CustomPaint(
          size: Size(38, 38),
          painter: _AaruPlayMarkPainter(),
        ),
        const SizedBox(width: 10),
        const Text(
          AppConfig.appName,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w900,
            letterSpacing: 0.8,
            shadows: [
              Shadow(color: Color(0x4D55DDF5), blurRadius: 16),
            ],
          ),
        ),
        const Spacer(),
        IconButton(
          tooltip: 'About and settings',
          onPressed: onAbout ?? () {},
          icon: const Icon(Icons.person_outline_rounded),
          style: IconButton.styleFrom(
            backgroundColor: _surfaceRaised,
            foregroundColor: Colors.white,
          ),
        ),
      ],
    );
  }
}

class _AaruPlayMarkPainter extends CustomPainter {
  const _AaruPlayMarkPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final tile = RRect.fromRectAndRadius(
      Offset.zero & size,
      Radius.circular(size.width * 0.24),
    );
    canvas.drawRRect(tile, Paint()..color = const Color(0xFF16152B));
    canvas.drawRRect(
      tile,
      Paint()
        ..color = const Color(0xFF00E5FF)
        ..style = PaintingStyle.stroke
        ..strokeWidth = size.width * 0.03,
    );

    final play = Path()
      ..moveTo(size.width * 0.35, size.height * 0.30)
      ..lineTo(size.width * 0.70, size.height * 0.50)
      ..lineTo(size.width * 0.35, size.height * 0.70);
    canvas.drawPath(
      play,
      Paint()
        ..color = const Color(0xFFFF2A85)
        ..style = PaintingStyle.stroke
        ..strokeWidth = size.width * 0.07
        ..strokeJoin = StrokeJoin.round
        ..strokeCap = StrokeCap.round,
    );

    final wave = Path()
      ..moveTo(size.width * 0.55, size.height * 0.50)
      ..quadraticBezierTo(
        size.width * 0.60,
        size.height * 0.42,
        size.width * 0.65,
        size.height * 0.50,
      )
      ..quadraticBezierTo(
        size.width * 0.70,
        size.height * 0.58,
        size.width * 0.75,
        size.height * 0.50,
      );
    canvas.drawPath(
      wave,
      Paint()
        ..color = const Color(0xFF00E5FF)
        ..style = PaintingStyle.stroke
        ..strokeWidth = size.width * 0.03
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(covariant _AaruPlayMarkPainter oldDelegate) => false;
}

class _PageFrame extends StatelessWidget {
  const _PageFrame({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1120),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 8),
          child: child,
        ),
      ),
    );
  }
}

class _SearchField extends StatefulWidget {
  const _SearchField({
    this.controller,
    this.hint = 'Search songs, creators, and more',
    required this.onChanged,
  });

  final TextEditingController? controller;
  final String hint;
  final ValueChanged<String> onChanged;

  @override
  State<_SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<_SearchField> {
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode()..addListener(_handleFocusChange);
  }

  @override
  void dispose() {
    _focusNode
      ..removeListener(_handleFocusChange)
      ..dispose();
    super.dispose();
  }

  void _handleFocusChange() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final focused = _focusNode.hasFocus;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: focused
              ? [_cyan.withValues(alpha: 0.42), _purple.withValues(alpha: 0.3)]
              : [
                  Colors.white.withValues(alpha: 0.1),
                  _blue.withValues(alpha: 0.2)
                ],
        ),
        boxShadow: focused
            ? [
                BoxShadow(
                  color: _cyan.withValues(alpha: 0.24),
                  blurRadius: 24,
                  spreadRadius: 1,
                ),
              ]
            : const [],
      ),
      padding: const EdgeInsets.all(1),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: BackdropFilter(
          filter: ui.ImageFilter.blur(sigmaX: 12, sigmaY: 12),
          child: TextField(
            controller: widget.controller,
            focusNode: _focusNode,
            onChanged: widget.onChanged,
            textInputAction: TextInputAction.search,
            style: const TextStyle(color: Colors.white, fontSize: 14),
            decoration: InputDecoration(
              hintText: widget.hint,
              hintStyle: const TextStyle(color: _muted, fontSize: 14),
              prefixIcon: const Icon(Icons.search_rounded, color: _cyan),
              filled: true,
              fillColor: const Color(0xE60C1220),
              contentPadding: const EdgeInsets.symmetric(vertical: 15),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _CategoryChip extends StatelessWidget {
  const _CategoryChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: selected
            ? const LinearGradient(colors: [_cyan, _blue])
            : const LinearGradient(
                colors: [Color(0xAA18243A), Color(0xAA101827)],
              ),
        border: Border.all(
          color: selected
              ? _cyan.withValues(alpha: 0.9)
              : _blue.withValues(alpha: 0.32),
        ),
        boxShadow: selected
            ? [
                BoxShadow(
                  color: _cyan.withValues(alpha: 0.25),
                  blurRadius: 16,
                  spreadRadius: 0.5,
                ),
              ]
            : [
                BoxShadow(
                  color: _blue.withValues(alpha: 0.08),
                  blurRadius: 10,
                ),
              ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(22),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
            child: Text(
              label,
              style: TextStyle(
                color: selected ? _background : Colors.white,
                fontSize: 11,
                letterSpacing: 0.8,
                fontWeight: FontWeight.w800,
                shadows: selected
                    ? const []
                    : [
                        Shadow(
                            color: _blue.withValues(alpha: 0.4), blurRadius: 8)
                      ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({
    required this.title,
    required this.action,
    required this.onAction,
  });

  final String title;
  final String action;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 3,
          height: 19,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [_cyan, _purple],
            ),
            boxShadow: [
              BoxShadow(
                color: _cyan.withValues(alpha: 0.6),
                blurRadius: 10,
              ),
            ],
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.35,
              shadows: [Shadow(color: Color(0x3355DDF5), blurRadius: 12)],
            ),
          ),
        ),
        TextButton(
          onPressed: onAction,
          child: Text(
            action,
            style: const TextStyle(color: _cyan, fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}

class _TrendingCard extends StatelessWidget {
  const _TrendingCard({required this.item, required this.onTap});

  final PlayItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 228,
      child: _GlassPanel(
        radius: 17,
        glow: _blue,
        padding: const EdgeInsets.all(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  height: 132,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: item.colors,
                    ),
                    border:
                        Border.all(color: Colors.white.withValues(alpha: 0.12)),
                  ),
                  child: Stack(
                    children: [
                      Positioned.fill(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                _cyan.withValues(alpha: 0.08),
                                Colors.transparent,
                                _purple.withValues(alpha: 0.16),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        right: -14,
                        top: -25,
                        child: Icon(
                          item.icon,
                          size: 132,
                          color: Colors.white.withValues(alpha: 0.11),
                        ),
                      ),
                      Center(
                        child: Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: const Color(0x99070D1B),
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: _cyan.withValues(alpha: 0.68),
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: _cyan.withValues(alpha: 0.35),
                                blurRadius: 18,
                              ),
                            ],
                          ),
                          child: const Icon(
                            Icons.play_arrow_rounded,
                            color: Colors.white,
                            size: 32,
                          ),
                        ),
                      ),
                      Positioned(
                        right: 9,
                        bottom: 9,
                        child: _DurationBadge(text: item.duration),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 9),
              Text(
                item.title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                '${item.performer}  •  ${item.creator}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: _muted, fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickPlayTile extends StatelessWidget {
  const _QuickPlayTile({
    required this.item,
    required this.isSaved,
    required this.onPlay,
    required this.onLibrary,
    this.isDownloaded = false,
    this.onDownload,
  });

  final PlayItem item;
  final bool isSaved;
  final bool isDownloaded;
  final VoidCallback onPlay;
  final VoidCallback onLibrary;
  final VoidCallback? onDownload;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: _GlassPanel(
        radius: 15,
        glow: isSaved ? _purple : _cyan,
        padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 7),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onPlay,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 2),
              child: Row(
                children: [
                  Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(13),
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: item.colors,
                      ),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.16),
                      ),
                    ),
                    child: Icon(item.icon, color: Colors.white, size: 24),
                  ),
                  const SizedBox(width: 13),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${item.performer}  •  ${item.creator}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: _muted, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip:
                        isSaved ? 'Remove from library' : 'Save to library',
                    onPressed: onLibrary,
                    icon: Icon(
                      isSaved
                          ? Icons.favorite_rounded
                          : Icons.favorite_border_rounded,
                      color: isSaved ? _purple : _muted,
                      size: 21,
                    ),
                  ),
                  if (onDownload != null)
                    IconButton(
                      tooltip: isDownloaded
                          ? 'Remove offline item'
                          : 'Add to offline list',
                      onPressed: onDownload,
                      icon: Icon(
                        isDownloaded
                            ? Icons.download_done_rounded
                            : Icons.download_for_offline_outlined,
                        color: isDownloaded ? _cyan : _muted,
                        size: 21,
                      ),
                    )
                  else
                    const SizedBox(width: 6),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DurationBadge extends StatelessWidget {
  const _DurationBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.62),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      ),
    );
  }
}

class _EmptyInline extends StatelessWidget {
  const _EmptyInline({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(message, style: const TextStyle(color: _muted)),
    );
  }
}

class _EmptyCollection extends StatelessWidget {
  const _EmptyCollection({
    required this.icon,
    required this.title,
    required this.detail,
  });

  final IconData icon;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 42),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Icon(icon, size: 38, color: _purple),
          const SizedBox(height: 14),
          Text(title,
              style:
                  const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 7),
          Text(
            detail,
            textAlign: TextAlign.center,
            style: const TextStyle(color: _muted, height: 1.5),
          ),
        ],
      ),
    );
  }
}

class _CreateOption extends StatelessWidget {
  const _CreateOption({
    required this.icon,
    required this.title,
    required this.detail,
  });

  final IconData icon;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(17),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: _purple.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(icon, color: _purple),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 5),
                Text(detail,
                    style: const TextStyle(color: _muted, fontSize: 12)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: _muted),
        ],
      ),
    );
  }
}
