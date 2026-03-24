import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import 'ad_config.dart';

/// Singleton manager for interstitial ads.
///
/// Trigger rules:
/// - After every 5th successful payment recording
/// - After a successful report export
///
/// Never trigger on: login, registration, error states, wizard steps,
/// or while a form is open.
class InterstitialAdManager {
  int _paymentCount = 0;
  InterstitialAd? _ad;

  Future<void> init() async => _loadAd();

  /// Call after each successful payment recording.
  void onPaymentRecorded() {
    _paymentCount++;
    if (_paymentCount % 5 == 0) {
      _showIfReady();
    }
    _loadAd(); // Preload next
  }

  /// Call after a successful report export.
  void onReportExported() => _showIfReady();

  void _showIfReady() {
    if (_ad != null) {
      _ad!.show();
      _ad = null;
    }
  }

  Future<void> _loadAd() async {
    if (_ad != null) return; // Already loaded
    await InterstitialAd.load(
      adUnitId: AdConfig.interstitialId,
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (ad) {
          _ad = ad;
          ad.fullScreenContentCallback = FullScreenContentCallback(
            onAdDismissedFullScreenContent: (ad) {
              ad.dispose();
              _ad = null;
              _loadAd(); // Preload next
            },
            onAdFailedToShowFullScreenContent: (ad, error) {
              if (kDebugMode) debugPrint('Interstitial failed to show: $error');
              ad.dispose();
              _ad = null;
            },
          );
        },
        onAdFailedToLoad: (error) {
          if (kDebugMode) debugPrint('Interstitial failed to load: $error');
          _ad = null;
        },
      ),
    );
  }

  void dispose() {
    _ad?.dispose();
    _ad = null;
  }
}
