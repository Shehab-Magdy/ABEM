// ABEM Interactive Walkthrough System — Flutter
//
// Integration checklist:
//   1. Wrap your root Scaffold body (or MaterialApp builder) with
//      WalkthroughOverlay:
//
//        WalkthroughOverlay(
//          controller: WalkthroughController.instance,
//          child: child,            // your normal page content
//        )
//
//   2. Add TutorialIconButton to your AppBar actions (before the
//      notification bell):
//        actions: [
//          TutorialIconButton(controller: WalkthroughController.instance),
//          NotificationBellButton(),
//        ]
//
//   3. Attach the GlobalKeys declared at the bottom of this file to the
//      widgets listed in TUTORIAL_ANCHORS.md.
//
//   4. The app uses GoRouter.  Pass the GoRouter instance to the controller
//      once (see WalkthroughController.init).  Navigation happens via
//      GoRouter.of(context).go(route) from inside next()/prev().

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Brand colours
// ─────────────────────────────────────────────────────────────────────────────

const _kPrimaryBlue = Color(0xFF2563EB);
const _kGreen = Color(0xFF10B981);
const _kCardBorder = Color(0xFFE5E7EB);
const _kBadgeBg = Color(0xFFEFF6FF);
const _kBadgeText = Color(0xFF1E40AF);
const _kBodyText = Color(0xFF6B7280);
const _kHeadText = Color(0xFF1F2937);

// ─────────────────────────────────────────────────────────────────────────────
// Step model
// ─────────────────────────────────────────────────────────────────────────────

enum TutorialRole { admin, owner }

enum TutorialPlacement { below, above, right, left, center }

class WalkthroughStep {
  const WalkthroughStep({
    required this.route,
    required this.title,
    required this.description,
    this.anchorKey,
    this.placement = TutorialPlacement.below,
  });

  /// Named GoRouter route, e.g. '/home', '/buildings'.
  final String route;
  final String title;
  final String description;

  /// A GlobalKey attached to the widget to highlight. Null = center screen.
  final GlobalKey? anchorKey;

  final TutorialPlacement placement;
}

// ─────────────────────────────────────────────────────────────────────────────
// Step data
// ─────────────────────────────────────────────────────────────────────────────

final _adminSteps = <WalkthroughStep>[
  WalkthroughStep(
    route: '/home',
    title: 'Welcome to ABEM',
    description:
        'The dashboard shows total income, total expenses, overdue units, and the number of buildings managed — refreshed in real time.',
  ),
  WalkthroughStep(
    route: '/buildings',
    anchorKey: kAddBuildingKey,
    title: 'Create your first building',
    description:
        'Every workflow starts here. Tap the + button to enter the address, number of floors, apartments, and stores.',
  ),
  WalkthroughStep(
    route: '/buildings',
    anchorKey: kBuildingActionsKey,
    title: 'What you can do with a building',
    description:
        'Edit details, manage units, assign owners, activate/deactivate, or soft-delete. Deleted records remain visible in the audit log.',
    placement: TutorialPlacement.above,
  ),
  WalkthroughStep(
    route: '/expenses',
    anchorKey: kAddExpenseKey,
    title: 'Add a shared expense',
    description:
        'Select a category, enter the amount, and choose how to split it across units. Every share is rounded up to the nearest 5 EGP.',
  ),
  WalkthroughStep(
    route: '/expenses',
    anchorKey: kExpenseActionsKey,
    title: 'Expense actions explained',
    description:
        'Edit, view the per-unit breakdown, upload the original bill, or delete. Deleting reverses outstanding balances with a full audit entry.',
    placement: TutorialPlacement.left,
  ),
  WalkthroughStep(
    route: '/users',
    anchorKey: kAddUserKey,
    title: 'Manage users',
    description:
        'Create Admin or Owner accounts. Deactivate blocks login immediately without deleting history — critical for compliance.',
  ),
  WalkthroughStep(
    route: '/categories',
    anchorKey: kCategoriesListKey,
    title: 'Expense categories',
    description:
        'ABEM ships with 15 built-in categories. Each has an icon, hex color, and optional subcategory. Add custom categories for building-specific needs.',
  ),
  WalkthroughStep(
    route: '/assets',
    anchorKey: kAssetsListKey,
    title: 'Building assets',
    description:
        'Track physical equipment — elevators, generators, pumps, CCTV. Record sale date, price, and buyer when an asset is disposed of.',
  ),
  WalkthroughStep(
    route: '/audit',
    anchorKey: kAuditListKey,
    title: 'Audit log',
    description:
        'Every write action is logged automatically. Entries cannot be edited or deleted. Use for financial compliance and dispute resolution.',
  ),
];

final _ownerSteps = <WalkthroughStep>[
  WalkthroughStep(
    route: '/home',
    title: 'Your personal overview',
    description:
        'This dashboard shows your unit\'s outstanding balance, most recent payments, and any new expenses the admin has assigned to you.',
  ),
  WalkthroughStep(
    route: '/expenses',
    anchorKey: kExpensesListKey,
    title: 'Your shared expenses',
    description:
        'Every building expense that includes your unit appears here with the total cost, your individual share, and payment status.',
  ),
  WalkthroughStep(
    route: '/payments',
    anchorKey: kPaymentsListKey,
    title: 'Your payment history',
    description:
        'Payments recorded by the admin for your unit are listed here — amount, method, date, and running balance. Tap any row to download a PDF receipt.',
  ),
  WalkthroughStep(
    route: '/notifications',
    anchorKey: kNotificationsListKey,
    title: 'Notifications centre',
    description:
        'You receive alerts for new expenses, confirmed payments, and broadcast announcements. Mark individual items as read from this list.',
  ),
  WalkthroughStep(
    route: '/profile',
    anchorKey: kProfileCardKey,
    title: 'Your profile',
    description:
        'Update your display name, phone number, or password. Email and role are set by the admin — contact them if either needs to change.',
  ),
];

// ─────────────────────────────────────────────────────────────────────────────
// Controller (ChangeNotifier)
// ─────────────────────────────────────────────────────────────────────────────

class WalkthroughController extends ChangeNotifier {
  WalkthroughController._();

  /// Singleton — access from anywhere via WalkthroughController.instance.
  static final instance = WalkthroughController._();

  bool _isRolePicking = false;
  bool _isActive = false;
  TutorialRole? _role;
  int _currentStep = 0;
  GoRouter? _router;

  bool get isRolePicking => _isRolePicking;
  bool get isActive => _isActive;
  TutorialRole? get role => _role;
  int get currentStep => _currentStep;

  List<WalkthroughStep> get steps =>
      _role == TutorialRole.admin ? _adminSteps : _ownerSteps;

  WalkthroughStep? get currentStepData =>
      _isActive && _currentStep < steps.length ? steps[_currentStep] : null;

  /// Call once, e.g. in your root widget's initState:
  ///   WalkthroughController.instance.init(router: GoRouter.of(context));
  void init({required GoRouter router}) {
    _router = router;
  }

  void openRolePicker() {
    _isRolePicking = true;
    notifyListeners();
  }

  void closeRolePicker() {
    _isRolePicking = false;
    notifyListeners();
  }

  void startTutorial(TutorialRole role, BuildContext context) {
    _role = role;
    _isActive = true;
    _isRolePicking = false;
    _currentStep = 0;
    notifyListeners();
    _navigateToCurrentStep(context);
  }

  void next(BuildContext context) {
    if (!_isActive) return;
    if (_currentStep < steps.length - 1) {
      _currentStep++;
      notifyListeners();
      _navigateToCurrentStep(context);
    } else {
      endTutorial();
    }
  }

  void previous(BuildContext context) {
    if (!_isActive || _currentStep == 0) return;
    _currentStep--;
    notifyListeners();
    _navigateToCurrentStep(context);
  }

  void endTutorial() {
    _isActive = false;
    _role = null;
    _currentStep = 0;
    notifyListeners();
  }

  void _navigateToCurrentStep(BuildContext context) {
    final step = currentStepData;
    if (step == null) return;
    final router = _router ?? GoRouter.of(context);
    if (GoRouterState.of(context).matchedLocation != step.route) {
      router.go(step.route);
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SVG spotlight painter
// ─────────────────────────────────────────────────────────────────────────────

class _SpotlightPainter extends CustomPainter {
  _SpotlightPainter({required this.highlight, required this.padding});

  final Rect? highlight;
  final double padding;

  @override
  void paint(Canvas canvas, Size size) {
    final full = Offset.zero & size;
    final paint = Paint()..color = const Color(0x9E000000);

    if (highlight == null) {
      canvas.drawRect(full, paint);
      return;
    }

    final hole = highlight!.inflate(padding);
    final path = Path()
      ..addRect(full)
      ..addRRect(RRect.fromRectAndRadius(hole, const Radius.circular(6)))
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, paint);

    // Blue ring
    final ringPaint = Paint()
      ..color = _kPrimaryBlue
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;
    canvas.drawRRect(
      RRect.fromRectAndRadius(hole, const Radius.circular(6)),
      ringPaint,
    );
  }

  @override
  bool shouldRepaint(_SpotlightPainter old) =>
      old.highlight != highlight || old.padding != padding;
}

// ─────────────────────────────────────────────────────────────────────────────
// Progress dots
// ─────────────────────────────────────────────────────────────────────────────

class _ProgressDots extends StatelessWidget {
  const _ProgressDots({required this.total, required this.current});

  final int total;
  final int current;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(total, (i) {
        final isActive = i == current;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          width: isActive ? 18 : 6,
          height: 6,
          margin: const EdgeInsets.only(right: 4),
          decoration: BoxDecoration(
            color: isActive ? _kPrimaryBlue : const Color(0xFFCBD5E1),
            borderRadius: BorderRadius.circular(99),
          ),
        );
      }),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tooltip card
// ─────────────────────────────────────────────────────────────────────────────

class _TutorialCard extends StatelessWidget {
  const _TutorialCard({
    required this.step,
    required this.stepIndex,
    required this.totalSteps,
    required this.onNext,
    required this.onPrev,
    required this.onEnd,
    required this.alignment,
  });

  final WalkthroughStep step;
  final int stepIndex;
  final int totalSteps;
  final VoidCallback onNext;
  final VoidCallback onPrev;
  final VoidCallback onEnd;
  final Alignment alignment;

  @override
  Widget build(BuildContext context) {
    final isLast = stepIndex == totalSteps - 1;

    return Align(
      alignment: alignment,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          elevation: 16,
          shadowColor: Colors.black26,
          child: Container(
            width: 320,
            decoration: BoxDecoration(
              border: Border.all(color: _kCardBorder, width: 0.5),
              borderRadius: BorderRadius.circular(16),
            ),
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header row: badge + close
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: _kBadgeBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        'STEP ${stepIndex + 1} OF $totalSteps',
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: _kBadgeText,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                    GestureDetector(
                      onTap: onEnd,
                      child: const Icon(Icons.close,
                          size: 18, color: _kBodyText),
                    ),
                  ],
                ),

                const SizedBox(height: 10),

                // Title
                Text(
                  step.title,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: _kHeadText,
                  ),
                ),

                const SizedBox(height: 6),

                // Description
                Text(
                  step.description,
                  style: const TextStyle(
                    fontSize: 13,
                    color: _kBodyText,
                    height: 1.6,
                  ),
                ),

                const SizedBox(height: 16),

                // Footer: dots + navigation
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _ProgressDots(
                        total: totalSteps, current: stepIndex),
                    Row(
                      children: [
                        if (stepIndex > 0)
                          TextButton.icon(
                            onPressed: onPrev,
                            icon: const Icon(Icons.navigate_before,
                                size: 16, color: _kBodyText),
                            label: const Text('Back',
                                style: TextStyle(
                                    color: _kBodyText,
                                    fontWeight: FontWeight.w500)),
                            style: TextButton.styleFrom(
                                padding: EdgeInsets.zero,
                                minimumSize: Size.zero,
                                tapTargetSize:
                                    MaterialTapTargetSize.shrinkWrap),
                          ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: onNext,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _kPrimaryBlue,
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8)),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 14, vertical: 8),
                            minimumSize: Size.zero,
                            tapTargetSize:
                                MaterialTapTargetSize.shrinkWrap,
                            elevation: 0,
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                isLast ? 'Finish' : 'Next',
                                style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 13),
                              ),
                              if (!isLast) ...[
                                const SizedBox(width: 2),
                                const Icon(Icons.navigate_next,
                                    color: Colors.white, size: 16),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Role picker bottom sheet
// ─────────────────────────────────────────────────────────────────────────────

class RolePickerSheet extends StatelessWidget {
  const RolePickerSheet({super.key, required this.controller});

  final WalkthroughController controller;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
      ),
      padding: EdgeInsets.fromLTRB(
          24, 16, 24, MediaQuery.of(context).viewInsets.bottom + 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 36,
              height: 4,
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: const Color(0xFFE5E7EB),
                borderRadius: BorderRadius.circular(99),
              ),
            ),
          ),

          const Text(
            'Choose a tour',
            style: TextStyle(
                fontSize: 18, fontWeight: FontWeight.w700, color: _kHeadText),
          ),

          const SizedBox(height: 6),

          const Text(
            'Select the role you want to explore. The tour will navigate '
            'the app step by step and highlight key features.',
            style: TextStyle(fontSize: 13, color: _kBodyText, height: 1.5),
          ),

          const SizedBox(height: 20),

          // Admin button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                controller.startTutorial(TutorialRole.admin, context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: _kPrimaryBlue,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(vertical: 16),
                elevation: 0,
              ),
              child: const Text(
                'Admin tour — 9 steps',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 15),
              ),
            ),
          ),

          const SizedBox(height: 10),

          // Owner button
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () {
                Navigator.of(context).pop();
                controller.startTutorial(TutorialRole.owner, context);
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: _kPrimaryBlue,
                side: const BorderSide(color: _kPrimaryBlue),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text(
                'Owner tour — 5 steps',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tutorial icon button (AppBar action)
// ─────────────────────────────────────────────────────────────────────────────

class TutorialIconButton extends StatelessWidget {
  const TutorialIconButton({super.key, required this.controller});

  final WalkthroughController controller;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: TextButton.icon(
            onPressed: controller.isActive
                ? null
                : () => showModalBottomSheet(
                      context: context,
                      backgroundColor: Colors.transparent,
                      isScrollControlled: true,
                      builder: (_) =>
                          RolePickerSheet(controller: controller),
                    ),
            icon: const Icon(Icons.school_outlined,
                size: 16, color: Colors.white),
            label: const Text(
              'Tour',
              style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 12),
            ),
            style: TextButton.styleFrom(
              backgroundColor: _kGreen,
              disabledBackgroundColor: _kGreen.withValues(alpha: 0.45),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8)),
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        );
      },
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Walkthrough overlay widget — wraps the page content
// ─────────────────────────────────────────────────────────────────────────────

/// Wrap the body of your root Scaffold (or the MaterialApp builder) with this.
/// It renders the dimmed spotlight and tooltip card on top of all content.
class WalkthroughOverlay extends StatefulWidget {
  const WalkthroughOverlay({
    super.key,
    required this.controller,
    required this.child,
  });

  final WalkthroughController controller;
  final Widget child;

  @override
  State<WalkthroughOverlay> createState() => _WalkthroughOverlayState();
}

class _WalkthroughOverlayState extends State<WalkthroughOverlay> {
  Rect? _anchorRect;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChanged);
    super.dispose();
  }

  void _onControllerChanged() {
    if (!widget.controller.isActive) {
      setState(() => _anchorRect = null);
      return;
    }
    // Schedule after frame so the new page has rendered before we measure.
    WidgetsBinding.instance.addPostFrameCallback((_) => _resolveAnchor());
  }

  void _resolveAnchor() {
    final step = widget.controller.currentStepData;
    if (step == null || step.anchorKey == null) {
      setState(() => _anchorRect = null);
      return;
    }
    final ctx = step.anchorKey!.currentContext;
    if (ctx == null) {
      // Retry once (navigation may still be completing)
      Future.delayed(const Duration(milliseconds: 180), _resolveAnchor);
      return;
    }
    final box = ctx.findRenderObject() as RenderBox?;
    if (box == null || !box.hasSize) {
      setState(() => _anchorRect = null);
      return;
    }
    final pos = box.localToGlobal(Offset.zero);
    setState(() {
      _anchorRect = pos & box.size;
    });
  }

  Alignment _cardAlignment(TutorialPlacement placement) {
    return switch (placement) {
      TutorialPlacement.below => Alignment.bottomCenter,
      TutorialPlacement.above => Alignment.topCenter,
      TutorialPlacement.right => Alignment.centerRight,
      TutorialPlacement.left => Alignment.centerLeft,
      TutorialPlacement.center => Alignment.center,
    };
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.controller,
      builder: (context, _) {
        final ctrl = widget.controller;
        final step = ctrl.currentStepData;

        if (!ctrl.isActive || step == null) {
          return widget.child;
        }

        return Stack(
          children: [
            widget.child,

            // Spotlight (dimmed overlay with hole)
            Positioned.fill(
              child: GestureDetector(
                onTap: ctrl.endTutorial,
                child: CustomPaint(
                  painter: _SpotlightPainter(
                    highlight: _anchorRect,
                    padding: 6,
                  ),
                ),
              ),
            ),

            // Tooltip card (blocks tap-to-dismiss)
            GestureDetector(
              onTap: () {}, // absorb taps so card doesn't close on click
              child: _TutorialCard(
                step: step,
                stepIndex: ctrl.currentStep,
                totalSteps: ctrl.steps.length,
                alignment: _cardAlignment(step.placement),
                onNext: () => ctrl.next(context),
                onPrev: () => ctrl.previous(context),
                onEnd: ctrl.endTutorial,
              ),
            ),
          ],
        );
      },
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Global Keys — attach these to the widgets listed in TUTORIAL_ANCHORS.md
// ─────────────────────────────────────────────────────────────────────────────

/// Admin step 2 — "New Building" FAB / action button
final GlobalKey kAddBuildingKey =
    GlobalKey(debugLabel: 'tutorial:add-building');

/// Admin step 3 — Action icons row on a BuildingCard
final GlobalKey kBuildingActionsKey =
    GlobalKey(debugLabel: 'tutorial:building-actions');

/// Admin step 4 — "Add Expense" FAB / AppBar action
final GlobalKey kAddExpenseKey =
    GlobalKey(debugLabel: 'tutorial:add-expense');

/// Admin step 5 — Expense row actions (PopupMenuButton / icons)
final GlobalKey kExpenseActionsKey =
    GlobalKey(debugLabel: 'tutorial:expense-actions');

/// Admin step 6 — "Add User" FAB
final GlobalKey kAddUserKey =
    GlobalKey(debugLabel: 'tutorial:add-user');

/// Admin step 7 — Categories list / table
final GlobalKey kCategoriesListKey =
    GlobalKey(debugLabel: 'tutorial:categories-list');

/// Admin step 8 — Assets list
final GlobalKey kAssetsListKey =
    GlobalKey(debugLabel: 'tutorial:assets-list');

/// Admin step 9 — Audit log list
final GlobalKey kAuditListKey =
    GlobalKey(debugLabel: 'tutorial:audit-list');

/// Owner step 2 — Expenses list
final GlobalKey kExpensesListKey =
    GlobalKey(debugLabel: 'tutorial:expenses-list');

/// Owner step 3 — Payments list
final GlobalKey kPaymentsListKey =
    GlobalKey(debugLabel: 'tutorial:payments-list');

/// Owner step 4 — Notifications list
final GlobalKey kNotificationsListKey =
    GlobalKey(debugLabel: 'tutorial:notifications-list');

/// Owner step 5 — Profile card / page root
final GlobalKey kProfileCardKey =
    GlobalKey(debugLabel: 'tutorial:profile-card');
