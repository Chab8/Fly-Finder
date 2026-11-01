import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../state/identification_controller.dart';
import '../../widgets/common.dart';
import '../../widgets/rise_rings.dart';

/// Shows only the phases that really happen: upload progress, then waiting for the server.
class AnalysisScreen extends ConsumerWidget {
  const AnalysisScreen({super.key, required this.mode});
  final IdentifyMode mode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
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
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                // The photo sits in the middle of the rise rings: the app is "waiting for the fish".
                RiseRingsAnimation(
                  color: fly.ripple,
                  size: 300,
                  child: state.photo == null
                      ? const SizedBox.shrink()
                      : Container(
                          width: 152,
                          height: 152,
                          decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: fly.card, width: 4)),
                          clipBehavior: Clip.antiAlias,
                          child: Image.memory(state.photo!.bytes, width: 152, height: 152, fit: BoxFit.cover),
                        ),
                ),
                const SizedBox(height: 20),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(children: [
                      _PhaseRow(
                        key: const Key('phase-upload'),
                        label: t.phaseUploading,
                        active: uploading,
                        done: !uploading,
                        progress: uploading ? state.uploadProgress : null,
                      ),
                      const SizedBox(height: 16),
                      _PhaseRow(key: const Key('phase-analyze'), label: t.phaseAnalyzing, active: !uploading, done: false),
                    ]),
                  ),
                ),
                const SizedBox(height: 20),
                Text(t.analysisNote, textAlign: TextAlign.center, style: context.secondaryStyle),
              ]),
            ),
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
    final fly = context.fly;
    final color = active || done ? fly.ink : fly.inkSecondary;
    return Column(children: [
      Row(children: [
        SizedBox(
          width: 28,
          height: 28,
          child: done
              ? Icon(Icons.check_circle, color: fly.accent)
              : active
                  ? const CircularProgressIndicator(strokeWidth: 3)
                  : Icon(Icons.radio_button_unchecked, color: fly.inkSecondary),
        ),
        const SizedBox(width: 14),
        Expanded(child: Text(label, style: Theme.of(context).textTheme.titleMedium?.copyWith(color: color))),
      ]),
      if (progress != null)
        Padding(
          padding: const EdgeInsets.only(left: 42, top: 10),
          child: LinearProgressIndicator(value: progress, minHeight: 6, borderRadius: BorderRadius.circular(3)),
        ),
    ]);
  }
}
