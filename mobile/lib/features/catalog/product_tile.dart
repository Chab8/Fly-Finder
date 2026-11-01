import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/commerce.dart';
import '../../widgets/common.dart';
import '../../widgets/labels.dart';

/// Formats a price in its own currency. Prices are never converted between currencies.
String formatPrice(String amount, String currency, String locale) {
  final value = double.tryParse(amount);
  if (value == null) return '$amount $currency';
  return NumberFormat.currency(locale: locale, name: currency, symbol: '$currency ').format(value);
}

class ProductTile extends StatelessWidget {
  const ProductTile(this.product, {super.key});
  final ProductInfo product;

  Future<void> _open(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    final message = AppLocalizations.of(context).cannotOpenLink;
    final uri = Uri.tryParse(product.buyUrl);
    final opened = uri != null && (uri.scheme == 'https' || uri.scheme == 'http') && await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened) messenger.showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final fly = context.fly;
    final locale = Localizations.localeOf(context).toLanguageTag();
    final price = product.price != null && product.currency != null ? formatPrice(product.price!, product.currency!, locale) : t.priceNotAvailable;
    return InfoCard(
      onTap: () => _open(context),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: Text(product.name, style: Theme.of(context).textTheme.titleMedium)),
          const SizedBox(width: 8),
          Padding(padding: const EdgeInsets.only(top: 2), child: Icon(Icons.open_in_new, size: 20, color: fly.accent)),
        ]),
        const SizedBox(height: 4),
        Text('${product.store.name} · ${product.store.country}${product.brand == null ? '' : ' · ${product.brand}'}', style: context.secondaryStyle),
        const SizedBox(height: 12),
        Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
          // Brass means tackle and shops: prices share the colour of hook sizes.
          Text(price, key: const Key('product-price'), style: context.bodyStyle.copyWith(color: fly.brass, fontWeight: FontWeight.w700, fontSize: 18)),
          TagChip(t.availability(product.availabilityStatus)),
          if (product.shipsToRequestedCountry == true) TagChip(t.shipsToYou, icon: Icons.local_shipping_outlined),
        ]),
        if (product.lastVerifiedAt != null) ...[
          const SizedBox(height: 8),
          Text(t.lastVerified(DateFormat.yMMMd(locale).format(product.lastVerifiedAt!.toLocal())), style: context.captionStyle),
        ],
      ]),
    );
  }
}
