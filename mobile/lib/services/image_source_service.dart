import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

enum PhotoSource { camera, gallery }

class PickedPhoto {
  const PickedPhoto({required this.bytes, required this.filename});
  final Uint8List bytes;
  final String filename;
}

class PhotoPermissionDenied implements Exception {}

/// Wraps image_picker so screens can be tested with a fake.
abstract class ImageSourceService {
  Future<PickedPhoto?> pick(PhotoSource source);
}

class PickerImageSourceService implements ImageSourceService {
  PickerImageSourceService([ImagePicker? picker]) : _picker = picker ?? ImagePicker();

  final ImagePicker _picker;

  @override
  Future<PickedPhoto?> pick(PhotoSource source) async {
    try {
      // Resizing on device keeps uploads small. When a size or quality is requested,
      // image_picker re-encodes the photo, which also converts iPhone HEIC to JPEG.
      final file = await _picker.pickImage(
        source: source == PhotoSource.camera ? ImageSource.camera : ImageSource.gallery,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 88,
        requestFullMetadata: false,
      );
      if (file == null) return null;
      return PickedPhoto(bytes: await file.readAsBytes(), filename: file.name);
    } on PlatformException catch (error) {
      if (error.code.contains('access_denied') || error.code.contains('permission')) throw PhotoPermissionDenied();
      rethrow;
    }
  }
}
