import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../state/identification_controller.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import 'fly_result_view.dart';
import 'organism_result_view.dart';
import 'result_common.dart';

Widget _view(IdentificationResult result, {Uint8List? photo}) => switch (result) {
      OrganismIdentification r => OrganismResultView(result: r, photo: photo),
      FlyIdentification r => FlyResultView(result: r, photo: photo),
      _ => const SizedBox.shrink(),
    };

/// Result of the identification that just ran on this device.
class LiveResultScreen extends ConsumerWidget {
  const LiveResultScreen({super.key, required this.mode});
  final IdentifyMode mode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final state = ref.watch(identificationControllerProvider(mode));
    final result = state.result;
    return Scaffold(
      appBar: AppBar(title: Text(mode == IdentifyMode.organism ? t.resultOrganismTitle : t.resultFlyTitle)),
      body: Column(children: [
        if (result?.analysis.isDemo ?? false) const DemoBanner(),
        Expanded(child: result == null ? MessageView(icon: Icons.search_off, message: t.noIdentification) : _view(result, photo: state.photo?.bytes)),
      ]),
      bottomNavigationBar: ResultActions(
        onHome: () {
          ref.read(identificationControllerProvider(mode).notifier).clear();
          context.go('/');
        },
        onNewPhoto: () {
          ref.read(identificationControllerProvider(mode).notifier).clear();
          context.go('/');
          context.push('/identify/${mode.name}');
        },
      ),
    );
  }
}

/// A past identification loaded from the backend history (the photo itself is not stored).
class StoredResultScreen extends ConsumerWidget {
  const StoredResultScreen({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final async = ref.watch(storedIdentificationProvider(id));
    return Scaffold(
      appBar: AppBar(title: Text(t.historyTitle)),
      body: async.when(
        loading: () => const LoadingView(),
        error: (error, _) => ErrorView(error: error, onRetry: () => ref.invalidate(storedIdentificationProvider(id))),
        data: (result) => Column(children: [
          if (result.analysis.isDemo) const DemoBanner(),
          Expanded(child: _view(result)),
        ]),
      ),
    );
  }
}
