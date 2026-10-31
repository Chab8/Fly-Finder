import 'package:dio/dio.dart';

import '../core/network/api_failure.dart';
import '../models/catalog.dart';
import '../models/commerce.dart';
import '../models/identification.dart';
import '../models/json.dart';

/// Progress callback for uploads: fraction in [0, 1].
typedef UploadProgress = void Function(double fraction);

/// Backend contract used by the app. Screens and state depend on this, never on Dio.
abstract class FlyFinderApi {
  Future<IdentificationResult> identify(IdentifyMode mode, List<int> imageBytes, String filename, {UploadProgress? onProgress, String? country});
  Future<CatalogPage<OrganismSummary>> organisms({String? query, String? group, int limit = 100});
  Future<CatalogPage<FlyPatternSummary>> flies({String? query, String? category, int limit = 100});
  Future<OrganismDetail> organism(String id);
  Future<FlyPatternDetail> fly(String id);
  Future<List<ProductInfo>> flyProducts(String flyId, {String? country});
  Future<List<IdentificationSummary>> history();
  Future<IdentificationResult> storedIdentification(String id);
}

class DioFlyFinderApi implements FlyFinderApi {
  DioFlyFinderApi({required String baseUrl, required String clientId, required this.language, Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: '${baseUrl.replaceAll(RegExp(r'/+$'), '')}/api/v1',
              connectTimeout: const Duration(seconds: 10),
              sendTimeout: const Duration(seconds: 60),
              // Gemini analysis has its own 45 s server-side timeout.
              receiveTimeout: const Duration(seconds: 90),
              headers: {'X-Client-Id': clientId},
            ));

  final Dio _dio;
  /// Returns the current UI language code (en/es) for localized backend texts.
  final String Function() language;

  Future<T> _call<T>(Future<Response<dynamic>> Function() request, T Function(dynamic data) parse) async {
    try {
      final response = await request();
      return parse(response.data);
    } on DioException catch (error) {
      throw ApiFailure.fromDio(error);
    }
  }

  Map<String, dynamic> _params([Map<String, dynamic>? extra]) =>
      {'lang': language(), ...?extra}..removeWhere((key, value) => value == null || value == '');

  @override
  Future<IdentificationResult> identify(IdentifyMode mode, List<int> imageBytes, String filename, {UploadProgress? onProgress, String? country}) {
    final form = FormData.fromMap({'image': MultipartFile.fromBytes(imageBytes, filename: filename)});
    return _call(
      () => _dio.post(
        '/identify/${mode.name}',
        data: form,
        queryParameters: _params({'country': mode == IdentifyMode.fly ? country : null}),
        onSendProgress: onProgress == null ? null : (sent, total) => onProgress(total > 0 ? sent / total : 0),
      ),
      (data) => mode == IdentifyMode.fly ? FlyIdentification.fromJson(Json.from(data as Map)) : OrganismIdentification.fromJson(Json.from(data as Map)),
    );
  }

  @override
  Future<CatalogPage<OrganismSummary>> organisms({String? query, String? group, int limit = 100}) => _call(
        () => _dio.get('/organisms', queryParameters: _params({'q': query, 'group': group, 'limit': limit})),
        (data) => CatalogPage.fromJson(Json.from(data as Map), OrganismSummary.fromJson),
      );

  @override
  Future<CatalogPage<FlyPatternSummary>> flies({String? query, String? category, int limit = 100}) => _call(
        () => _dio.get('/flies', queryParameters: _params({'q': query, 'category': category, 'limit': limit})),
        (data) => CatalogPage.fromJson(Json.from(data as Map), FlyPatternSummary.fromJson),
      );

  @override
  Future<OrganismDetail> organism(String id) =>
      _call(() => _dio.get('/organisms/$id', queryParameters: _params()), (data) => OrganismDetail.fromJson(Json.from(data as Map)));

  @override
  Future<FlyPatternDetail> fly(String id) =>
      _call(() => _dio.get('/flies/$id', queryParameters: _params()), (data) => FlyPatternDetail.fromJson(Json.from(data as Map)));

  @override
  Future<List<ProductInfo>> flyProducts(String flyId, {String? country}) => _call(
        () => _dio.get('/flies/$flyId/products', queryParameters: _params({'country': country})),
        (data) => listOf(data, ProductInfo.fromJson),
      );

  @override
  Future<List<IdentificationSummary>> history() =>
      _call(() => _dio.get('/identifications', queryParameters: _params()), (data) => listOf(data, IdentificationSummary.fromJson));

  @override
  Future<IdentificationResult> storedIdentification(String id) =>
      _call(() => _dio.get('/identifications/$id', queryParameters: _params()), (data) => parseIdentification(Json.from(data as Map)));
}
