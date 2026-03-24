/// Round a value UP to the nearest multiple of 5.
///
/// This matches the ABEM business rule: expense shares are always
/// rounded up to the nearest 5 EGP (e.g. 22.01 → 25.00).
double roundUpToNearest5(double value) {
  if (value <= 0) return 0;
  return (value / 5).ceil() * 5.0;
}
