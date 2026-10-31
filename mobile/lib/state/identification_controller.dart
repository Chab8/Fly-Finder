import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/api_failure.dart';
import '../models/identification.dart';
import '../services/image_source_service.dart';
import 'providers.dart';

/// Phases the user sees. Each one corresponds to something really happening:
/// uploading = bytes leaving the phone (real progress), analyzing = waiting for the server.
enum AnalysisPhase { idle, uploading, analyzing, done, failed }

enum LocalImageProblem { tooLarge, unsupported, permissionDenied }

class IdentificationState {
  const IdentificationState({
    this.photo,
    this.phase = AnalysisPhase.idle,
    this.uploadProgress = 0,
    this.result,
    this.failure,
    this.localProblem,
  });

  final PickedPhoto? photo;
  final AnalysisPhase phase;
  final double uploadProgress;
  final IdentificationResult? result;
  final ApiFailure? failure;
  final LocalImageProblem? localProblem;

  bool get busy => phase == AnalysisPhase.uploading || phase == AnalysisPhase.analyzing;
}

const _allowedExtensions = {'jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'};

class IdentificationController extends Notifier<IdentificationState> {
  IdentificationController(this.mode);

  final IdentifyMode mode;

  @override
  IdentificationState build() => const IdentificationState();

  Future<void> pick(PhotoSource source) async {
    try {
      final photo = await ref.read(imageSourceProvider).pick(source);
      if (photo == null) return; // user cancelled
      state = IdentificationState(photo: photo, localProblem: _check(photo));
    } on PhotoPermissionDenied {
      state = IdentificationState(photo: state.photo, localProblem: LocalImageProblem.permissionDenied);
    }
  }

  LocalImageProblem? _check(PickedPhoto photo) {
    final maxBytes = ref.read(appConfigProvider).maxUploadMb * 1024 * 1024;
    if (photo.bytes.length > maxBytes) return LocalImageProblem.tooLarge;
    final extension = photo.filename.contains('.') ? photo.filename.split('.').last.toLowerCase() : '';
    // Content is validated for real on the server; this only catches obvious mistakes early.
    if (extension.isNotEmpty && !_allowedExtensions.contains(extension)) return LocalImageProblem.unsupported;
    return null;
  }

  void clear() => state = const IdentificationState();

  Future<void> analyze() async {
    final photo = state.photo;
    if (photo == null || state.localProblem != null || state.busy) return;
    state = IdentificationState(photo: photo, phase: AnalysisPhase.uploading);
    try {
      final result = await ref.read(apiProvider).identify(
        mode,
        photo.bytes,
        photo.filename,
        country: deviceCountry(),
        onProgress: (fraction) {
          final phase = fraction >= 1 ? AnalysisPhase.analyzing : AnalysisPhase.uploading;
          if (state.phase != AnalysisPhase.done) {
            state = IdentificationState(photo: photo, phase: phase, uploadProgress: fraction);
          }
        },
      );
      state = IdentificationState(photo: photo, phase: AnalysisPhase.done, result: result);
    } on ApiFailure catch (failure) {
      state = IdentificationState(photo: photo, phase: AnalysisPhase.failed, failure: failure);
    }
  }
}

final identificationControllerProvider =
    NotifierProvider.family<IdentificationController, IdentificationState, IdentifyMode>(IdentificationController.new);
