import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final config = ref.watch(appConfigProvider);
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 28, 20, 24),
          children: [
            Row(children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: AppColors.forest, borderRadius: BorderRadius.circular(14)),
                child: const Icon(flyIcon, color: AppColors.sand, size: 26),
              ),
              const SizedBox(width: 12),
              Text(config.appName, style: Theme.of(context).textTheme.headlineMedium),
            ]),
            const SizedBox(height: 10),
            Text(t.homeTagline, style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.muted)),
            const SizedBox(height: 28),
            _FeatureCard(
              key: const Key('home-identify-organism'),
              icon: organismIcon,
              title: t.identifyOrganismTitle,
              subtitle: t.identifyOrganismSubtitle,
              background: AppColors.forest,
              foreground: Colors.white,
              onTap: () => context.push('/identify/organism'),
            ),
            const SizedBox(height: 14),
            _FeatureCard(
              key: const Key('home-identify-fly'),
              icon: flyIcon,
              title: t.identifyFlyTitle,
              subtitle: t.identifyFlySubtitle,
              background: AppColors.olive,
              foreground: Colors.white,
              onTap: () => context.push('/identify/fly'),
            ),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(
                child: _SmallCard(key: const Key('home-catalog'), icon: Icons.menu_book_outlined, title: t.catalogTitle, subtitle: t.catalogSubtitle, onTap: () => context.push('/catalog')),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: _SmallCard(key: const Key('home-history'), icon: Icons.history, title: t.historyTitle, subtitle: t.historySubtitle, onTap: () => context.push('/history')),
              ),
            ]),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  const _FeatureCard({super.key, required this.icon, required this.title, required this.subtitle, required this.background, required this.foreground, required this.onTap});

  final IconData icon;
  final String title;
  final String subtitle;
  final Color background;
  final Color foreground;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: background,
        borderRadius: BorderRadius.circular(22),
        child: InkWell(
          borderRadius: BorderRadius.circular(22),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(22),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(16)),
                child: Icon(icon, color: foreground, size: 34),
              ),
              const SizedBox(width: 18),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(color: foreground)),
                  const SizedBox(height: 6),
                  Text(subtitle, style: TextStyle(color: foreground.withValues(alpha: 0.85), height: 1.35)),
                ]),
              ),
              Icon(Icons.arrow_forward_ios, color: foreground.withValues(alpha: 0.7), size: 18),
            ]),
          ),
        ),
      );
}

class _SmallCard extends StatelessWidget {
  const _SmallCard({super.key, required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InfoCard(
        onTap: onTap,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, color: AppColors.forest, size: 28),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
        ]),
      );
}
