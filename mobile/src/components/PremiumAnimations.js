/**
 * Premium Notebook Animations — High-End Interactive Effects
 * Parallax, 3D tilt, ink ripples, confetti, typewriter, floating particles,
 * animated counters, progress rings — all in notebook aesthetic.
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { View, Text, Animated, Easing, StyleSheet, Dimensions, Platform, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width: SW, height: SH } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';

// ══════════════════════════════════════════════════
// 1. PARALLAX SCROLL HEADER — Compresses on scroll
// ══════════════════════════════════════════════════
export function ParallaxHeader({ scrollY, maxHeight = 120, minHeight = 60, children }) {
  const headerHeight = scrollY.interpolate({
    inputRange: [0, maxHeight - minHeight],
    outputRange: [maxHeight, minHeight],
    extrapolate: 'clamp',
  });
  const headerOpacity = scrollY.interpolate({
    inputRange: [0, (maxHeight - minHeight) * 0.6],
    outputRange: [1, 0],
    extrapolate: 'clamp',
  });
  const headerScale = scrollY.interpolate({
    inputRange: [0, maxHeight - minHeight],
    outputRange: [1, 0.9],
    extrapolate: 'clamp',
  });

  return (
    <Animated.View style={[ph.header, { height: headerHeight }]}>
      <Animated.View style={{ opacity: headerOpacity, transform: [{ scale: headerScale }], flex: 1 }}>
        {children}
      </Animated.View>
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 2. 3D TILT CARD — Tilts based on scroll position
// ══════════════════════════════════════════════════
export function TiltCard({ children, scrollY, index, style }) {
  const itemOffset = index * 300;
  const rotateX = scrollY.interpolate({
    inputRange: [itemOffset - 400, itemOffset, itemOffset + 400],
    outputRange: ['8deg', '0deg', '-8deg'],
    extrapolate: 'clamp',
  });
  const scaleVal = scrollY.interpolate({
    inputRange: [itemOffset - 300, itemOffset, itemOffset + 300],
    outputRange: [0.92, 1, 0.92],
    extrapolate: 'clamp',
  });
  const opacityVal = scrollY.interpolate({
    inputRange: [itemOffset - 400, itemOffset, itemOffset + 400],
    outputRange: [0.7, 1, 0.7],
    extrapolate: 'clamp',
  });

  return (
    <Animated.View style={[style, {
      transform: [{ perspective: 1000 }, { rotateX }, { scale: scaleVal }],
      opacity: opacityVal,
    }]}>
      {children}
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 3. INK RIPPLE — Splash effect on tap
// ══════════════════════════════════════════════════
export function InkRippleButton({ onPress, children, style, rippleColor = 'rgba(44,24,16,0.08)' }) {
  const rippleScale = useRef(new Animated.Value(0)).current;
  const rippleOpacity = useRef(new Animated.Value(0)).current;
  const [ripplePos, setRipplePos] = useState({ x: 0, y: 0 });

  const handlePress = (e) => {
    const { locationX, locationY } = e.nativeEvent;
    setRipplePos({ x: locationX, y: locationY });
    rippleScale.setValue(0);
    rippleOpacity.setValue(1);
    Animated.parallel([
      Animated.timing(rippleScale, { toValue: 1, duration: 400, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      Animated.timing(rippleOpacity, { toValue: 0, duration: 400, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
    ]).start();
    onPress && onPress();
  };

  return (
    <TouchableOpacity activeOpacity={0.9} onPress={handlePress} style={[style, { overflow: 'hidden' }]}>
      <Animated.View style={[ir.ripple, {
        left: ripplePos.x - 50, top: ripplePos.y - 50,
        backgroundColor: rippleColor,
        opacity: rippleOpacity,
        transform: [{ scale: rippleScale.interpolate({ inputRange: [0, 1], outputRange: [0.3, 4] }) }],
      }]} />
      {children}
    </TouchableOpacity>
  );
}

// ══════════════════════════════════════════════════
// 4. CONFETTI BURST — Celebration particles
// ══════════════════════════════════════════════════
export function ConfettiBurst({ visible, count = 20 }) {
  const particles = useRef(Array.from({ length: count }, () => ({
    x: new Animated.Value(0),
    y: new Animated.Value(0),
    rotate: new Animated.Value(0),
    opacity: new Animated.Value(0),
    scale: new Animated.Value(0),
  }))).current;

  const colors = ['#FFD60A', '#2563EB', '#DC2626', '#059669', '#7C3AED', '#EA580C', '#EC4899', '#0D9488'];

  useEffect(() => {
    if (visible) {
      particles.forEach((p, i) => {
        const angle = (Math.random() * 360 * Math.PI) / 180;
        const dist = 60 + Math.random() * 100;
        p.x.setValue(0); p.y.setValue(0); p.rotate.setValue(0);
        p.opacity.setValue(0); p.scale.setValue(0);

        Animated.sequence([
          Animated.delay(i * 20),
          Animated.parallel([
            Animated.timing(p.opacity, { toValue: 1, duration: 100, useNativeDriver: true }),
            Animated.timing(p.scale, { toValue: 0.5 + Math.random() * 1, duration: 200, useNativeDriver: true }),
            Animated.timing(p.x, { toValue: Math.cos(angle) * dist, duration: 600, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
            Animated.timing(p.y, { toValue: Math.sin(angle) * dist - 40, duration: 700, easing: Easing.out(Easing.quad), useNativeDriver: true }),
            Animated.timing(p.rotate, { toValue: Math.random() * 4, duration: 700, useNativeDriver: true }),
          ]),
          Animated.timing(p.opacity, { toValue: 0, duration: 300, useNativeDriver: true }),
        ]).start();
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <View style={cf.wrap} pointerEvents="none">
      {particles.map((p, i) => {
        const rotateI = p.rotate.interpolate({ inputRange: [0, 4], outputRange: ['0deg', '720deg'] });
        const isSquare = i % 3 === 0;
        const isLine = i % 3 === 1;
        return (
          <Animated.View key={i} style={[cf.particle, {
            backgroundColor: colors[i % colors.length],
            width: isLine ? 3 : isSquare ? 8 : 6,
            height: isLine ? 14 : isSquare ? 8 : 6,
            borderRadius: isSquare ? 1 : 3,
            opacity: p.opacity,
            transform: [{ translateX: p.x }, { translateY: p.y }, { scale: p.scale }, { rotate: rotateI }],
          }]} />
        );
      })}
    </View>
  );
}

// ══════════════════════════════════════════════════
// 5. TYPEWRITER TEXT — Types letter by letter
// ══════════════════════════════════════════════════
export function TypewriterText({ text, style, speed = 50, delay = 0 }) {
  const [displayed, setDisplayed] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    let i = 0;
    const timeout = setTimeout(() => {
      const interval = setInterval(() => {
        if (i < text.length) {
          setDisplayed(text.substring(0, i + 1));
          i++;
        } else {
          clearInterval(interval);
          setTimeout(() => setCursorVisible(false), 500);
        }
      }, speed);
      return () => clearInterval(interval);
    }, delay);
    return () => clearTimeout(timeout);
  }, [text]);

  return (
    <Text style={style}>
      {displayed}
      {cursorVisible && <Text style={[style, { color: ACCENT }]}>|</Text>}
    </Text>
  );
}

// ══════════════════════════════════════════════════
// 6. ANIMATED COUNTER — Numbers count up
// ══════════════════════════════════════════════════
export function AnimatedCounter({ value, duration = 1000, style, suffix = '' }) {
  const animValue = useRef(new Animated.Value(0)).current;
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    animValue.setValue(0);
    Animated.timing(animValue, { toValue: value, duration, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
    const listener = animValue.addListener(({ value: v }) => setDisplay(Math.round(v)));
    return () => animValue.removeListener(listener);
  }, [value]);

  return <Text style={style}>{display.toLocaleString()}{suffix}</Text>;
}

// ══════════════════════════════════════════════════
// 7. PROGRESS RING — Animated circular progress
// ══════════════════════════════════════════════════
export function ProgressRing({ progress = 0, size = 60, strokeWidth = 4, color = ACCENT, bgColor = '#E6D5B8', children }) {
  const animProgress = useRef(new Animated.Value(0)).current;
  const circumference = (size - strokeWidth) * Math.PI;

  useEffect(() => {
    Animated.timing(animProgress, { toValue: progress, duration: 1200, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [progress]);

  // We'll fake the ring with overlapping views since SVG isn't available
  const rotation = animProgress.interpolate({
    inputRange: [0, 100],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={[pg.wrap, { width: size, height: size }]}>
      {/* Background circle */}
      <View style={[pg.ring, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth, borderColor: bgColor }]} />
      {/* Progress arc — using rotation trick */}
      <View style={[pg.halfWrap, { width: size / 2, height: size, left: 0 }]}>
        <Animated.View style={[pg.halfCircle, {
          width: size, height: size, borderRadius: size / 2,
          borderWidth: strokeWidth, borderColor: color,
          borderRightColor: 'transparent', borderBottomColor: 'transparent',
          transform: [{ rotate: rotation }],
        }]} />
      </View>
      {/* Center content */}
      <View style={pg.center}>
        {children}
      </View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 8. FLOATING PARTICLES BG — Subtle paper texture
// ══════════════════════════════════════════════════
export function FloatingParticles({ count = 8 }) {
  const particles = useRef(Array.from({ length: count }, () => ({
    x: new Animated.Value(Math.random() * SW),
    y: new Animated.Value(Math.random() * SH),
    opacity: new Animated.Value(0.04 + Math.random() * 0.06),
    size: 4 + Math.random() * 8,
  }))).current;

  useEffect(() => {
    particles.forEach((p) => {
      const drift = () => {
        Animated.sequence([
          Animated.parallel([
            Animated.timing(p.x, { toValue: Math.random() * SW, duration: 8000 + Math.random() * 6000, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
            Animated.timing(p.y, { toValue: Math.random() * SH, duration: 8000 + Math.random() * 6000, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
          ]),
        ]).start(() => drift());
      };
      drift();
    });
  }, []);

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {particles.map((p, i) => (
        <Animated.View key={i} style={{
          position: 'absolute',
          width: p.size, height: p.size,
          borderRadius: i % 2 === 0 ? p.size / 2 : 1,
          backgroundColor: INK,
          opacity: p.opacity,
          transform: [{ translateX: p.x }, { translateY: p.y }, { rotate: i % 2 === 0 ? '0deg' : '45deg' }],
        }} />
      ))}
    </View>
  );
}

// ══════════════════════════════════════════════════
// 9. SWIPE REVEAL ACTIONS — Swipe card for actions
// ══════════════════════════════════════════════════
export function SwipeRevealCard({ children, onSwipeLeft, onSwipeRight, leftContent, rightContent, style }) {
  const translateX = useRef(new Animated.Value(0)).current;

  const onMoveShouldSetResponder = (e) => {
    return Math.abs(e.nativeEvent.pageX) > 10;
  };

  const onResponderMove = (e) => {
    const dx = e.nativeEvent.pageX - (e.nativeEvent.pageX - e.nativeEvent.locationX);
    translateX.setValue(Math.max(-80, Math.min(80, e.nativeEvent.locationX - SW / 2)));
  };

  const onResponderRelease = () => {
    Animated.spring(translateX, { toValue: 0, friction: 6, tension: 100, useNativeDriver: true }).start();
  };

  return (
    <View style={[sw.wrap, style]}>
      {/* Background actions */}
      <View style={sw.actions}>
        <View style={sw.leftAction}>{leftContent}</View>
        <View style={sw.rightAction}>{rightContent}</View>
      </View>
      {/* Main content */}
      <Animated.View style={[sw.content, { transform: [{ translateX }] }]}
        onMoveShouldSetResponder={onMoveShouldSetResponder}
        onResponderMove={onResponderMove}
        onResponderRelease={onResponderRelease}
      >
        {children}
      </Animated.View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 10. NOTEBOOK PAGE TURN — Screen transition effect
// ══════════════════════════════════════════════════
export function PageTurnTransition({ visible, children, onComplete }) {
  const rotateY = useRef(new Animated.Value(visible ? -90 : 0)).current;
  const opacity = useRef(new Animated.Value(visible ? 0 : 1)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(rotateY, { toValue: 0, duration: 500, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 1, duration: 300, useNativeDriver: true }),
      ]).start(() => onComplete && onComplete());
    }
  }, [visible]);

  const rotateI = rotateY.interpolate({ inputRange: [-90, 0], outputRange: ['-90deg', '0deg'] });

  return (
    <Animated.View style={[pt.page, { opacity, transform: [{ perspective: 1200 }, { rotateY: rotateI }] }]}>
      {/* Paper shadow on left edge */}
      <View style={pt.shadow} />
      {children}
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 11. PULSE GLOW — Subtle pulsing glow effect
// ══════════════════════════════════════════════════
export function PulseGlow({ size = 40, color = ACCENT, children, style }) {
  const pulse = useRef(new Animated.Value(1)).current;
  const glowOpacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(pulse, { toValue: 1.15, duration: 1200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
          Animated.timing(glowOpacity, { toValue: 0.1, duration: 1200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        ]),
        Animated.parallel([
          Animated.timing(pulse, { toValue: 1, duration: 1200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
          Animated.timing(glowOpacity, { toValue: 0.3, duration: 1200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        ]),
      ])
    ).start();
  }, []);

  return (
    <View style={[gl.wrap, style]}>
      <Animated.View style={[gl.glow, {
        width: size * 1.5, height: size * 1.5, borderRadius: size * 0.75,
        backgroundColor: color, opacity: glowOpacity, transform: [{ scale: pulse }],
      }]} />
      {children}
    </View>
  );
}

// ══════════════════════════════════════════════════
// STYLES
// ══════════════════════════════════════════════════
const ph = StyleSheet.create({
  header: { overflow: 'hidden', backgroundColor: PAPER, zIndex: 10 },
});

const ir = StyleSheet.create({
  ripple: { position: 'absolute', width: 100, height: 100, borderRadius: 50 },
});

const cf = StyleSheet.create({
  wrap: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', zIndex: 999 },
  particle: { position: 'absolute' },
});

const pg = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center' },
  ring: { position: 'absolute' },
  halfWrap: { position: 'absolute', overflow: 'hidden' },
  halfCircle: { position: 'absolute' },
  center: { position: 'absolute', alignItems: 'center', justifyContent: 'center' },
});

const sw = StyleSheet.create({
  wrap: { position: 'relative', overflow: 'hidden' },
  actions: { ...StyleSheet.absoluteFillObject, flexDirection: 'row', justifyContent: 'space-between' },
  leftAction: { width: 80, justifyContent: 'center', alignItems: 'center', backgroundColor: '#059669' },
  rightAction: { width: 80, justifyContent: 'center', alignItems: 'center', backgroundColor: '#DC2626' },
  content: { backgroundColor: PAPER },
});

const pt = StyleSheet.create({
  page: { flex: 1, backgroundColor: PAPER },
  shadow: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, backgroundColor: 'rgba(0,0,0,0.05)' },
});

const gl = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center' },
  glow: { position: 'absolute' },
});
