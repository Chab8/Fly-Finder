import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/identification.dart';
import '../../services/image_source_service.dart';
import '../../state/identification_controller.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

class CaptureScreen extends ConsumerWidget {
  const CaptureScreen({super.key, required this.mode});
  final IdentifyMode mode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context);
    final state = ref.watch(identificationControllerProvider(mode));
    final controller = ref.read(identificationControllerProvider(mode).notifier);
    final photo = state.photo;
    final problem = switch (state.localProblem) {
      LocalImageProblem.tooLarge => t.imageTooLargeLocal(ref.read(appConfigProvider).maxUploadMb),
      LocalImageProblem.unsupported => t.unsupportedFormatLocal,
      LocalImageProblem.permissionDenied => t.permissionDenied,
      null => null,
    };

    return Scaffold(
      appBar: AppBar(
        title: Text(mode == IdentifyMode.organism ? t.identifyOrganismTitle : t.identifyFlyTitle),
        leading: IconButton(
          tooltip: t.cancel,
          icon: const Icon(Icons.close),
          onPressed: () {
            controller.clear();
            context.pop();
          },
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(22),
                child: Container(
                  color: AppColors.sandLight,
                  child: photo == null
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(28),
                            child: Column(mainAxisSize: MainAxisSize.min, children: [
                              Icon(mode == IdentifyMode.organism ? organismIcon : flyIcon, size: 64, color: AppColors.olive),
                              const SizedBox(height: 16),
                              Text(t.noPhotoSelected, style: Theme.of(context).textTheme.titleMedium),
                              const SizedBox(height: 8),
                              Text(
                                mode == IdentifyMode.organism ? t.captureHintOrganism : t.captureHintFly,
                                textAlign: TextAlign.center,
                                style: const TextStyle(color: AppColors.muted),
                              ),
                            ]),
                          ),
                        )
                      : Image.memory(photo.bytes, key: const Key('capture-preview'), fit: BoxFit.contain),
                ),
              ),
            ),
            if (problem != null) ...[
              const SizedBox(height: 12),
              NoticeList([Notice('local', problem)]),
            ],
            const SizedBox(height: 16),
            if (photo != null && problem == null) ...[
              FilledButton.icon(
                key: const Key('capture-analyze'),
                onPressed: () {
                  controller.analyze();
                  context.push('/identify/${mode.name}/analysis');
                },
                icon: const Icon(Icons.search),
                label: Text(t.analyze),
              ),
              const SizedBox(height: 10),
            ],
            Row(children: [
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('capture-camera'),
                  onPressed: () => controller.pick(PhotoSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: Text(photo == null ? t.takePhoto : t.changePhoto),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  key: const Key('capture-gallery'),
                  onPressed: () => controller.pick(PhotoSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: Text(t.chooseFromGallery),
                ),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}
