import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions, StatusBar, Platform, Easing } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width, height } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';

// Split into two lines for full-screen impact
const LINE1 = ['S','c','r','o','l','l'];
const LINE2 = ['F','o','r','w','a','r','d'];

export default function SplashScreen({ onFinish }) {
  // Background
  const bgOpacity = useRef(new Animated.Value(0)).current;

  // Ruled lines wipe
  const linesClipY = useRef(new Animated.Value(height)).current;

  // LINE 1 letters — "Scroll"
  const l1Anims = useRef(LINE1.map(() => ({
    opacity: new Animated.Value(0),
    y: new Animated.Value(60),
    scale: new Animated.Value(0.3),
  }))).current;

  // The big "U" — special animation
  const uScale = useRef(new Animated.Value(0)).current;
  const uOpacity = useRef(new Animated.Value(0)).current;
  const uRotate = useRef(new Animated.Value(0)).current;
  // Spinning ring around U
  const ringScale = useRef(new Animated.Value(0)).current;
  const ringOpacity = useRef(new Animated.Value(0)).current;
  const ringRotate = useRef(new Animated.Value(0)).current;
  // Second ring pulse
  const ring2Scale = useRef(new Animated.Value(0.5)).current;
  const ring2Opacity = useRef(new Animated.Value(0)).current;

  // LINE 2 letters — "Forward"
  const l2Anims = useRef(LINE2.map(() => ({
    opacity: new Animated.Value(0),
    y: new Animated.Value(60),
    scale: new Animated.Value(0.3),
  }))).current;

  // Marker underline
  const markerX = useRef(new Animated.Value(-width)).current;

  // Tagline
  const tagOpacity = useRef(new Animated.Value(0)).current;
  const tagY = useRef(new Animated.Value(15)).current;

  // Bottom — notebook deco
  const bottomOpacity = useRef(new Animated.Value(0)).current;

  // Logo icon (small, above text)
  const iconOpacity = useRef(new Animated.Value(0)).current;
  const iconScale = useRef(new Animated.Value(0)).current;

  // Exit
  const fade = useRef(new Animated.Value(1)).current;

  const easeOut = Easing.out(Easing.cubic);
  const easeBack = Easing.out(Easing.back(1.5));

  useEffect(() => { go(); }, []);

  const go = () => {
    Animated.sequence([

      // ── 1. Background + ruled lines wipe down (0-500ms) ──
      Animated.parallel([
        Animated.timing(bgOpacity, { toValue: 1, duration: 300, easing: easeOut, useNativeDriver: true }),
        Animated.timing(linesClipY, { toValue: 0, duration: 500, easing: Easing.out(Easing.quad), useNativeDriver: true }),
      ]),

      // ── 2. Small logo icon drops in (500-700ms) ──
      Animated.parallel([
        Animated.timing(iconOpacity, { toValue: 1, duration: 250, easing: easeOut, useNativeDriver: true }),
        Animated.timing(iconScale, { toValue: 1, duration: 350, easing: easeBack, useNativeDriver: true }),
      ]),

      // ── 3. "Scroll" — letters rise up one by one (700-1200ms) ──
      Animated.stagger(55, l1Anims.map(a =>
        Animated.parallel([
          Animated.timing(a.opacity, { toValue: 1, duration: 250, easing: easeOut, useNativeDriver: true }),
          Animated.timing(a.y, { toValue: 0, duration: 350, easing: easeBack, useNativeDriver: true }),
          Animated.timing(a.scale, { toValue: 1, duration: 350, easing: easeBack, useNativeDriver: true }),
        ])
      )),

      // ── 4. THE "U" — big special reveal (1200-1700ms) ──
      Animated.parallel([
        // Ring spins in first
        Animated.parallel([
          Animated.timing(ringScale, { toValue: 1, duration: 400, easing: easeOut, useNativeDriver: true }),
          Animated.timing(ringOpacity, { toValue: 1, duration: 300, easing: easeOut, useNativeDriver: true }),
          Animated.timing(ringRotate, { toValue: 1, duration: 600, easing: Easing.out(Easing.quad), useNativeDriver: true }),
        ]),
        // Then U letter appears
        Animated.sequence([
          Animated.delay(150),
          Animated.parallel([
            Animated.timing(uOpacity, { toValue: 1, duration: 250, easing: easeOut, useNativeDriver: true }),
            Animated.timing(uScale, { toValue: 1, duration: 400, easing: easeBack, useNativeDriver: true }),
            Animated.timing(uRotate, { toValue: 1, duration: 500, easing: Easing.out(Easing.quad), useNativeDriver: true }),
          ]),
        ]),
        // Second ring pulse
        Animated.sequence([
          Animated.delay(250),
          Animated.parallel([
            Animated.timing(ring2Opacity, { toValue: 0.5, duration: 200, useNativeDriver: true }),
            Animated.timing(ring2Scale, { toValue: 1.8, duration: 500, easing: easeOut, useNativeDriver: true }),
          ]),
          Animated.timing(ring2Opacity, { toValue: 0, duration: 300, useNativeDriver: true }),
        ]),
        // First ring fades after pulse
        Animated.sequence([
          Animated.delay(400),
          Animated.timing(ringOpacity, { toValue: 0, duration: 300, useNativeDriver: true }),
        ]),
      ]),

      // ── 5. "Forward" — letters rise up (1700-2200ms) ──
      Animated.stagger(50, l2Anims.map(a =>
        Animated.parallel([
          Animated.timing(a.opacity, { toValue: 1, duration: 250, easing: easeOut, useNativeDriver: true }),
          Animated.timing(a.y, { toValue: 0, duration: 350, easing: easeBack, useNativeDriver: true }),
          Animated.timing(a.scale, { toValue: 1, duration: 350, easing: easeBack, useNativeDriver: true }),
        ])
      )),

      // ── 6. Marker underline sweeps across (2200-2500ms) ──
      Animated.timing(markerX, { toValue: 0, duration: 300, easing: easeOut, useNativeDriver: true }),

      // ── 7. Tagline + bottom deco (2500-2800ms) ──
      Animated.parallel([
        Animated.parallel([
          Animated.timing(tagOpacity, { toValue: 1, duration: 300, easing: easeOut, useNativeDriver: true }),
          Animated.timing(tagY, { toValue: 0, duration: 350, easing: easeBack, useNativeDriver: true }),
        ]),
        Animated.sequence([
          Animated.delay(150),
          Animated.timing(bottomOpacity, { toValue: 1, duration: 250, easing: easeOut, useNativeDriver: true }),
        ]),
      ]),

      // ── 8. Hold + exit (2800-3200ms) ──
      Animated.delay(300),
      Animated.timing(fade, { toValue: 0, duration: 300, easing: Easing.inOut(Easing.cubic), useNativeDriver: true }),

    ]).start(() => onFinish());
  };

  const ringRotateI = ringRotate.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const uRotateI = uRotate.interpolate({ inputRange: [0, 1], outputRange: ['-15deg', '0deg'] });

  return (
    <Animated.View style={[st.container, { opacity: fade }]}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      {/* ═══ BACKGROUND ═══ */}
      <Animated.View style={[st.bg, { opacity: bgOpacity }]} />

      {/* ═══ RULED LINES (wipe down) ═══ */}
      <Animated.View style={[st.linesWrap, { transform: [{ translateY: linesClipY }] }]}>
        {Array.from({ length: Math.ceil(height / 28) + 1 }, (_, i) => (
          <View key={i} style={[st.ruled, { top: i * 28 }]} />
        ))}
        <View style={st.margin} />
        {[0.1, 0.3, 0.5, 0.7, 0.9].map((p, i) => (
          <View key={`h${i}`} style={[st.hole, { top: `${p * 100}%` }]} />
        ))}
      </Animated.View>

      {/* ═══ SMALL LOGO ICON ═══ */}
      <Animated.View style={[st.iconWrap, {
        opacity: iconOpacity,
        transform: [{ scale: iconScale }],
      }]}>
        <View style={st.iconCircle}>
          <Ionicons name="school" size={22} color={ACCENT} />
        </View>
      </Animated.View>

      {/* ═══ LINE 1: "Scroll" ═══ */}
      <View style={st.line1}>
        {LINE1.map((ch, i) => (
          <Animated.Text key={`l1-${i}`} style={[st.bigLetter, {
            opacity: l1Anims[i].opacity,
            transform: [
              { translateY: l1Anims[i].y },
              { scale: l1Anims[i].scale },
            ],
          }]}>
            {ch}
          </Animated.Text>
        ))}

        {/* ═══ THE "U" — with spinning ring ═══ */}
        <View style={st.uContainer}>
          {/* Dotted ring */}
          <Animated.View style={[st.uRing, {
            opacity: ringOpacity,
            transform: [{ scale: ringScale }, { rotate: ringRotateI }],
          }]}>
            {Array.from({ length: 12 }, (_, i) => {
              const angle = (i * 30 * Math.PI) / 180;
              return (
                <View key={i} style={[st.ringDot, {
                  left: 28 + Math.cos(angle) * 28,
                  top: 28 + Math.sin(angle) * 28,
                  backgroundColor: i % 3 === 0 ? ACCENT : i % 3 === 1 ? BLUE : '#DC2626',
                }]} />
              );
            })}
          </Animated.View>

          {/* Pulse ring */}
          <Animated.View style={[st.uPulseRing, {
            opacity: ring2Opacity,
            transform: [{ scale: ring2Scale }],
          }]} />

          {/* The U letter */}
          <Animated.Text style={[st.uLetter, {
            opacity: uOpacity,
            transform: [{ scale: uScale }, { rotate: uRotateI }],
          }]}>
            U
          </Animated.Text>
        </View>
      </View>

      {/* ═══ LINE 2: "Forward" ═══ */}
      <View style={st.line2}>
        {LINE2.map((ch, i) => (
          <Animated.Text key={`l2-${i}`} style={[st.bigLetter2, {
            opacity: l2Anims[i].opacity,
            transform: [
              { translateY: l2Anims[i].y },
              { scale: l2Anims[i].scale },
            ],
          }]}>
            {ch}
          </Animated.Text>
        ))}
      </View>

      {/* ═══ MARKER UNDERLINE ═══ */}
      <Animated.View style={[st.markerWrap, { transform: [{ translateX: markerX }] }]}>
        <View style={st.markerThick} />
        <View style={st.markerThin} />
      </Animated.View>

      {/* ═══ TAGLINE ═══ */}
      <Animated.Text style={[st.tagline, {
        opacity: tagOpacity,
        transform: [{ translateY: tagY }],
      }]}>
        Where Curiosity Scales
      </Animated.Text>

      {/* ═══ BOTTOM DECORATION ═══ */}
      <Animated.View style={[st.bottom, { opacity: bottomOpacity }]}>
        <View style={st.tapeLabel}>
          <Text style={st.tapeLabelText}>YOUR KNOWLEDGE JOURNAL</Text>
        </View>
        <View style={st.dividerRow}>
          <View style={[st.divLine, { width: 20 }]} />
          <View style={st.divDot} />
          <View style={[st.divLine, { width: 35, opacity: 0.5 }]} />
          <Ionicons name="school-outline" size={10} color="#C4AA78" />
          <View style={[st.divLine, { width: 35, opacity: 0.5 }]} />
          <View style={st.divDot} />
          <View style={[st.divLine, { width: 20 }]} />
        </View>
      </Animated.View>
    </Animated.View>
  );
}

const LETTER_SIZE = 52;
const U_SIZE = 62;

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#E8DCBE' },

  bg: { ...StyleSheet.absoluteFillObject, backgroundColor: PAPER },

  // Ruled lines
  linesWrap: { ...StyleSheet.absoluteFillObject },
  ruled: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.10)' },
  margin: { position: 'absolute', left: 44, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.12)' },
  hole: {
    position: 'absolute', left: 14, width: 14, height: 14, borderRadius: 7,
    backgroundColor: '#E6D5B8', borderWidth: 1.5, borderColor: '#C4AA78',
  },

  // Logo icon
  iconWrap: {
    position: 'absolute',
    top: height * 0.32,
    alignSelf: 'center',
  },
  iconCircle: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(255,214,10,0.08)',
    borderWidth: 2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 3 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },

  // Line 1: "ScrollU"
  line1: {
    position: 'absolute',
    top: height * 0.32 + 56,
    flexDirection: 'row', alignItems: 'center',
    alignSelf: 'center',
  },
  bigLetter: {
    fontSize: LETTER_SIZE, fontWeight: '900', color: INK,
    letterSpacing: -2,
  },

  // U container with ring
  uContainer: {
    width: U_SIZE + 10, height: U_SIZE + 16,
    alignItems: 'center', justifyContent: 'center',
    marginHorizontal: -2,
  },
  uRing: {
    position: 'absolute',
    width: 60, height: 60,
  },
  ringDot: {
    position: 'absolute',
    width: 5, height: 5, borderRadius: 2.5,
    marginLeft: -2.5, marginTop: -2.5,
  },
  uPulseRing: {
    position: 'absolute',
    width: 50, height: 50, borderRadius: 25,
    borderWidth: 2, borderColor: ACCENT,
  },
  uLetter: {
    fontSize: U_SIZE, fontWeight: '900', color: BLUE,
    fontStyle: 'italic',
  },

  // Line 2: "Forward"
  line2: {
    position: 'absolute',
    top: height * 0.32 + 56 + LETTER_SIZE + 2,
    flexDirection: 'row',
    alignSelf: 'center',
  },
  bigLetter2: {
    fontSize: LETTER_SIZE - 4, fontWeight: '900', color: INK,
    letterSpacing: -1.5,
  },

  // Marker underline
  markerWrap: {
    position: 'absolute',
    top: height * 0.32 + 56 + LETTER_SIZE * 2 + 6,
    alignSelf: 'center',
    width: width * 0.55,
    flexDirection: 'row', gap: 4,
  },
  markerThick: {
    flex: 3, height: 7, backgroundColor: 'rgba(255,214,10,0.50)',
    borderRadius: 4, transform: [{ rotate: '-0.8deg' }],
  },
  markerThin: {
    flex: 2, height: 4, backgroundColor: INK, opacity: 0.08,
    borderRadius: 3, marginTop: 2,
  },

  // Tagline
  tagline: {
    position: 'absolute',
    top: height * 0.32 + 56 + LETTER_SIZE * 2 + 28,
    alignSelf: 'center',
    fontSize: 12, fontWeight: '600', color: '#8A7558',
    letterSpacing: 3.5, textTransform: 'uppercase',
    fontStyle: 'italic',
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },

  // Bottom
  bottom: {
    position: 'absolute', bottom: 50,
    alignSelf: 'center', alignItems: 'center', gap: 14,
  },
  tapeLabel: {
    backgroundColor: 'rgba(255,214,10,0.35)',
    paddingHorizontal: 16, paddingVertical: 6,
    borderRadius: 1, transform: [{ rotate: '-1.5deg' }],
  },
  tapeLabelText: {
    fontSize: 8, fontWeight: '800', color: '#4A3520', letterSpacing: 2.5,
  },
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  divLine: { height: 1.5, backgroundColor: '#C4AA78', borderRadius: 1 },
  divDot: { width: 4, height: 4, borderRadius: 2, backgroundColor: '#C4AA78' },
});
