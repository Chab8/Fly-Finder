import 'package:dio/dio.dart';

enum FailureKind { network, timeout, rateLimited, invalidImage, tooLarge, unavailable, notFound, server, unknown }

/// A failed API call, mapped from Dio errors and the backend's `{"error": {...}}` body.
class ApiFailure implements Exception {
  const ApiFailure(this.kind, {this.code, this.message});

  final FailureKind kind;
  final String? code;
  final String? message;

  factory ApiFailure.fromDio(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const ApiFailure(FailureKind.timeout);
      case DioExceptionType.connectionError:
        return const ApiFailure(FailureKind.network);
      default:
        break;
    }
    final response = error.response;
    if (response == null) return const ApiFailure(FailureKind.network);
    final data = response.data;
    final body = data is Map && data['error'] is Map ? data['error'] as Map : const {};
    final code = body['code'] as String?;
    final message = body['message'] as String?;
    final kind = switch (response.statusCode) {
      404 => FailureKind.notFound,
      413 => FailureKind.tooLarge,
      422 => FailureKind.invalidImage,
      429 => FailureKind.rateLimited,
      502 || 503 || 504 => FailureKind.unavailable,
      _ => FailureKind.server,
    };
    return ApiFailure(kind, code: code, message: message);
  }

  @override
  String toString() => 'ApiFailure($kind, $code)';
}
