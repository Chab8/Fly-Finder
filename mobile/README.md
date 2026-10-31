# Fly Finder — app Flutter

App móvil (iOS y Android) del proyecto. Documentación general en el [README raíz](../README.md) y [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

```bash
flutter test
```

- La app no contiene claves: todo pasa por el backend.
- Textos: `lib/l10n/app_es.arb` y `app_en.arb` (se regeneran con `flutter gen-l10n`).
- Los JSON de `test/fixtures/` se generan desde el backend (`backend/tests/test_contract_fixtures.py`); no editarlos a mano.
