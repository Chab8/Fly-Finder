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
    return DefaultTabController(
      length: 2,
      initialIndex: widget.initialTab,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.catalogTitle),
          bottom: TabBar(tabs: [Tab(text: t.organismsTab), Tab(text: t.fliesTab)]),
        ),
        body: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
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

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return SizedBox(
      height: 52,
      child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), children: [
        ChoiceChip(label: Text(t.filterAll), selected: selected == null, onSelected: (_) => onSelected(null)),
        for (final value in values)
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: ChoiceChip(label: Text(label(value)), selected: selected == value, onSelected: (_) => onSelected(value)),
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
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: page.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final o = page.items[index];
                    return InfoCard(
                      padding: const EdgeInsets.all(12),
                      onTap: () => context.push('/organisms/${o.id}'),
                      child: Row(children: [
                        CatalogThumb(url: o.thumbnailUrl, icon: organismGroupIcon(o.organismGroup)),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(o.scientificName, style: const TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.w600, fontSize: 16)),
                            Text([o.commonName, o.order].whereType<String>().join(' · '), style: const TextStyle(color: AppColors.muted)),
                          ]),
                        ),
                        TagChip(t.rankName(o.taxonomicRank)),
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
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: page.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final f = page.items[index];
                    return InfoCard(
                      padding: const EdgeInsets.all(12),
                      onTap: () => context.push('/flies/${f.id}'),
                      child: Row(children: [
                        CatalogThumb(url: f.thumbnailUrl, icon: flyIcon),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(f.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                            Text(t.category(f.category), style: const TextStyle(color: AppColors.muted)),
                          ]),
                        ),
                        if (f.hookSizeMin != null && f.hookSizeMax != null) TagChip(t.hookRange(f.hookSizeMax!, f.hookSizeMin!)),
                      ]),
                    );
                  },
                ),
        ),
      ),
    ]);
  }
}
