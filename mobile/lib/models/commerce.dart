import 'json.dart';

class StoreInfo {
  const StoreInfo({required this.name, required this.country, required this.currency, required this.website, this.shippingCountries = const []});

  final String name;
  final String country;
  final String currency;
  final String website;
  final List<String> shippingCountries;

  factory StoreInfo.fromJson(Json j) => StoreInfo(
        name: j['name'] as String,
        country: j['country'] as String,
        currency: j['currency'] as String,
        website: j['website'] as String,
        shippingCountries: stringsOf(j['shipping_countries']),
      );
}

class ProductInfo {
  const ProductInfo({
    required this.id,
    required this.name,
    required this.store,
    required this.buyUrl,
    required this.availabilityStatus,
    this.brand,
    this.price,
    this.currency,
    this.lastVerifiedAt,
    this.shipsToRequestedCountry,
    this.isDemo = false,
  });

  final String id;
  final String name;
  final String? brand;
  final StoreInfo store;
  final String buyUrl;
  /// Kept as the exact decimal string from the backend. Never converted between currencies.
  final String? price;
  final String? currency;
  final String availabilityStatus;
  final DateTime? lastVerifiedAt;
  final bool? shipsToRequestedCountry;
  final bool isDemo;

  factory ProductInfo.fromJson(Json j) => ProductInfo(
        id: j['id'] as String,
        name: j['name'] as String,
        brand: j['brand'] as String?,
        store: StoreInfo.fromJson(Json.from(j['store'] as Map)),
        buyUrl: j['buy_url'] as String,
        price: j['price']?.toString(),
        currency: j['currency'] as String?,
        availabilityStatus: j['availability_status'] as String? ?? 'unknown',
        lastVerifiedAt: j['last_verified_at'] == null ? null : DateTime.tryParse(j['last_verified_at'] as String),
        shipsToRequestedCountry: j['ships_to_requested_country'] as bool?,
        isDemo: j['is_demo'] as bool? ?? false,
      );
}
