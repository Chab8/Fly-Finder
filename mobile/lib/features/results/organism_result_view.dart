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
    return ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 28), children: [
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
            for (final feature in result.features) BulletText(feature),
            if (result.estimatedLengthMm != null && result.sizeReference != null)
              Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Text(t.estimatedLength(result.estimatedLengthMm!.toStringAsFixed(0), result.sizeReference!), style: context.secondaryStyle),
              ),
          ]),
        ),
      ],
      if (result.alternatives.isNotEmpty) ...[
        SectionTitle(t.alternatives),
        for (final alt in result.alternatives) Padding(padding: const EdgeInsets.only(bottom: 10), child: _CandidateCard(candidate: alt)),
      ],
      if (primary != null) ...[
        SectionTitle(t.recommendedFlies),
        if (result.recommendations.isEmpty)
          InfoCard(child: Text(t.noRecommendations))
        else ...[
          for (final rec in result.recommendations) Padding(padding: const EdgeInsets.only(bottom: 10), child: RecommendationCard(rec)),
          Text(t.notAProbability, style: context.captionStyle),
        ],
      ],
      if (result.similarOrganisms.isNotEmpty) ...[
        SectionTitle(t.similarOrganisms),
        for (final (organism, similarity) in result.similarOrganisms)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InfoCard(
              padding: const EdgeInsets.all(12),
              onTap: () => context.push('/organisms/${organism.id}'),
              child: Row(children: [
                CatalogThumb(url: organism.thumbnailUrl, icon: organismIcon),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(organism.scientificName, style: context.species(17)),
                    Text(t.visualSimilarity(similarity.toStringAsFixed(2)), style: context.secondaryStyle),
                  ]),
                ),
                Icon(Icons.chevron_right, color: context.fly.inkSecondary),
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
      highlight: prominent,
      onTap: organism == null ? null : () => context.push('/organisms/${organism.id}'),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: Text(candidate.scientificName, style: context.species(prominent ? 26 : 19))),
          if (organism != null) Padding(padding: const EdgeInsets.only(left: 8, top: 4), child: Icon(Icons.chevron_right, color: context.fly.inkSecondary)),
        ]),
        if (candidate.commonName != null) Padding(padding: const EdgeInsets.only(top: 2), child: Text(candidate.commonName!, style: context.secondaryStyle.copyWith(fontSize: 16))),
        const SizedBox(height: 12),
        Wrap(spacing: 6, runSpacing: 6, children: [
          TagChip(t.rankName(candidate.taxonomicRank)),
          TagChip(t.aiConfidence(t.confidence(candidate.aiConfidence))),
          if (candidate.taxonomyVerified) TagChip(t.taxonomyVerified, icon: Icons.check, tone: TagTone.good),
          TagChip(candidate.inCatalog ? t.inCatalog : t.notInCatalog, icon: candidate.inCatalog ? Icons.menu_book_outlined : Icons.help_outline),
        ]),
        if (prominent) ...[
          const SizedBox(height: 14),
          LabeledValue(t.order, candidate.order),
          LabeledValue(t.family, candidate.family),
          LabeledValue(t.genus, candidate.genus),
          if (lifeStage != null) LabeledValue(t.lifeStage, t.stage(lifeStage!)),
        ],
        if (candidate.visualEvidence != null) ...[
          const SizedBox(height: 10),
          Text(candidate.visualEvidence!, style: context.secondaryStyle),
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
              Text(rec.fly.name, style: context.serif(18)),
              Text(t.category(rec.fly.category), style: context.secondaryStyle),
            ]),
          ),
          Icon(Icons.chevron_right, color: context.fly.inkSecondary),
        ]),
        const SizedBox(height: 12),
        Wrap(spacing: 6, runSpacing: 6, children: [
          // Documented matches get the "good" tone; a purely visual suggestion stays neutral.
          TagChip(t.tier(rec.tier), tone: rec.tier == 'visual_only' ? TagTone.neutral : TagTone.good),
          if (rec.lifeStage != null) TagChip(t.stage(rec.lifeStage!)),
          if (rec.matchType != null) TagChip(t.matchType(rec.matchType!)),
          if (rec.tier != 'visual_only') VerificationTag(verified: rec.expertVerified),
        ]),
        for (final reason in rec.reasons) BulletText(reason, style: context.secondaryStyle),
      ]),
    );
  }
}
