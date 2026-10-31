import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../l10n/app_localizations.dart';
import '../models/identification.dart';
import 'labels.dart';

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 24, 4, 10),
        child: Row(children: [
          Expanded(child: Text(text, style: Theme.of(context).textTheme.titleMedium)),
          ?trailing,
        ]),
      );
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.child, this.padding = const EdgeInsets.all(16), this.onTap});
  final Widget child;
  final EdgeInsets padding;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(onTap: onTap, child: Padding(padding: padding, child: child)),
      );
}

class LabeledValue extends StatelessWidget {
  const LabeledValue(this.label, this.value, {super.key, this.italic = false});
  final String label;
  final String? value;
  final bool italic;

  @override
  Widget build(BuildContext context) {
    if (value == null || value!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 120, child: Text(label, style: const TextStyle(color: AppColors.muted))),
        Expanded(child: Text(value!, style: TextStyle(fontStyle: italic ? FontStyle.italic : null, fontWeight: FontWeight.w500))),
      ]),
    );
  }
}

Color matchLevelColor(String level) => switch (level) {
      'high_match' => AppColors.levelHigh,
      'moderate_match' => AppColors.levelModerate,
      'low_match' => AppColors.levelLow,
      _ => AppColors.levelNone,
    };

IconData matchLevelIcon(String level) => switch (level) {
      'high_match' => Icons.verified_outlined,
      'moderate_match' => Icons.check_circle_outline,
      'low_match' => Icons.help_outline,
      'insufficient_image' => Icons.no_photography_outlined,
      'not_compatible' => Icons.block_outlined,
      _ => Icons.help_center_outlined,
    };

/// Qualitative certainty level. Always shows a text label, never a percentage.
class MatchLevelBadge extends StatelessWidget {
  const MatchLevelBadge(this.level, {super.key});
  final String level;

  @override
  Widget build(BuildContext context) {
    final color = matchLevelColor(level);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(matchLevelIcon(level), size: 18, color: color),
        const SizedBox(width: 6),
        Flexible(child: Text(AppLocalizations.of(context).matchLevel(level), style: TextStyle(color: color, fontWeight: FontWeight.w700))),
      ]),
    );
  }
}

class TagChip extends StatelessWidget {
  const TagChip(this.label, {super.key, this.icon, this.color});
  final String label;
  final IconData? icon;
  final Color? color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(color: (color ?? AppColors.sand).withValues(alpha: 0.35), borderRadius: BorderRadius.circular(8)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icon != null) ...[Icon(icon, size: 15, color: AppColors.graphite), const SizedBox(width: 4)],
          Flexible(child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
        ]),
      );
}

class VerificationTag extends StatelessWidget {
  const VerificationTag({super.key, required this.verified});
  final bool verified;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return TagChip(
      verified ? t.expertVerified : t.notExpertVerified,
      icon: verified ? Icons.verified_user_outlined : Icons.pending_outlined,
      color: verified ? AppColors.levelHigh : AppColors.sand,
    );
  }
}

class NoticeList extends StatelessWidget {
  const NoticeList(this.notices, {super.key});
  final List<Notice> notices;

  @override
  Widget build(BuildContext context) {
    if (notices.isEmpty) return const SizedBox.shrink();
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.warningBg, borderRadius: BorderRadius.circular(16)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        for (final notice in notices)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Padding(padding: EdgeInsets.only(top: 2), child: Icon(Icons.info_outline, size: 18, color: AppColors.warning)),
              const SizedBox(width: 8),
              Expanded(child: Text(notice.message, style: const TextStyle(color: AppColors.graphite))),
            ]),
          ),
      ]),
    );
  }
}

class DemoBanner extends StatelessWidget {
  const DemoBanner({super.key});

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        color: AppColors.warning,
        child: Text(AppLocalizations.of(context).demoBanner,
            textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
      );
}

class CatalogThumb extends StatelessWidget {
  const CatalogThumb({super.key, this.url, this.size = 56, this.icon = Icons.image_outlined});
  final String? url;
  final double size;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final placeholder = Container(
      width: size,
      height: size,
      color: AppColors.sandLight,
      child: Icon(icon, color: AppColors.olive, size: size * 0.45),
    );
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: url == null
          ? placeholder
          : CachedNetworkImage(imageUrl: url!, width: size, height: size, fit: BoxFit.cover, errorWidget: (_, _, _) => placeholder),
    );
  }
}

class LoadingView extends StatelessWidget {
  const LoadingView({super.key});

  @override
  Widget build(BuildContext context) => const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()));
}

class MessageView extends StatelessWidget {
  const MessageView({super.key, required this.icon, required this.message, this.actionLabel, this.onAction});
  final IconData icon;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 48, color: AppColors.olive),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge),
            if (actionLabel != null) ...[
              const SizedBox(height: 20),
              SizedBox(width: 220, child: OutlinedButton(onPressed: onAction, child: Text(actionLabel!))),
            ],
          ]),
        ),
      );
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.error, this.onRetry});
  final Object error;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return MessageView(icon: Icons.cloud_off_outlined, message: t.failure(error), actionLabel: onRetry == null ? null : t.retry, onAction: onRetry);
  }
}

/// Organism and fly icons used across the app.
const organismIcon = Icons.pest_control_outlined;
const flyIcon = Icons.phishing;

IconData organismGroupIcon(String group) => switch (group) {
      'fish' => Icons.set_meal_outlined,
      'crustacean' || 'annelid' || 'mollusc' => Icons.water_outlined,
      _ => organismIcon,
    };
