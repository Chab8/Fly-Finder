import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import '../../widgets/rise_rings.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    final config = ref.watch(appConfigProvider);
    final bottomInset = MediaQuery.paddingOf(context).bottom;
    return Scaffold(
      body: AnnotatedRegion<SystemUiOverlayStyle>(
        value: (fly.isDark ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark).copyWith(statusBarColor: Colors.transparent),
        child: ListView(
          padding: EdgeInsets.only(bottom: bottomInset + 28),
          children: [
            _Header(title: config.appName, tagline: t.homeTagline),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                const SizedBox(height: 8),
                // The insect-to-fly flow is the main job of the app, so it carries the brand fill.
                _ActionCard(
                  key: const Key('home-identify-organism'),
                  icon: organismIcon,
                  title: t.identifyOrganismTitle,
                  subtitle: t.identifyOrganismSubtitle,
                  primary: true,
                  onTap: () => context.push('/identify/organism'),
                ),
                const SizedBox(height: 12),
                _ActionCard(
                  key: const Key('home-identify-fly'),
                  icon: flyIcon,
                  title: t.identifyFlyTitle,
                  subtitle: t.identifyFlySubtitle,
                  primary: false,
                  onTap: () => context.push('/identify/fly'),
                ),
                const SizedBox(height: 24),
                Card(
                  clipBehavior: Clip.antiAlias,
                  child: Column(children: [
                    _NavRow(key: const Key('home-catalog'), icon: Icons.menu_book_outlined, title: t.catalogTitle, subtitle: t.catalogSubtitle, onTap: () => context.push('/catalog')),
                    Divider(indent: 68, color: fly.hairline),
                    _NavRow(key: const Key('home-history'), icon: Icons.history, title: t.historyTitle, subtitle: t.historySubtitle, onTap: () => context.push('/history')),
                  ]),
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}

/// Title block with the rise rings spreading from the top-right corner. Branding defers to
/// content: no logo tile, just the name and one line.
class _Header extends StatelessWidget {
  const _Header({required this.title, required this.tagline});
  final String title;
  final String tagline;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    final top = MediaQuery.paddingOf(context).top;
    final width = MediaQuery.sizeOf(context).width;
    return ClipRect(
      child: Stack(children: [
        Positioned.fill(
          child: ExcludeSemantics(
            child: CustomPaint(
              painter: RiseRingsPainter(
                color: fly.ripple,
                progress: 0.1,
                rings: 7,
                squash: 0.5,
                anchor: const Alignment(0.82, -0.35),
                radius: width * 0.95,
                opacity: fly.isDark ? 0.34 : 0.3,
              ),
            ),
          ),
        ),
        Padding(
          padding: EdgeInsets.fromLTRB(24, top + 44, 24, 28),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Semantics(header: true, child: Text(title, style: Theme.of(context).textTheme.displaySmall)),
            const SizedBox(height: 10),
            Text(
              tagline,
              style: TextStyle(fontFamily: AppFonts.serif, fontStyle: FontStyle.italic, fontSize: 19, height: 1.35, color: fly.inkSecondary),
            ),
          ]),
        ),
      ]),
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({super.key, required this.icon, required this.title, required this.subtitle, required this.primary, required this.onTap});

  final IconData icon;
  final String title;
  final String subtitle;
  final bool primary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    final foreground = primary ? fly.onRiver : fly.ink;
    final secondary = primary ? fly.onRiver.withValues(alpha: 0.88) : fly.inkSecondary;
    const radius = BorderRadius.all(Radius.circular(22));
    return Material(
      color: primary ? fly.river : fly.card,
      shape: RoundedRectangleBorder(borderRadius: radius, side: primary ? BorderSide.none : BorderSide(color: fly.hairline)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(color: primary ? fly.onRiver.withValues(alpha: 0.16) : fly.riverTint, shape: BoxShape.circle),
              child: Icon(icon, color: primary ? fly.onRiver : fly.accent, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: context.serif(21, color: foreground)),
                const SizedBox(height: 4),
                Text(subtitle, style: context.bodyStyle.copyWith(color: secondary)),
              ]),
            ),
            const SizedBox(width: 8),
            Icon(Icons.chevron_right, color: secondary, size: 26),
          ]),
        ),
      ),
    );
  }
}

class _NavRow extends StatelessWidget {
  const _NavRow({super.key, required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: fly.tint, borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, color: fly.accent, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              Text(subtitle, style: context.captionStyle),
            ]),
          ),
          Icon(Icons.chevron_right, color: fly.inkSecondary),
        ]),
      ),
    );
  }
}
