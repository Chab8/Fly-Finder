import 'package:flutter/material.dart';

/// The app's one signature motif: the rings a trout leaves on the surface when it takes an
/// insect. Used twice (home header, analysis screen) and nowhere else.
class RiseRingsPainter extends CustomPainter {
  const RiseRingsPainter({
    required this.color,
    this.progress = 0,
    this.rings = 5,
    this.squash = 1,
    this.anchor = Alignment.center,
    this.radius,
    this.opacity = 0.32,
  });

  final Color color;

  /// 0..1 phase. Animated on the analysis screen, fixed on the home header.
  final double progress;
  final int rings;

  /// Height / width of each ring. Below 1 the rings read as seen across the water.
  final double squash;
  final Alignment anchor;

  /// Outer radius. Defaults to half of the shortest side.
  final double? radius;
  final double opacity;

  @override
  void paint(Canvas canvas, Size size) {
    final center = anchor.alongSize(size);
    final maxRadius = radius ?? size.shortestSide / 2;
    for (var i = 0; i < rings; i++) {
      final t = ((i / rings) + progress) % 1.0;
      final fadeIn = (t * 8).clamp(0.0, 1.0);
      final alpha = opacity * (1 - t) * fadeIn;
      if (alpha <= 0.002) continue;
      final r = maxRadius * t;
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.2 - 1.2 * t
        ..color = color.withValues(alpha: alpha);
      canvas.drawOval(Rect.fromCenter(center: center, width: r * 2, height: r * 2 * squash), paint);
    }
  }

  @override
  bool shouldRepaint(RiseRingsPainter old) =>
      old.color != color || old.progress != progress || old.rings != rings || old.squash != squash || old.anchor != anchor || old.radius != radius || old.opacity != opacity;
}

/// Rings that keep spreading around [child]. Holds still when the system asks to reduce motion.
class RiseRingsAnimation extends StatefulWidget {
  const RiseRingsAnimation({super.key, required this.color, required this.child, this.size = 300});
  final Color color;
  final Widget child;
  final double size;

  @override
  State<RiseRingsAnimation> createState() => _RiseRingsAnimationState();
}

class _RiseRingsAnimationState extends State<RiseRingsAnimation> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this, duration: const Duration(seconds: 4));
  bool _reduceMotion = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduceMotion = MediaQuery.disableAnimationsOf(context);
    if (_reduceMotion) {
      _controller.stop();
    } else if (!_controller.isAnimating) {
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => SizedBox(
        width: widget.size,
        height: widget.size,
        child: Stack(alignment: Alignment.center, children: [
          Positioned.fill(
            child: ExcludeSemantics(
              child: AnimatedBuilder(
                animation: _controller,
                builder: (context, _) => CustomPaint(
                  painter: RiseRingsPainter(color: widget.color, progress: _reduceMotion ? 0.15 : _controller.value, rings: 4, opacity: 0.5),
                ),
              ),
            ),
          ),
          widget.child,
        ]),
      );
}

/// Four corner marks, like a macro-photography viewfinder: tells people where the subject goes.
class ViewfinderPainter extends CustomPainter {
  const ViewfinderPainter({required this.color, this.length = 30, this.strokeWidth = 3});
  final Color color;
  final double length;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = strokeWidth
      ..color = color;
    final w = size.width;
    final h = size.height;
    final path = Path()
      ..moveTo(0, length)
      ..lineTo(0, 0)
      ..lineTo(length, 0)
      ..moveTo(w - length, 0)
      ..lineTo(w, 0)
      ..lineTo(w, length)
      ..moveTo(w, h - length)
      ..lineTo(w, h)
      ..lineTo(w - length, h)
      ..moveTo(length, h)
      ..lineTo(0, h)
      ..lineTo(0, h - length);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(ViewfinderPainter old) => old.color != color || old.length != length || old.strokeWidth != strokeWidth;
}
