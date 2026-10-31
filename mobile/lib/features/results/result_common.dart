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
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (photo != null)
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Image.memory(photo!, height: 220, width: double.infinity, fit: BoxFit.cover),
        ),
      const SizedBox(height: 16),
      Wrap(spacing: 10, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
        Text(t.certainty, style: const TextStyle(color: AppColors.muted)),
        MatchLevelBadge(result.matchLevel),
      ]),
      const SizedBox(height: 6),
      Text(t.certaintyExplanation, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
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
      padding: const EdgeInsets.only(top: 24),
      child: Text(
        '${t.sources}: ${result.sources.map((s) => s.detail == null ? s.name : '${s.name} (${s.detail})').join(' · ')}',
        style: const TextStyle(color: AppColors.muted, fontSize: 12),
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
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
        child: Row(children: [
          Expanded(child: OutlinedButton(onPressed: onHome, child: Text(t.backHome))),
          const SizedBox(width: 12),
          Expanded(child: FilledButton(onPressed: onNewPhoto, child: Text(t.newPhoto))),
        ]),
      ),
    );
  }
}
