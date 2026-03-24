/// AdMob unit IDs — injected via --dart-define in production builds.
///
/// Default values are Google's official test IDs (safe for development).
class AdConfig {
  AdConfig._();

  static String get bannerId => const String.fromEnvironment(
        'ADMOB_BANNER_ID',
        defaultValue: 'ca-app-pub-3940256099942544/6300978111',
      );

  static String get interstitialId => const String.fromEnvironment(
        'ADMOB_INTERSTITIAL_ID',
        defaultValue: 'ca-app-pub-3940256099942544/1033173712',
      );
}
