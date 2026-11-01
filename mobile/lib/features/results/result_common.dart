import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../widgets/common.dart';

/// Photo + certainty header shared by both result screens.
class ResultHeader extends StatelessWidget {
  const ResultHeader({super.key, required this.result, this.photo});
  final IdentificationResult result;
  final Uint8List? photo;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (photo != null) ...[
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Image.memory(photo!, height: 220, width: double.infinity, fit: BoxFit.cover),
        ),
        const SizedBox(height: 16),
      ],
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: fly.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: fly.hairline)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
            Text(t.certainty, style: context.secondaryStyle),
            MatchLevelBadge(result.matchLevel),
          ]),
          const SizedBox(height: 10),
          Text(t.certaintyExplanation, style: context.captionStyle),
        ]),
      ),
      if (result.warnings.isNotEmpty) ...[const SizedBox(height: 14), NoticeList(result.warnings)],
    ]);
  }
}

class SourcesFooter extends StatelessWidget {
  const SourcesFooter(this.result, {super.key});
  final IdentificationResult result;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    if (result.sources.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 28),
      child: Text(
        '${t.sources}: ${result.sources.map((s) => s.detail == null ? s.name : '${s.name} (${s.detail})').join(' · ')}',
        style: context.captionStyle,
      ),
    );
  }
}

class ResultActions extends StatelessWidget {
  const ResultActions({super.key, required this.onNewPhoto, required this.onHome});
  final VoidCallback onNewPhoto;
  final VoidCallback onHome;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    return DecoratedBox(
      decoration: BoxDecoration(color: fly.canvas, border: Border(top: BorderSide(color: fly.hairline))),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
          child: Row(children: [
            Expanded(child: OutlinedButton(onPressed: onHome, child: Text(t.backHome))),
            const SizedBox(width: 12),
            Expanded(child: FilledButton(onPressed: onNewPhoto, child: Text(t.newPhoto))),
          ]),
        ),
      ),
    );
  }
}
