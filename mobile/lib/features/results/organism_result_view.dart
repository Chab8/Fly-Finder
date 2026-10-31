import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../widgets/common.dart';
import '../../widgets/labels.dart';
import 'result_common.dart';

class OrganismResultView extends StatelessWidget {
  const OrganismResultView({super.key, required this.result, this.photo});
  final OrganismIdentification result;
  final Uint8List? photo;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final primary = result.primary;
    return ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 24), children: [
      ResultHeader(result: result, photo: photo),
      if (primary != null) ...[
        SectionTitle(t.primaryIdentification),
        _CandidateCard(candidate: primary, lifeStage: result.lifeStage, prominent: true),
      ] else if (result.similarOrganisms.isEmpty) ...[
        const SizedBox(height: 24),
        MessageView(icon: Icons.search_off, message: t.noIdentification),
      ],
      if (result.colors.isNotEmpty || result.features.isNotEmpty) ...[
        SectionTitle(t.characteristics),
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (result.colors.isNotEmpty) Wrap(spacing: 6, runSpacing: 6, children: [for (final c in result.colors) TagChip(c)]),
            for (final feature in result.features)
              Padding(padding: const EdgeInsets.only(top: 8), child: Text('• $feature')),
            if (result.estimatedLengthMm != null && result.sizeReference != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(t.estimatedLength(result.estimatedLengthMm!.toStringAsFixed(0), result.sizeReference!)),
              ),
          ]),
        ),
      ],
      if (result.alternatives.isNotEmpty) ...[
        SectionTitle(t.alternatives),
        for (final alt in result.alternatives)
          Padding(padding: const EdgeInsets.only(bottom: 10), child: _CandidateCard(candidate: alt)),
      ],
      if (primary != null) ...[
        SectionTitle(t.recommendedFlies),
        if (result.recommendations.isEmpty)
          InfoCard(child: Text(t.noRecommendations))
        else ...[
          for (final rec in result.recommendations)
            Padding(padding: const EdgeInsets.only(bottom: 10), child: RecommendationCard(rec)),
          Text(t.notAProbability, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
        ],
      ],
      if (result.similarOrganisms.isNotEmpty) ...[
        SectionTitle(t.similarOrganisms),
        for (final (organism, similarity) in result.similarOrganisms)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InfoCard(
              onTap: () => context.push('/organisms/${organism.id}'),
              child: Row(children: [
                CatalogThumb(url: organism.thumbnailUrl, icon: organismIcon),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(organism.scientificName, style: const TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.w600)),
                    Text(t.visualSimilarity(similarity.toStringAsFixed(2)), style: const TextStyle(color: AppColors.muted)),
                  ]),
                ),
              ]),
            ),
          ),
      ],
      SourcesFooter(result),
    ]);
  }
}

class _CandidateCard extends StatelessWidget {
  const _CandidateCard({required this.candidate, this.lifeStage, this.prominent = false});
  final OrganismCandidate candidate;
  final String? lifeStage;
  final bool prominent;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final organism = candidate.catalogOrganism;
    return InfoCard(
      onTap: organism == null ? null : () => context.push('/organisms/${organism.id}'),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(
          candidate.scientificName,
          style: (prominent ? Theme.of(context).textTheme.titleLarge : Theme.of(context).textTheme.titleMedium)?.copyWith(fontStyle: FontStyle.italic),
        ),
        if (candidate.commonName != null) Text(candidate.commonName!, style: const TextStyle(color: AppColors.muted)),
        const SizedBox(height: 10),
        Wrap(spacing: 6, runSpacing: 6, children: [
          TagChip(t.rankName(candidate.taxonomicRank)),
          TagChip(t.aiConfidence(t.confidence(candidate.aiConfidence))),
          if (candidate.taxonomyVerified) TagChip(t.taxonomyVerified, icon: Icons.check, color: AppColors.levelHigh),
          TagChip(candidate.inCatalog ? t.inCatalog : t.notInCatalog, icon: candidate.inCatalog ? Icons.menu_book_outlined : Icons.help_outline),
        ]),
        if (prominent) ...[
          const SizedBox(height: 12),
          LabeledValue(t.order, candidate.order),
          LabeledValue(t.family, candidate.family),
          LabeledValue(t.genus, candidate.genus),
          if (lifeStage != null) LabeledValue(t.lifeStage, t.stage(lifeStage!)),
        ],
        if (candidate.visualEvidence != null) ...[
          const SizedBox(height: 8),
          Text(candidate.visualEvidence!, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
        ],
      ]),
    );
  }
}

class RecommendationCard extends StatelessWidget {
  const RecommendationCard(this.rec, {super.key});
  final FlyRecommendation rec;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return InfoCard(
      onTap: () => context.push('/flies/${rec.fly.id}'),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          CatalogThumb(url: rec.fly.thumbnailUrl, icon: flyIcon),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(rec.fly.name, style: Theme.of(context).textTheme.titleMedium),
              Text(t.category(rec.fly.category), style: const TextStyle(color: AppColors.muted)),
            ]),
          ),
          const Icon(Icons.chevron_right, color: AppColors.muted),
        ]),
        const SizedBox(height: 10),
        Wrap(spacing: 6, runSpacing: 6, children: [
          TagChip(t.tier(rec.tier), color: rec.tier == 'visual_only' ? AppColors.sand : AppColors.olive),
          if (rec.lifeStage != null) TagChip(t.stage(rec.lifeStage!)),
          if (rec.matchType != null) TagChip(t.matchType(rec.matchType!)),
          if (rec.tier != 'visual_only') VerificationTag(verified: rec.expertVerified),
        ]),
        const SizedBox(height: 8),
        for (final reason in rec.reasons)
          Padding(padding: const EdgeInsets.only(top: 3), child: Text('• $reason', style: const TextStyle(fontSize: 13))),
      ]),
    );
  }
}
