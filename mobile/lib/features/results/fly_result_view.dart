import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../widgets/common.dart';
import '../../widgets/labels.dart';
import '../catalog/product_tile.dart';
import 'result_common.dart';

class FlyResultView extends StatelessWidget {
  const FlyResultView({super.key, required this.result, this.photo});
  final FlyIdentification result;
  final Uint8List? photo;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final primary = result.primary;
    return ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 24), children: [
      ResultHeader(result: result, photo: photo),
      if (primary == null) ...[
        const SizedBox(height: 24),
        MessageView(icon: Icons.search_off, message: t.noIdentification),
      ] else ...[
        SectionTitle(t.primaryIdentification),
        _FlyCandidateCard(candidate: primary, category: result.category, prominent: true),
      ],
      if (result.colors.isNotEmpty || result.features.isNotEmpty) ...[
        SectionTitle(t.characteristics),
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (result.colors.isNotEmpty) Wrap(spacing: 6, runSpacing: 6, children: [for (final c in result.colors) TagChip(c)]),
            for (final feature in result.features) Padding(padding: const EdgeInsets.only(top: 8), child: Text('• $feature')),
          ]),
        ),
      ],
      if (primary?.fly != null) ...[
        SectionTitle(t.imitates),
        if (result.imitates.isEmpty)
          InfoCard(child: Text(t.imitatesNothingDocumented))
        else
          for (final relation in result.imitates)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InfoCard(
                onTap: () => context.push('/organisms/${relation.organism!.id}'),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(relation.organism!.scientificName, style: const TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.w600, fontSize: 16)),
                  if (relation.organism!.commonName != null) Text(relation.organism!.commonName!, style: const TextStyle(color: AppColors.muted)),
                  const SizedBox(height: 8),
                  Wrap(spacing: 6, runSpacing: 6, children: [
                    TagChip(t.stage(relation.lifeStage)),
                    TagChip(t.compatibility(relation.biologicalCompatibility)),
                    VerificationTag(verified: relation.expertVerified),
                  ]),
                ]),
              ),
            ),
      ],
      if (result.aiHints.isNotEmpty) ...[
        SectionTitle(t.aiSuggestions),
        InfoCard(
          child: Wrap(spacing: 6, runSpacing: 6, children: [
            for (final (group, stage, confidence) in result.aiHints) TagChip('$group · ${t.stage(stage)} · ${t.confidence(confidence)}'),
          ]),
        ),
      ],
      if (result.variants.isNotEmpty) ...[
        SectionTitle(t.variants),
        InfoCard(child: Wrap(spacing: 6, runSpacing: 6, children: [for (final v in result.variants) TagChip(v.name)])),
      ],
      if (primary?.fly != null) ...[
        SectionTitle(t.products),
        if (result.products.isEmpty)
          InfoCard(child: Text(t.noProducts))
        else
          for (final product in result.products) Padding(padding: const EdgeInsets.only(bottom: 8), child: ProductTile(product)),
      ],
      if (result.alternatives.isNotEmpty) ...[
        SectionTitle(t.alternatives),
        for (final alt in result.alternatives) Padding(padding: const EdgeInsets.only(bottom: 8), child: _FlyCandidateCard(candidate: alt)),
      ],
      SourcesFooter(result),
    ]);
  }
}

class _FlyCandidateCard extends StatelessWidget {
  const _FlyCandidateCard({required this.candidate, this.category, this.prominent = false});
  final FlyCandidate candidate;
  final String? category;
  final bool prominent;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = candidate.fly;
    return InfoCard(
      onTap: fly == null ? null : () => context.push('/flies/${fly.id}'),
      child: Row(children: [
        CatalogThumb(url: fly?.thumbnailUrl, icon: flyIcon, size: prominent ? 72 : 56),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(candidate.patternName, style: prominent ? Theme.of(context).textTheme.titleLarge : Theme.of(context).textTheme.titleMedium),
            if (fly != null || category != null) Text(t.category(fly?.category ?? category!), style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 8),
            Wrap(spacing: 6, runSpacing: 6, children: [
              if (candidate.aiConfidence != null) TagChip(t.aiConfidence(t.confidence(candidate.aiConfidence!))),
              if (candidate.visualSimilarity != null) TagChip(t.visualSimilarity(candidate.visualSimilarity!.toStringAsFixed(2))),
              TagChip(candidate.inCatalog ? t.inCatalog : t.notInCatalog),
            ]),
          ]),
        ),
        if (fly != null) const Icon(Icons.chevron_right, color: AppColors.muted),
      ]),
    );
  }
}
