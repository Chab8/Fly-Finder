import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import '../../widgets/labels.dart';

const _groups = ['aquatic_insect', 'terrestrial_insect', 'crustacean', 'annelid', 'fish'];
const _categories = ['dry_fly', 'nymph', 'emerger', 'wet_fly', 'streamer', 'terrestrial', 'saltwater', 'attractor'];

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key, this.initialTab = 0});
  final int initialTab;

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    return DefaultTabController(
      length: 2,
      initialIndex: widget.initialTab,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.catalogTitle),
          bottom: TabBar(
            labelColor: fly.accent,
            unselectedLabelColor: fly.inkSecondary,
            indicatorColor: fly.accent,
            dividerColor: fly.hairline,
            labelStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            unselectedLabelStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            tabs: [Tab(text: t.organismsTab), Tab(text: t.fliesTab)],
          ),
        ),
        body: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
            child: TextField(
              key: const Key('catalog-search'),
              decoration: InputDecoration(hintText: t.searchHint, prefixIcon: const Icon(Icons.search)),
              textInputAction: TextInputAction.search,
              onSubmitted: (value) => setState(() => _query = value.trim()),
              onChanged: (value) {
                if (value.isEmpty) setState(() => _query = '');
              },
            ),
          ),
          Expanded(child: TabBarView(children: [_OrganismTab(query: _query), _FlyTab(query: _query)])),
        ]),
      ),
    );
  }
}

class _FilterBar extends StatelessWidget {
  const _FilterBar({required this.values, required this.selected, required this.label, required this.onSelected});
  final List<String> values;
  final String? selected;
  final String Function(String) label;
  final ValueChanged<String?> onSelected;

  Widget _chip(BuildContext context, String text, bool isSelected, VoidCallback onTap) {
    final fly = context.fly;
    return ChoiceChip(
      label: Text(text),
      selected: isSelected,
      labelStyle: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: isSelected ? fly.onRiver : fly.ink),
      selectedColor: fly.river,
      side: BorderSide(color: isSelected ? fly.river : fly.hairline),
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      onSelected: (_) => onTap(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    // The bar grows with the text size so chips are never clipped at large Dynamic Type sizes.
    final height = math.max(56.0, MediaQuery.textScalerOf(context).scale(15) + 40);
    return SizedBox(
      height: height,
      child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), children: [
        _chip(context, t.filterAll, selected == null, () => onSelected(null)),
        for (final value in values)
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: _chip(context, label(value), selected == value, () => onSelected(value)),
          ),
      ]),
    );
  }
}

class _OrganismTab extends ConsumerStatefulWidget {
  const _OrganismTab({required this.query});
  final String query;

  @override
  ConsumerState<_OrganismTab> createState() => _OrganismTabState();
}

class _OrganismTabState extends ConsumerState<_OrganismTab> {
  String? _group;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final key = (query: widget.query, filter: _group);
    final async = ref.watch(organismListProvider(key));
    return Column(children: [
      _FilterBar(values: _groups, selected: _group, label: t.group, onSelected: (v) => setState(() => _group = v)),
      Expanded(
        child: async.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(organismListProvider(key))),
          data: (page) => page.items.isEmpty
              ? MessageView(icon: Icons.inventory_2_outlined, message: widget.query.isEmpty && _group == null ? t.emptyCatalog : t.emptySearch)
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                  itemCount: page.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final o = page.items[index];
                    return InfoCard(
                      padding: const EdgeInsets.all(12),
                      onTap: () => context.push('/organisms/${o.id}'),
                      child: Row(children: [
                        CatalogThumb(url: o.thumbnailUrl, icon: organismGroupIcon(o.organismGroup), size: 60),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(o.scientificName, style: context.species(18)),
                            Text([o.commonName, o.order].whereType<String>().join(' · '), style: context.secondaryStyle),
                            const SizedBox(height: 6),
                            TagChip(t.rankName(o.taxonomicRank)),
                          ]),
                        ),
                        Icon(Icons.chevron_right, color: context.fly.inkSecondary),
                      ]),
                    );
                  },
                ),
        ),
      ),
    ]);
  }
}

class _FlyTab extends ConsumerStatefulWidget {
  const _FlyTab({required this.query});
  final String query;

  @override
  ConsumerState<_FlyTab> createState() => _FlyTabState();
}

class _FlyTabState extends ConsumerState<_FlyTab> {
  String? _category;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final key = (query: widget.query, filter: _category);
    final async = ref.watch(flyListProvider(key));
    return Column(children: [
      _FilterBar(values: _categories, selected: _category, label: t.category, onSelected: (v) => setState(() => _category = v)),
      Expanded(
        child: async.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(flyListProvider(key))),
          data: (page) => page.items.isEmpty
              ? MessageView(icon: Icons.inventory_2_outlined, message: widget.query.isEmpty && _category == null ? t.emptyCatalog : t.emptySearch)
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                  itemCount: page.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final f = page.items[index];
                    return InfoCard(
                      padding: const EdgeInsets.all(12),
                      onTap: () => context.push('/flies/${f.id}'),
                      child: Row(children: [
                        CatalogThumb(url: f.thumbnailUrl, icon: flyIcon, size: 60),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(f.name, style: context.serif(18)),
                            Text(t.category(f.category), style: context.secondaryStyle),
                            if (f.hookSizeMin != null && f.hookSizeMax != null) ...[
                              const SizedBox(height: 6),
                              TagChip(t.hookRange(f.hookSizeMax!, f.hookSizeMin!), tone: TagTone.brass),
                            ],
                          ]),
                        ),
                        Icon(Icons.chevron_right, color: context.fly.inkSecondary),
                      ]),
                    );
                  },
                ),
        ),
      ),
    ]);
  }
}
