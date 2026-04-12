import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions, StatusBar, Platform } from 'react-native';

const { width, height } = Dimensions.get('window');
const ACCENT = '#FFD60A';
const INK = '#2C1810';
const PAPER = '#FDF6E3';

const IMAGES = [
  require('../../assets/splash1.jpg'),
  require('../../assets/splash2.jpg'),
  require('../../assets/splash3.jpg'),
  require('../../assets/splash4.jpg'),
  require('../../assets/splash5.jpg'),
];

export default function SplashScreen({ onFinish }) {
  const [currentImg, setCurrentImg] = useState(0);
  const [phase, setPhase] = useState('cover'); // cover -> open -> gallery -> done

  // Cover animation
  const coverScale = useRef(new Animated.Value(0.85)).current;
  const coverOpacity = useRef(new Animated.Value(1)).current;
  const coverRotate = useRef(new Animated.Value(0)).current;

  // Page turn effect
  const pageFlip = useRef(new Animated.Value(0)).current;

  // Title animations
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const titleSlideY = useRef(new Animated.Value(20)).current;
  const subtitleOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;

  // Image gallery
  const imgAnims = useRef(IMAGES.map(() => ({
    opacity: new Animated.Value(0),
    scale: new Animated.Value(0.3),
  }))).current;

  // Decorative elements
  const ruledLinesOpacity = useRef(new Animated.Value(0)).current;
  const spiralOpacity = useRef(new Animated.Value(0)).current;
  const ribbonSlide = useRef(new Animated.Value(-60)).current;
  const stampRotate = useRef(new Animated.Value(-20)).current;
  const stampScale = useRef(new Animated.Value(0)).current;

  // Progress
  const barWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    startSequence();
  }, []);

  const startSequence = () => {
    // Phase 1: Show notebook cover with bounce
    Animated.sequence([
      Animated.spring(coverScale, { toValue: 1, friction: 6, tension: 80, useNativeDriver: true }),
      Animated.delay(300),
    ]).start(() => {
      // Phase 2: Open the notebook — cover flips away
      setPhase('open');
      Animated.parallel([
        Animated.timing(coverOpacity, { toValue: 0, duration: 500, useNativeDriver: true }),
        Animated.timing(coverRotate, { toValue: 1, duration: 600, useNativeDriver: true }),
        // Reveal ruled lines
        Animated.timing(ruledLinesOpacity, { toValue: 1, duration: 400, useNativeDriver: true }),
        // Spiral binding slides in
        Animated.timing(spiralOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
        // Bookmark ribbon slides down
        Animated.spring(ribbonSlide, { toValue: 0, friction: 5, tension: 60, useNativeDriver: true }),
      ]).start(() => {
        // Phase 3: Title writes itself in
        Animated.stagger(150, [
          Animated.parallel([
            Animated.timing(titleOpacity, { toValue: 1, duration: 400, useNativeDriver: true }),
            Animated.spring(titleSlideY, { toValue: 0, friction: 6, tension: 80, useNativeDriver: true }),
          ]),
          Animated.timing(subtitleOpacity, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.timing(taglineOpacity, { toValue: 1, duration: 300, useNativeDriver: true }),
          // Stamp slams in
          Animated.parallel([
            Animated.spring(stampScale, { toValue: 1, friction: 4, tension: 120, useNativeDriver: true }),
            Animated.spring(stampRotate, { toValue: 0, friction: 6, tension: 80, useNativeDriver: true }),
          ]),
        ]).start(() => {
          // Done — finish splash
          Animated.timing(barWidth, { toValue: 100, duration: 400, useNativeDriver: false }).start(() => {
            setTimeout(() => onFinish(), 300);
          });
        });
      });
    });
  };

  const showImage = (idx) => {
    if (idx >= IMAGES.length) {
      // Finish
      Animated.timing(barWidth, { toValue: 100, duration: 200, useNativeDriver: false }).start(() => {
        setTimeout(() => onFinish(), 200);
      });
      return;
    }

    setCurrentImg(idx);
    const anim = imgAnims[idx];
    anim.scale.setValue(idx % 2 === 0 ? 0.4 : 1.8);
    anim.opacity.setValue(0);

    Animated.timing(barWidth, {
      toValue: ((idx + 1) / IMAGES.length) * 85,
      duration: 80,
      useNativeDriver: false,
    }).start();

    Animated.parallel([
      Animated.timing(anim.scale, { toValue: 1, duration: 120, useNativeDriver: true }),
      Animated.timing(anim.opacity, { toValue: 0.12, duration: 60, useNativeDriver: true }),
    ]).start(() => {
      setTimeout(() => {
        Animated.parallel([
          Animated.timing(anim.scale, { toValue: 2.2, duration: 120, useNativeDriver: true }),
          Animated.timing(anim.opacity, { toValue: 0, duration: 100, useNativeDriver: true }),
        ]).start();
        showImage(idx + 1);
      }, 80);
    });
  };

  const coverRotateInterp = coverRotate.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '-90deg'],
  });

  const stampRotateInterp = stampRotate.interpolate({
    inputRange: [-20, 0],
    outputRange: ['-20deg', '-4deg'],
  });

  return (
    <View style={s.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0A0A0A" />

      <View style={StyleSheet.absoluteFill}>
        {/* Dark background base */}
        <View style={s.darkBg} />

        {/* ═══ NOTEBOOK PAGE BACKGROUND ═══ */}
        <Animated.View style={[s.notebookBg, { opacity: ruledLinesOpacity }]}>
          {/* Paper texture */}
          <View style={s.paperTexture} />

          {/* Ruled lines */}
          {Array.from({ length: 30 }, (_, i) => (
            <View key={`line-${i}`} style={[s.ruledLine, { top: 80 + i * 28 }]} />
          ))}

          {/* Margin line */}
          <View style={s.marginLine} />

          {/* Three hole punches */}
          {[0.2, 0.5, 0.8].map((pos, i) => (
            <View key={`hole-${i}`} style={[s.holePunch, { top: `${pos * 100}%` }]}>
              <View style={s.holePunchInner} />
            </View>
          ))}
        </Animated.View>

        {/* ═══ SPIRAL BINDING ═══ */}
        <Animated.View style={[s.spiralCol, { opacity: spiralOpacity }]}>
          {Array.from({ length: 10 }, (_, i) => (
            <View key={`spiral-${i}`} style={s.spiralCoil}>
              <View style={s.spiralCoilInner} />
            </View>
          ))}
        </Animated.View>

        {/* ═══ BOOKMARK RIBBON ═══ */}
        <Animated.View style={[s.ribbon, { transform: [{ translateY: ribbonSlide }] }]}>
          <View style={s.ribbonBody} />
          <View style={s.ribbonVCut}>
            <View style={s.ribbonVLeft} />
            <View style={s.ribbonVRight} />
          </View>
          <View style={s.ribbonShadow} />
        </Animated.View>

        {/* Images removed */}

        {/* ═══ NOTEBOOK COVER ═══ */}
        <Animated.View style={[s.coverWrap, {
          opacity: coverOpacity,
          transform: [
            { scale: coverScale },
            { perspective: 800 },
            { rotateY: coverRotateInterp },
          ],
        }]}>
          <View style={s.cover}>
            {/* Cover texture pattern */}
            <View style={s.coverPattern}>
              {Array.from({ length: 6 }, (_, i) => (
                <View key={i} style={[s.coverStripe, { top: 30 + i * 50 }]} />
              ))}
            </View>

            {/* Cover border */}
            <View style={s.coverBorder}>
              <View style={s.coverLabel}>
                <Text style={s.coverLabelSmall}>-- est. 2024 --</Text>
                <Text style={s.coverTitle}>Scroll<Text style={s.coverTitleAccent}>U</Text></Text>
                <Text style={s.coverTitle}>Forward</Text>
                <View style={s.coverDivider} />
                <Text style={s.coverSubtitle}>JOURNAL OF CURIOSITY</Text>
              </View>
            </View>

            {/* Decorative corner marks */}
            <View style={[s.coverCorner, { top: 16, left: 16 }]} />
            <View style={[s.coverCorner, { top: 16, right: 16, transform: [{ rotate: '90deg' }] }]} />
            <View style={[s.coverCorner, { bottom: 16, left: 16, transform: [{ rotate: '-90deg' }] }]} />
            <View style={[s.coverCorner, { bottom: 16, right: 16, transform: [{ rotate: '180deg' }] }]} />
          </View>
        </Animated.View>

        {/* ═══ TITLE OVERLAY (after cover opens) ═══ */}
        <View style={s.titleOverlay} pointerEvents="none">
          <Animated.View style={{ opacity: titleOpacity, transform: [{ translateY: titleSlideY }] }}>
            <Text style={s.title}>
              Scroll<Text style={s.titleAccent}>U</Text>Forward
            </Text>
          </Animated.View>

          <Animated.Text style={[s.subtitle, { opacity: subtitleOpacity }]}>
            Where Curiosity Scales
          </Animated.Text>

          <Animated.Text style={[s.tagline, { opacity: taglineOpacity }]}>
            Your intellectual journal awaits
          </Animated.Text>

          {/* Stamp decoration */}
          <Animated.View style={[s.stampDecor, {
            transform: [{ scale: stampScale }, { rotate: stampRotateInterp }],
          }]}>
            <Text style={s.stampText}>OPEN</Text>
            <Text style={s.stampTextSmall}>YOUR MIND</Text>
          </Animated.View>
        </View>

        {/* ═══ PROGRESS BAR ═══ */}
        <Animated.View style={[s.bar, {
          width: barWidth.interpolate({
            inputRange: [0, 100],
            outputRange: ['0%', '100%'],
          }),
        }]} />

        {/* ═══ COUNTER ═══ */}
        <Text style={s.counter} />

        {/* ═══ WASHI TAPE DECORATION ═══ */}
        <Animated.View style={[s.washiTop, { opacity: ruledLinesOpacity }]}>
          <View style={s.washiTape} />
        </Animated.View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  darkBg: { ...StyleSheet.absoluteFillObject, backgroundColor: '#0A0A0A' },

  // ─── Notebook page background ───
  notebookBg: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: PAPER,
  },
  paperTexture: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(200,180,140,0.04)',
  },
  ruledLine: {
    position: 'absolute', left: 0, right: 0,
    height: 1, backgroundColor: 'rgba(90,150,210,0.15)',
  },
  marginLine: {
    position: 'absolute', left: 48, top: 0, bottom: 0,
    width: 1.5, backgroundColor: 'rgba(200,55,55,0.18)',
  },
  holePunch: {
    position: 'absolute', left: 14,
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: '#E6D5B8', borderWidth: 2,
    borderColor: '#C4AA78', justifyContent: 'center', alignItems: 'center',
    zIndex: 2,
  },
  holePunchInner: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: '#D4C4A0', borderWidth: 1, borderColor: '#B8A680',
  },

  // ─── Spiral binding ───
  spiralCol: {
    position: 'absolute', left: 6, top: 40, bottom: 40,
    width: 28, justifyContent: 'space-evenly', zIndex: 6,
  },
  spiralCoil: {
    width: 22, height: 22, borderRadius: 11,
    backgroundColor: '#C4AA78', borderWidth: 2.5,
    borderColor: '#A08E68', justifyContent: 'center', alignItems: 'center',
  },
  spiralCoilInner: {
    width: 10, height: 10, borderRadius: 5,
    backgroundColor: PAPER, borderWidth: 1.5, borderColor: '#C4AA78',
  },

  // ─── Bookmark ribbon ───
  ribbon: {
    position: 'absolute', right: 36, top: -4, zIndex: 8,
    alignItems: 'center',
  },
  ribbonBody: {
    width: 22, height: 70,
    backgroundColor: '#DC2626',
  },
  ribbonVCut: { flexDirection: 'row' },
  ribbonVLeft: {
    width: 0, height: 0,
    borderLeftWidth: 11, borderRightWidth: 0, borderBottomWidth: 10,
    borderLeftColor: '#DC2626', borderRightColor: 'transparent', borderBottomColor: 'transparent',
  },
  ribbonVRight: {
    width: 0, height: 0,
    borderLeftWidth: 0, borderRightWidth: 11, borderBottomWidth: 10,
    borderLeftColor: 'transparent', borderRightColor: '#DC2626', borderBottomColor: 'transparent',
  },
  ribbonShadow: {
    position: 'absolute', right: 0, top: 0, bottom: 10,
    width: 3, backgroundColor: 'rgba(0,0,0,0.15)',
  },

  // ─── Splash images ───
  fullImg: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    width: '100%', height: '100%',
  },

  // ─── Notebook cover ───
  coverWrap: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center', alignItems: 'center', zIndex: 20,
  },
  cover: {
    width: width * 0.82, height: height * 0.55,
    backgroundColor: '#2C1810',
    borderRadius: 8,
    borderWidth: 3, borderColor: '#1A0E08',
    overflow: 'hidden',
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 6, height: 8 }, shadowOpacity: 0.6, shadowRadius: 12 },
      android: { elevation: 20 },
    }),
  },
  coverPattern: { ...StyleSheet.absoluteFillObject, opacity: 0.08 },
  coverStripe: {
    position: 'absolute', left: 0, right: 0,
    height: 2, backgroundColor: ACCENT,
  },
  coverBorder: {
    flex: 1, margin: 14,
    borderWidth: 2, borderColor: 'rgba(255,214,10,0.25)',
    borderRadius: 4,
    justifyContent: 'center', alignItems: 'center',
  },
  coverLabel: { alignItems: 'center', paddingHorizontal: 24 },
  coverLabelSmall: {
    fontSize: 10, fontWeight: '700', color: 'rgba(255,214,10,0.5)',
    letterSpacing: 4, textTransform: 'uppercase', marginBottom: 12,
  },
  coverTitle: {
    fontSize: 42, fontWeight: '900', color: '#FFFFFF',
    letterSpacing: -2, lineHeight: 48,
    textShadowColor: 'rgba(255,214,10,0.3)', textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 20,
  },
  coverTitleAccent: { color: ACCENT },
  coverDivider: {
    width: 60, height: 3, backgroundColor: ACCENT,
    borderRadius: 2, marginVertical: 16, opacity: 0.7,
  },
  coverSubtitle: {
    fontSize: 11, fontWeight: '800', color: 'rgba(255,255,255,0.55)',
    letterSpacing: 5, textTransform: 'uppercase',
  },
  coverCorner: {
    position: 'absolute',
    width: 16, height: 16,
    borderLeftWidth: 2, borderTopWidth: 2,
    borderColor: 'rgba(255,214,10,0.3)',
  },

  // ─── Title overlay ───
  titleOverlay: {
    position: 'absolute', top: 0, right: 0, bottom: 0, left: 0,
    zIndex: 50,
    justifyContent: 'center', alignItems: 'center',
  },
  title: {
    fontSize: 52, fontWeight: '900', color: INK,
    letterSpacing: -2,
    textShadowColor: 'rgba(255,214,10,0.15)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 30,
  },
  titleAccent: { color: ACCENT },
  subtitle: {
    fontSize: 15, fontWeight: '700', color: '#8A7558',
    marginTop: 8, letterSpacing: 4, textTransform: 'uppercase',
  },
  tagline: {
    fontSize: 13, fontWeight: '400', fontStyle: 'italic', color: '#A08E68',
    marginTop: 6, letterSpacing: 0.5,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },
  stampDecor: {
    marginTop: 24,
    borderWidth: 3, borderColor: '#DC2626',
    borderRadius: 4, paddingHorizontal: 16, paddingVertical: 8,
    opacity: 0.6,
  },
  stampText: {
    fontSize: 16, fontWeight: '900', color: '#DC2626',
    letterSpacing: 6, textAlign: 'center',
  },
  stampTextSmall: {
    fontSize: 8, fontWeight: '800', color: '#DC2626',
    letterSpacing: 3, textAlign: 'center', marginTop: 2,
  },

  // ─── Progress bar ───
  bar: {
    position: 'absolute', bottom: 0, left: 0,
    height: 4, backgroundColor: ACCENT, zIndex: 100,
    borderTopRightRadius: 2,
  },
  counter: {
    position: 'absolute', top: 20, right: 20,
    fontSize: 12, fontWeight: '700', color: '#A08E68',
    letterSpacing: 2, zIndex: 100,
  },

  // ─── Washi tape decoration ───
  washiTop: {
    position: 'absolute', top: 50, left: width * 0.1,
    zIndex: 7, transform: [{ rotate: '-5deg' }],
  },
  washiTape: {
    width: 70, height: 18,
    backgroundColor: 'rgba(255,214,10,0.45)',
    borderRadius: 1,
  },
});
