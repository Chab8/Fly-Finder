import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../state/identification_controller.dart';
import '../../widgets/common.dart';

/// Shows only the phases that really happen: upload progress, then waiting for the server.
class AnalysisScreen extends ConsumerWidget {
  const AnalysisScreen({super.key, required this.mode});
  final IdentifyMode mode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final provider = identificationControllerProvider(mode);
    ref.listen(provider, (previous, next) {
      if (next.phase == AnalysisPhase.done && previous?.phase != AnalysisPhase.done) {
        context.pushReplacement('/identify/${mode.name}/result');
      }
    });
    final state = ref.watch(provider);

    if (state.phase == AnalysisPhase.failed) {
      return Scaffold(
        appBar: AppBar(),
        body: ErrorView(error: state.failure!, onRetry: () => ref.read(provider.notifier).analyze()),
        bottomNavigationBar: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: OutlinedButton(onPressed: () => context.pop(), child: Text(t.changePhoto)),
          ),
        ),
      );
    }

    final uploading = state.phase == AnalysisPhase.uploading;
    return PopScope(
      canPop: !state.busy,
      child: Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              if (state.photo != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: Image.memory(state.photo!.bytes, height: 200, fit: BoxFit.cover),
                ),
              const SizedBox(height: 36),
              _PhaseRow(
                key: const Key('phase-upload'),
                label: t.phaseUploading,
                active: uploading,
                done: !uploading,
                progress: uploading ? state.uploadProgress : null,
              ),
              const SizedBox(height: 14),
              _PhaseRow(key: const Key('phase-analyze'), label: t.phaseAnalyzing, active: !uploading, done: false),
              const SizedBox(height: 28),
              Text(t.analysisNote, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.muted)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _PhaseRow extends StatelessWidget {
  const _PhaseRow({super.key, required this.label, required this.active, required this.done, this.progress});
  final String label;
  final bool active;
  final bool done;
  final double? progress;

  @override
  Widget build(BuildContext context) {
    final color = active || done ? AppColors.forest : AppColors.muted;
    return Column(children: [
      Row(children: [
        SizedBox(
          width: 28,
          height: 28,
          child: done
              ? const Icon(Icons.check_circle, color: AppColors.forest)
              : active
                  ? const CircularProgressIndicator(strokeWidth: 3)
                  : const Icon(Icons.radio_button_unchecked, color: AppColors.muted),
        ),
        const SizedBox(width: 14),
        Expanded(child: Text(label, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: color))),
      ]),
      if (progress != null)
        Padding(
          padding: const EdgeInsets.only(left: 42, top: 8),
          child: LinearProgressIndicator(value: progress, minHeight: 6, borderRadius: BorderRadius.circular(3)),
        ),
    ]);
  }
}
