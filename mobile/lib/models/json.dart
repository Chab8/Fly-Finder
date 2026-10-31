typedef Json = Map<String, dynamic>;

List<T> listOf<T>(Object? value, T Function(Json) parse) =>
    value is List ? value.whereType<Map>().map((e) => parse(Json.from(e))).toList() : <T>[];

List<String> stringsOf(Object? value) => value is List ? value.map((e) => e.toString()).toList() : const [];

T? objectOf<T>(Object? value, T Function(Json) parse) => value is Map ? parse(Json.from(value)) : null;

double? doubleOf(Object? value) => switch (value) {
      num n => n.toDouble(),
      String s => double.tryParse(s),
      _ => null,
    };
