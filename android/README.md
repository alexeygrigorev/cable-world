# Android signing

`debug.keystore` - стабильная dev/sideload подпись для APK из GitHub Releases.

Это не production key для Google Play. Ключ специально лежит в репозитории со стандартными debug credentials:

- alias: `androiddebugkey`;
- keystore password: `android`;
- key password: `android`.

Для обновлений поверх установленной APK должны оставаться неизменными Android package id `com.mirtrossov.app` и этот keystore, а `version/code` в `export_presets.cfg` должен монотонно расти.
