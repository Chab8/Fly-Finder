import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../l10n/app_localizations.dart';
import '../models/identification.dart';
import 'labels.dart';

/// Chapter heading in the field-guide style: serif title followed by a hairline rule.
class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(2, 32, 2, 12),
        child: Row(children: [
          Flexible(child: Semantics(header: true, child: Text(text, style: context.serif(20)))),
          const SizedBox(width: 12),
          Expanded(child: Divider(color: context.fly.hairline)),
          if (trailing != null) ...[const SizedBox(width: 8), trailing!],
        ]),
      );
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.child, this.padding = const EdgeInsets.all(16), this.onTap, this.highlight = false});
  final Widget child;
  final EdgeInsets padding;
  final VoidCallback? onTap;

  /// Soft green surface for the primary result on a screen.
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    return Card(
      clipBehavior: Clip.antiAlias,
      color: highlight ? fly.riverTint : null,
      shape: RoundedRectangleBorder(
        borderRadius: const BorderRadius.all(Radius.circular(16)),
        side: BorderSide(color: highlight ? fly.accent.withValues(alpha: 0.35) : fly.hairline),
      ),
      child: InkWell(onTap: onTap, child: Padding(padding: padding, child: child)),
    );
  }
}

/// Label above its value. Proportional columns so large text sizes never clip the label.
class LabeledValue extends StatelessWidget {
  const LabeledValue(this.label, this.value, {super.key, this.italic = false});
  final String label;
  final String? value;
  final bool italic;

  @override
  Widget build(BuildContext context) {
    if (value == null || value!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(flex: 4, child: Text(label, style: context.secondaryStyle)),
        const SizedBox(width: 12),
        Expanded(
          flex: 6,
          child: Text(
            value!,
            style: italic ? context.species(16) : context.bodyStyle.copyWith(fontWeight: FontWeight.w600, fontSize: 16),
          ),
        ),
      ]),
    );
  }
}

/// A short bullet list item with a hanging indent.
class BulletText extends StatelessWidget {
  const BulletText(this.text, {super.key, this.style});
  final String text;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.only(top: 8, right: 10),
            child: Container(width: 5, height: 5, decoration: BoxDecoration(color: context.fly.accent, shape: BoxShape.circle)),
          ),
          Expanded(child: Text(text, style: style ?? context.bodyStyle)),
        ]),
      );
}

IconData matchLevelIcon(String level) => switch (level) {
      'high_match' => Icons.verified_outlined,
      'moderate_match' => Icons.check_circle_outline,
      'low_match' => Icons.help_outline,
      'insufficient_image' => Icons.no_photography_outlined,
      'not_compatible' => Icons.block_outlined,
      _ => Icons.help_center_outlined,
    };

/// Qualitative certainty level. Always shows a text label and an icon, never colour alone,
/// and never a percentage.
class MatchLevelBadge extends StatelessWidget {
  const MatchLevelBadge(this.level, {super.key});
  final String level;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    final color = fly.level(level);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(color: color.withValues(alpha: fly.tintAlpha), borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(matchLevelIcon(level), size: 18, color: color),
        const SizedBox(width: 6),
        Flexible(child: Text(AppLocalizations.of(context).matchLevel(level), style: context.bodyStyle.copyWith(color: color, fontWeight: FontWeight.w700))),
      ]),
    );
  }
}

/// neutral: plain information. good: verified or documented. brass: tackle (hook sizes, shops).
enum TagTone { neutral, good, brass }

class TagChip extends StatelessWidget {
  const TagChip(this.label, {super.key, this.icon, this.tone = TagTone.neutral});
  final String label;
  final IconData? icon;
  final TagTone tone;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    final (Color background, Color foreground) = switch (tone) {
      TagTone.neutral => (fly.tint, fly.ink),
      TagTone.good => (fly.levelHigh.withValues(alpha: fly.tintAlpha), fly.levelHigh),
      TagTone.brass => (fly.brass.withValues(alpha: fly.tintAlpha), fly.brass),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        if (icon != null) ...[Icon(icon, size: 15, color: foreground), const SizedBox(width: 5)],
        Flexible(child: Text(label, style: (Theme.of(context).textTheme.bodySmall ?? const TextStyle()).copyWith(color: foreground, fontWeight: FontWeight.w600))),
      ]),
    );
  }
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
      tone: verified ? TagTone.good : TagTone.neutral,
    );
  }
}

class NoticeList extends StatelessWidget {
  const NoticeList(this.notices, {super.key});
  final List<Notice> notices;

  @override
  Widget build(BuildContext context) {
    if (notices.isEmpty) return const SizedBox.shrink();
    final fly = context.fly;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: fly.warningBg, borderRadius: BorderRadius.circular(14)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        for (final notice in notices)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Padding(padding: const EdgeInsets.only(top: 2), child: Icon(Icons.info_outline, size: 20, color: fly.warning)),
              const SizedBox(width: 10),
              Expanded(child: Text(notice.message, style: context.bodyStyle)),
            ]),
          ),
      ]),
    );
  }
}

class DemoBanner extends StatelessWidget {
  const DemoBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 9, horizontal: 16),
      color: fly.warning,
      child: Text(
        AppLocalizations.of(context).demoBanner,
        textAlign: TextAlign.center,
        style: context.bodyStyle.copyWith(color: fly.onWarning, fontWeight: FontWeight.w700),
      ),
    );
  }
}

/// Small "specimen plate": a hairline-framed photo, or an icon when there is no photo.
class CatalogThumb extends StatelessWidget {
  const CatalogThumb({super.key, this.url, this.size = 56, this.icon = Icons.image_outlined});
  final String? url;
  final double size;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final fly = context.fly;
    final placeholder = Center(child: Icon(icon, color: fly.accent, size: size * 0.45));
    return ExcludeSemantics(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: fly.tint,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: fly.hairline),
        ),
        clipBehavior: Clip.antiAlias,
        child: url == null
            ? placeholder
            : CachedNetworkImage(imageUrl: url!, width: size, height: size, fit: BoxFit.cover, errorWidget: (_, _, _) => placeholder),
      ),
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
  Widget build(BuildContext context) {
    final fly = context.fly;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(color: fly.riverTint, shape: BoxShape.circle),
            child: Icon(icon, size: 34, color: fly.accent),
          ),
          const SizedBox(height: 18),
          Text(message, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge),
          if (actionLabel != null) ...[
            const SizedBox(height: 22),
            SizedBox(width: 220, child: OutlinedButton(onPressed: onAction, child: Text(actionLabel!))),
          ],
        ]),
      ),
    );
  }
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
