/**
 * Notebook Animated Components — Full Interactive Animation Kit
 * Inspired by SVGator's 12 Mobile Animation Patterns (2026)
 * Every animation uses notebook aesthetic: ruled lines, ink, paper textures.
 */
import React, { useRef, useEffect, useState } from 'react';
import { View, Text, Animated, Easing, StyleSheet, TouchableWithoutFeedback, Platform, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width: SW } = Dimensions.get('window');
const INK = '#2C1810';
const ACCENT = '#FFD60A';
const PAPER = '#FDF6E3';
const BLUE = '#2563EB';

// ══════════════════════════════════════════════════
// 1. PRESSABLE CARD — Scale-down micro-animation
// ══════════════════════════════════════════════════
export function PressableCard({ children, onPress, style, activeOpacity = 0.96 }) {
  const scale = useRef(new Animated.Value(1)).current;

  const onPressIn = () => {
    Animated.spring(scale, { toValue: 0.965, friction: 8, tension: 250, useNativeDriver: true }).start();
  };
  const onPressOut = () => {
    Animated.spring(scale, { toValue: 1, friction: 4, tension: 120, useNativeDriver: true }).start();
  };

  return (
    <TouchableWithoutFeedback onPress={onPress} onPressIn={onPressIn} onPressOut={onPressOut}>
      <Animated.View style={[style, { transform: [{ scale }] }]}>
        {children}
      </Animated.View>
    </TouchableWithoutFeedback>
  );
}

// ══════════════════════════════════════════════════
// 2. SKELETON SHIMMER — Loading placeholder
// ══════════════════════════════════════════════════
export function SkeletonCard({ style }) {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 1000, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 1000, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.3, 0.7] });

  return (
    <View style={[sk.card, style]}>
      {/* Ruled lines */}
      {[0, 1, 2, 3, 4].map(i => (
        <View key={i} style={[sk.ruledLine, { top: 12 + i * 28 }]} />
      ))}
      <View style={sk.marginLine} />
      {/* Image placeholder */}
      <Animated.View style={[sk.imgBlock, { opacity }]} />
      {/* Text lines */}
      <View style={sk.textArea}>
        <Animated.View style={[sk.textLine, { width: '35%', opacity }]} />
        <Animated.View style={[sk.textLine, { width: '90%', height: 14, opacity }]} />
        <Animated.View style={[sk.textLine, { width: '60%', height: 14, opacity }]} />
        <View style={sk.row}>
          <Animated.View style={[sk.avatar, { opacity }]} />
          <Animated.View style={[sk.textLine, { width: '40%', opacity }]} />
        </View>
      </View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 3. NOTEBOOK LOADER — Pencil spinning on paper
// ══════════════════════════════════════════════════
export function NotebookLoader({ size = 56, color = INK, text = 'Loading' }) {
  const rotate = useRef(new Animated.Value(0)).current;
  const dotCount = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotate, { toValue: 1, duration: 1400, easing: Easing.linear, useNativeDriver: true })
    ).start();
    Animated.loop(
      Animated.sequence([
        Animated.timing(dotCount, { toValue: 1, duration: 400, useNativeDriver: false }),
        Animated.timing(dotCount, { toValue: 2, duration: 400, useNativeDriver: false }),
        Animated.timing(dotCount, { toValue: 3, duration: 400, useNativeDriver: false }),
        Animated.timing(dotCount, { toValue: 0, duration: 0, useNativeDriver: false }),
      ])
    ).start();
  }, []);

  const rotateI = rotate.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });

  return (
    <View style={ld.wrap}>
      <View style={[ld.circle, { width: size, height: size, borderRadius: size / 2, borderColor: color }]}>
        <Animated.View style={{ transform: [{ rotate: rotateI }] }}>
          <Ionicons name="pencil" size={size * 0.4} color={color} />
        </Animated.View>
      </View>
      <Text style={[ld.text, { color }]}>{text}...</Text>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 4. SUCCESS CHECKMARK — Animated confirmation
// ══════════════════════════════════════════════════
export function SuccessCheck({ visible, size = 70, color = '#059669' }) {
  const scale = useRef(new Animated.Value(0)).current;
  const checkScale = useRef(new Animated.Value(0)).current;
  const ringScale = useRef(new Animated.Value(0.5)).current;
  const ringOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      scale.setValue(0); checkScale.setValue(0); ringScale.setValue(0.5); ringOpacity.setValue(0);
      Animated.sequence([
        Animated.spring(scale, { toValue: 1, friction: 5, tension: 100, useNativeDriver: true }),
        Animated.spring(checkScale, { toValue: 1, friction: 3, tension: 120, useNativeDriver: true }),
        Animated.parallel([
          Animated.timing(ringOpacity, { toValue: 0.5, duration: 150, useNativeDriver: true }),
          Animated.timing(ringScale, { toValue: 1.6, duration: 400, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
        ]),
        Animated.timing(ringOpacity, { toValue: 0, duration: 250, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;
  return (
    <View style={ss.wrap}>
      <Animated.View style={[ss.ring, { width: size * 1.4, height: size * 1.4, borderRadius: size * 0.7, borderColor: color, opacity: ringOpacity, transform: [{ scale: ringScale }] }]} />
      <Animated.View style={[ss.circle, { width: size, height: size, borderRadius: size / 2, backgroundColor: color, transform: [{ scale }] }]}>
        <Animated.View style={{ transform: [{ scale: checkScale }] }}>
          <Ionicons name="checkmark" size={size * 0.5} color="#fff" />
        </Animated.View>
      </Animated.View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 5. BOUNCE ICON — Tab bar icon animation
// ══════════════════════════════════════════════════
export function BounceIcon({ name, size, color, focused }) {
  const bounce = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (focused) {
      bounce.setValue(0.6);
      Animated.spring(bounce, { toValue: 1, friction: 3, tension: 180, useNativeDriver: true }).start();
    }
  }, [focused]);
  return (
    <Animated.View style={{ transform: [{ scale: bounce }] }}>
      <Ionicons name={name} size={size} color={color} />
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 6. HEART BURST — Double-tap like with particles
// ══════════════════════════════════════════════════
export function HeartBurst({ visible, size = 80 }) {
  const heartScale = useRef(new Animated.Value(0)).current;
  const heartOpacity = useRef(new Animated.Value(0)).current;
  const particles = useRef([0, 1, 2, 3, 4, 5].map(() => ({
    scale: new Animated.Value(0), x: new Animated.Value(0), y: new Animated.Value(0), opacity: new Animated.Value(0),
  }))).current;

  useEffect(() => {
    if (visible) {
      heartScale.setValue(0.3); heartOpacity.setValue(1);
      Animated.sequence([
        Animated.spring(heartScale, { toValue: 1.2, friction: 3, tension: 100, useNativeDriver: true }),
        Animated.parallel([
          Animated.spring(heartScale, { toValue: 1, friction: 5, useNativeDriver: true }),
          ...particles.map((p, i) => {
            const a = (i * 60 * Math.PI) / 180;
            return Animated.parallel([
              Animated.timing(p.opacity, { toValue: 1, duration: 100, useNativeDriver: true }),
              Animated.timing(p.x, { toValue: Math.cos(a) * 35, duration: 350, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
              Animated.timing(p.y, { toValue: Math.sin(a) * 35, duration: 350, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
              Animated.timing(p.scale, { toValue: 1, duration: 200, useNativeDriver: true }),
            ]);
          }),
        ]),
        Animated.delay(150),
        Animated.parallel([
          Animated.timing(heartOpacity, { toValue: 0, duration: 200, useNativeDriver: true }),
          ...particles.map(p => Animated.timing(p.opacity, { toValue: 0, duration: 150, useNativeDriver: true })),
        ]),
      ]).start(() => { particles.forEach(p => { p.x.setValue(0); p.y.setValue(0); p.scale.setValue(0); }); });
    }
  }, [visible]);

  if (!visible) return null;
  return (
    <View style={hs.wrap}>
      {particles.map((p, i) => (
        <Animated.View key={i} style={[hs.dot, { opacity: p.opacity, backgroundColor: i % 3 === 0 ? '#ED4956' : i % 3 === 1 ? '#FF6B6B' : ACCENT, transform: [{ translateX: p.x }, { translateY: p.y }, { scale: p.scale }] }]} />
      ))}
      <Animated.View style={{ opacity: heartOpacity, transform: [{ scale: heartScale }] }}>
        <Ionicons name="heart" size={size} color="#ED4956" />
      </Animated.View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// 7. EMPTY STATE — Animated floating icon + doodles
// ══════════════════════════════════════════════════
export function EmptyState({ icon = 'document-text-outline', title = 'Nothing here yet', subtitle, color = '#8A7558' }) {
  const float = useRef(new Animated.Value(0)).current;
  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, { toValue: 1, duration: 600, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      Animated.loop(Animated.sequence([
        Animated.timing(float, { toValue: -10, duration: 1800, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(float, { toValue: 0, duration: 1800, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ])),
    ]).start();
  }, []);

  return (
    <Animated.View style={[es.wrap, { opacity: fade }]}>
      {[0, 1, 2, 3].map(i => <View key={i} style={[es.line, { top: 20 + i * 28 }]} />)}
      <Animated.View style={{ transform: [{ translateY: float }] }}>
        <View style={es.iconCircle}>
          <Ionicons name={icon} size={36} color={color} />
        </View>
      </Animated.View>
      <Text style={es.title}>{title}</Text>
      {subtitle && <Text style={es.subtitle}>{subtitle}</Text>}
      <View style={es.doodle}>
        <View style={es.dash} /><View style={es.dot} />
        <View style={[es.dash, { width: 20, opacity: 0.5 }]} /><View style={es.diamond} />
        <View style={[es.dash, { width: 20, opacity: 0.5 }]} /><View style={es.dot} />
        <View style={es.dash} />
      </View>
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 8. FADE IN VIEW — Smooth entrance animation
// ══════════════════════════════════════════════════
export function FadeInView({ children, delay = 0, duration = 400, from = 'bottom', style }) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translate = useRef(new Animated.Value(from === 'bottom' ? 20 : from === 'top' ? -20 : from === 'left' ? -20 : 20)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(opacity, { toValue: 1, duration, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
        Animated.timing(translate, { toValue: 0, duration, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      ]),
    ]).start();
  }, []);

  const transform = from === 'left' || from === 'right' ? [{ translateX: translate }] : [{ translateY: translate }];
  return <Animated.View style={[style, { opacity, transform }]}>{children}</Animated.View>;
}

// ══════════════════════════════════════════════════
// 9. ANIMATED SEARCH BAR — Expands on focus
// ══════════════════════════════════════════════════
export function AnimatedSearchWrapper({ focused, children, style }) {
  const borderColor = useRef(new Animated.Value(0)).current;
  const elevation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(borderColor, { toValue: focused ? 1 : 0, duration: 200, useNativeDriver: false }),
      Animated.timing(elevation, { toValue: focused ? 1 : 0, duration: 200, useNativeDriver: false }),
    ]).start();
  }, [focused]);

  const borderColorI = borderColor.interpolate({ inputRange: [0, 1], outputRange: [INK, BLUE] });
  const shadowOpacity = elevation.interpolate({ inputRange: [0, 1], outputRange: [0.8, 1] });

  return (
    <Animated.View style={[style, { borderColor: borderColorI, ...Platform.select({ ios: { shadowOpacity }, android: {} }) }]}>
      {children}
    </Animated.View>
  );
}

// ══════════════════════════════════════════════════
// 10. ANIMATED CHIP — Scale bounce on select
// ══════════════════════════════════════════════════
export function AnimatedChip({ children, active, onPress, style, activeStyle }) {
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (active) {
      scale.setValue(0.85);
      Animated.spring(scale, { toValue: 1, friction: 4, tension: 150, useNativeDriver: true }).start();
    }
  }, [active]);

  return (
    <TouchableWithoutFeedback onPress={onPress}>
      <Animated.View style={[style, active && activeStyle, { transform: [{ scale }] }]}>
        {children}
      </Animated.View>
    </TouchableWithoutFeedback>
  );
}

// ══════════════════════════════════════════════════
// 11. STAGGERED LIST — Children animate in one by one
// ══════════════════════════════════════════════════
export function StaggeredItem({ children, index, style }) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(25)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.delay(index * 80),
      Animated.parallel([
        Animated.timing(opacity, { toValue: 1, duration: 350, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
        Animated.timing(translateY, { toValue: 0, duration: 400, easing: Easing.out(Easing.back(1.2)), useNativeDriver: true }),
      ]),
    ]).start();
  }, []);

  return <Animated.View style={[style, { opacity, transform: [{ translateY }] }]}>{children}</Animated.View>;
}

// ══════════════════════════════════════════════════
// 12. PULL REFRESH INDICATOR — Notebook pencil
// ══════════════════════════════════════════════════
export function NotebookRefreshControl({ refreshing }) {
  const rotate = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (refreshing) {
      Animated.loop(
        Animated.timing(rotate, { toValue: 1, duration: 800, easing: Easing.linear, useNativeDriver: true })
      ).start();
    } else {
      rotate.setValue(0);
    }
  }, [refreshing]);

  if (!refreshing) return null;
  const rotateI = rotate.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });

  return (
    <View style={pr.wrap}>
      <Animated.View style={{ transform: [{ rotate: rotateI }] }}>
        <View style={pr.circle}>
          <Ionicons name="pencil" size={16} color={INK} />
        </View>
      </Animated.View>
    </View>
  );
}

// ══════════════════════════════════════════════════
// STYLES
// ══════════════════════════════════════════════════
const sk = StyleSheet.create({
  card: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#E6D5B8',
    borderTopLeftRadius: 3, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 3,
    overflow: 'hidden', marginBottom: 18,
  },
  ruledLine: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.08)' },
  marginLine: { position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.06)' },
  imgBlock: { height: 180, backgroundColor: '#F3EACD', borderBottomWidth: 1, borderBottomColor: '#E6D5B8' },
  textArea: { padding: 14, gap: 10 },
  textLine: { height: 10, backgroundColor: '#E6D5B8', borderRadius: 4 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 4 },
  avatar: { width: 26, height: 26, borderRadius: 13, backgroundColor: '#E6D5B8' },
});

const ld = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center', paddingVertical: 30 },
  circle: { borderWidth: 2.5, borderStyle: 'dashed', justifyContent: 'center', alignItems: 'center' },
  text: { marginTop: 10, fontSize: 11, fontWeight: '700', letterSpacing: 2, textTransform: 'uppercase' },
});

const ss = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center' },
  ring: { position: 'absolute', borderWidth: 2 },
  circle: { justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8 },
      android: { elevation: 6 },
    }),
  },
});

const hs = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center' },
  dot: { position: 'absolute', width: 8, height: 8, borderRadius: 4 },
});

const es = StyleSheet.create({
  wrap: { alignItems: 'center', paddingVertical: 50, paddingHorizontal: 30 },
  line: { position: 'absolute', left: 20, right: 20, height: 1, backgroundColor: 'rgba(90,150,210,0.08)' },
  iconCircle: { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(255,214,10,0.08)', borderWidth: 2, borderColor: '#E6D5B8', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 18, fontWeight: '800', color: INK, marginBottom: 6 },
  subtitle: { fontSize: 13, textAlign: 'center', lineHeight: 19, color: '#8A7558' },
  doodle: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 20 },
  dash: { width: 12, height: 2, backgroundColor: '#C4AA78', borderRadius: 1 },
  dot: { width: 4, height: 4, borderRadius: 2, backgroundColor: '#C4AA78' },
  diamond: { width: 6, height: 6, backgroundColor: '#C4AA78', borderRadius: 1, transform: [{ rotate: '45deg' }] },
});

const pr = StyleSheet.create({
  wrap: { alignItems: 'center', paddingVertical: 10 },
  circle: { width: 32, height: 32, borderRadius: 16, borderWidth: 2, borderColor: INK, borderStyle: 'dashed', justifyContent: 'center', alignItems: 'center', backgroundColor: PAPER },
});
