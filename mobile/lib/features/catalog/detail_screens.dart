import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/catalog.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import '../../widgets/labels.dart';
import 'product_tile.dart';

/// Photo plate: swipeable, with page dots. Attribution and license are mandatory for every
/// catalog photo, so the credit line always sits under the image.
class _Gallery extends StatefulWidget {
  const _Gallery(this.images, this.icon);
  final List<CatalogImage> images;
  final IconData icon;

  @override
  State<_Gallery> createState() => _GalleryState();
}

class _GalleryState extends State<_Gallery> {
  int _page = 0;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    final images = widget.images;
    if (images.isEmpty) {
      return Container(
        height: 160,
        decoration: BoxDecoration(color: fly.tint, borderRadius: BorderRadius.circular(20), border: Border.all(color: fly.hairline)),
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(widget.icon, size: 44, color: fly.accent),
            const SizedBox(height: 8),
            Text(t.noImages, style: context.secondaryStyle),
          ]),
        ),
      );
    }
    final current = images[_page.clamp(0, images.length - 1)];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Container(
        height: 240,
        decoration: BoxDecoration(color: fly.tint, borderRadius: BorderRadius.circular(20), border: Border.all(color: fly.hairline)),
        clipBehavior: Clip.antiAlias,
        child: Stack(children: [
          PageView(
            onPageChanged: (index) => setState(() => _page = index),
            children: [
              for (final image in images) CachedNetworkImage(imageUrl: image.url, width: double.infinity, height: 240, fit: BoxFit.cover),
            ],
          ),
          if (images.length > 1)
            Positioned(
              left: 0,
              right: 0,
              bottom: 10,
              child: IgnorePointer(
                child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  for (var i = 0; i < images.length; i++)
                    Container(
                      width: 7,
                      height: 7,
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: i == _page ? Colors.white : Colors.white.withValues(alpha: 0.5),
                        boxShadow: const [BoxShadow(color: Color(0x66000000), blurRadius: 3)],
                      ),
                    ),
                ]),
              ),
            ),
        ]),
      ),
      Padding(
        padding: const EdgeInsets.only(top: 6, left: 2),
        child: Text(t.photoCredit(current.attribution, current.license), style: context.captionStyle),
      ),
    ]);
  }
}

class _ReviewNote extends StatelessWidget {
  const _ReviewNote(this.status);
  final String status;

  @override
  Widget build(BuildContext context) => status == 'expert_verified'
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.only(top: 24),
          child: Text(AppLocalizations.of(context).dataReviewNote, style: context.captionStyle),
        );
}

/// Common names in the user's language (falling back to all names).
String _namesFor(OrganismDetail o, String language) {
  final local = o.commonNames.where((n) => n.language == language).map((n) => n.name).toList();
  return (local.isNotEmpty ? local : o.commonNames.map((n) => n.name)).join(' · ');
}

class OrganismDetailScreen extends ConsumerWidget {
  const OrganismDetailScreen({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final async = ref.watch(organismDetailProvider(id));
    return Scaffold(
      appBar: AppBar(),
      body: async.when(
        loading: () => const LoadingView(),
        error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(organismDetailProvider(id))),
        data: (o) => ListView(padding: const EdgeInsets.fromLTRB(20, 0, 20, 36), children: [
          if (o.summary.isDemo) const DemoBanner(),
          Text(o.summary.scientificName, style: context.species(32)),
          if (o.summary.commonName != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(_namesFor(o, Localizations.localeOf(context).languageCode), style: context.secondaryStyle.copyWith(fontSize: 17)),
            ),
          const SizedBox(height: 18),
          _Gallery(o.images, organismGroupIcon(o.summary.organismGroup)),
          if (o.description != null) ...[SectionTitle(t.description), Text(o.description!, style: context.readingStyle)],
          if (o.fishingNotes != null) ...[SectionTitle(t.fishingNotes), Text(o.fishingNotes!, style: context.readingStyle)],
          SectionTitle(t.taxonomy),
          InfoCard(
            child: Column(children: [
              LabeledValue(t.rank, t.rankName(o.summary.taxonomicRank)),
              for (final entry in o.taxonomy.entries) LabeledValue(t.taxonomyField(entry.key), entry.value, italic: true),
              if (o.gbifTaxonId != null) LabeledValue('GBIF', '${o.gbifTaxonId}'),
            ]),
          ),
          if (o.lifeStages.isNotEmpty || o.habitats.isNotEmpty) ...[
            SectionTitle('${t.lifeStages} · ${t.habitat}'),
            Wrap(spacing: 6, runSpacing: 6, children: [
              for (final s in o.lifeStages) TagChip(t.stage(s)),
              for (final h in o.habitats) TagChip(t.habitatName(h), icon: Icons.water_outlined),
            ]),
          ],
          if (o.distribution != null) ...[SectionTitle(t.distribution), Text(o.distribution!, style: context.readingStyle)],
          SectionTitle(t.imitatedBy),
          if (o.imitatedBy.isEmpty)
            InfoCard(child: Text(t.noRecommendations))
          else
            for (final relation in o.imitatedBy)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: InfoCard(
                  padding: const EdgeInsets.all(12),
                  onTap: () => context.push('/flies/${relation.fly!.id}'),
                  child: Row(children: [
                    CatalogThumb(url: relation.fly!.thumbnailUrl, icon: flyIcon),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(relation.fly!.name, style: context.serif(18)),
                        Text('${t.stage(relation.lifeStage)} · ${t.matchType(relation.matchType)}', style: context.secondaryStyle),
                      ]),
                    ),
                    Icon(Icons.chevron_right, color: context.fly.inkSecondary),
                  ]),
                ),
              ),
          _ReviewNote(o.verificationStatus),
        ]),
      ),
    );
  }
}

class FlyDetailScreen extends ConsumerWidget {
  const FlyDetailScreen({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final async = ref.watch(flyDetailProvider(id));
    return Scaffold(
      appBar: AppBar(),
      body: async.when(
        loading: () => const LoadingView(),
        error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(flyDetailProvider(id))),
        data: (f) => ListView(padding: const EdgeInsets.fromLTRB(20, 0, 20, 36), children: [
          if (f.summary.isDemo) const DemoBanner(),
          Text(f.summary.name, style: Theme.of(context).textTheme.headlineMedium),
          if (f.alternateNames.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 4), child: Text(f.alternateNames.join(' · '), style: context.secondaryStyle.copyWith(fontSize: 17))),
          const SizedBox(height: 12),
          Wrap(spacing: 6, runSpacing: 6, children: [
            TagChip(t.category(f.summary.category)),
            TagChip(t.matchType(f.summary.imitationType)),
            if (f.summary.hookSizeMin != null && f.summary.hookSizeMax != null) TagChip(t.hookRange(f.summary.hookSizeMax!, f.summary.hookSizeMin!), tone: TagTone.brass),
          ]),
          const SizedBox(height: 18),
          _Gallery(f.images, flyIcon),
          if (f.description != null) ...[SectionTitle(t.description), Text(f.description!, style: context.readingStyle)],
          if (f.usageNotes != null) ...[SectionTitle(t.fishingNotes), Text(f.usageNotes!, style: context.readingStyle)],
          if (f.materials.isNotEmpty) ...[
            SectionTitle(t.materials),
            InfoCard(child: Column(children: [for (final m in f.materials) LabeledValue(m.component, m.material)])),
          ],
          if (f.variants.isNotEmpty) ...[
            SectionTitle(t.variants),
            Wrap(spacing: 6, runSpacing: 6, children: [for (final v in f.variants) TagChip(v.name)]),
          ],
          SectionTitle(t.imitates),
          if (f.imitates.isEmpty)
            InfoCard(child: Text(t.imitatesNothingDocumented))
          else
            for (final relation in f.imitates)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: InfoCard(
                  padding: const EdgeInsets.all(14),
                  onTap: () => context.push('/organisms/${relation.organism!.id}'),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Expanded(child: Text(relation.organism!.scientificName, style: context.species(19))),
                      Icon(Icons.chevron_right, color: context.fly.inkSecondary),
                    ]),
                    const SizedBox(height: 8),
                    Wrap(spacing: 6, runSpacing: 6, children: [
                      TagChip(t.stage(relation.lifeStage)),
                      TagChip(t.compatibility(relation.biologicalCompatibility)),
                      VerificationTag(verified: relation.expertVerified),
                    ]),
                  ]),
                ),
              ),
          SectionTitle(t.products),
          FilledButton.icon(
            key: const Key('fly-products'),
            onPressed: () => context.push('/flies/$id/products'),
            icon: const Icon(Icons.storefront_outlined),
            label: Text('${t.viewProducts} (${f.productCount})'),
          ),
          _ReviewNote(f.verificationStatus),
        ]),
      ),
    );
  }
}

class ProductsScreen extends ConsumerWidget {
  const ProductsScreen({super.key, required this.flyId});
  final String flyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final async = ref.watch(flyProductsProvider(flyId));
    return Scaffold(
      appBar: AppBar(title: Text(t.productsTitle)),
      body: async.when(
        loading: () => const LoadingView(),
        error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(flyProductsProvider(flyId))),
        data: (products) => products.isEmpty
            ? MessageView(icon: Icons.storefront_outlined, message: t.noProducts)
            : ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
                itemCount: products.length,
                separatorBuilder: (_, _) => const SizedBox(height: 8),
                itemBuilder: (_, index) => ProductTile(products[index]),
              ),
      ),
    );
  }
}
