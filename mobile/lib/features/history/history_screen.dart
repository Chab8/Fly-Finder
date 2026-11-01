import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    final locale = Localizations.localeOf(context).toLanguageTag();
    final async = ref.watch(historyProvider);
    return Scaffold(
      appBar: AppBar(title: Text(t.historyTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(historyProvider.future),
        child: async.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(historyProvider)),
          data: (items) => items.isEmpty
              ? ListView(children: [MessageView(icon: Icons.history, message: t.historyEmpty)])
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return InfoCard(
                      padding: const EdgeInsets.all(14),
                      onTap: () => context.push('/history/${item.id}'),
                      child: Row(children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(color: fly.riverTint, shape: BoxShape.circle),
                          child: Icon(item.mode == IdentifyMode.fly ? flyIcon : organismIcon, color: fly.accent, size: 22),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(
                              item.primaryLabel ?? (item.mode == IdentifyMode.fly ? t.kind_fly : t.kind_organism),
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            Text(DateFormat.yMMMd(locale).add_Hm().format(item.createdAt.toLocal()), style: context.captionStyle),
                            const SizedBox(height: 8),
                            // On its own line so a long certainty label never squeezes the title.
                            MatchLevelBadge(item.matchLevel),
                          ]),
                        ),
                        Icon(Icons.chevron_right, color: fly.inkSecondary),
                      ]),
                    );
                  },
                ),
        ),
      ),
    );
  }
}
