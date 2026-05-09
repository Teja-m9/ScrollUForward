import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  StatusBar, Platform, Dimensions, Animated, Easing,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { FadeInView } from '../components/AnimatedComponents';
import { AnimatedCounter } from '../components/PremiumAnimations';
import { DoodleDivider, MarkerUnderline } from '../components/SketchComponents';

const { width } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

const DOMAINS = [
  { id: 'physics', icon: 'planet', color: '#EA580C', label: 'Physics' },
  { id: 'ai', icon: 'hardware-chip', color: '#0D9488', label: 'A.I.' },
  { id: 'space', icon: 'rocket', color: '#4F46E5', label: 'Space' },
  { id: 'biology', icon: 'flask', color: '#059669', label: 'Biology' },
  { id: 'history', icon: 'library', color: '#7C3AED', label: 'History' },
  { id: 'technology', icon: 'code-slash', color: '#2563EB', label: 'Tech' },
  { id: 'nature', icon: 'leaf', color: '#10B981', label: 'Nature' },
  { id: 'mathematics', icon: 'calculator', color: '#EC4899', label: 'Math' },
];

export default function KnowledgeGraphScreen({ navigation }) {
  const [stats, setStats] = useState({});
  const [selected, setSelected] = useState(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadStats();
    // Pulse animation for central node
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 1500, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1500, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const loadStats = async () => {
    try {
      const qHist = await AsyncStorage.getItem('quiz_history');
      const history = qHist ? JSON.parse(qHist) : [];
      const domainStats = {};
      DOMAINS.forEach(d => { domainStats[d.id] = { quizzes: 0, avgScore: 0, iqEarned: 0, level: 0 }; });
      history.forEach(h => {
        if (domainStats[h.domain]) {
          const s = domainStats[h.domain];
          s.quizzes += 1;
          s.avgScore = Math.round(((s.avgScore * (s.quizzes - 1)) + h.accuracy) / s.quizzes);
          s.iqEarned += h.iqEarned || 0;
        }
      });
      // Calculate level (1-5) from engagement
      Object.keys(domainStats).forEach(d => {
        const s = domainStats[d];
        const pts = s.quizzes * 10 + (s.avgScore * 0.5);
        s.level = Math.min(5, Math.max(0, Math.floor(pts / 15)));
      });
      setStats(domainStats);
    } catch {}
  };

  // Position domains in a circular layout
  const graphSize = width - 40;
  const centerX = graphSize / 2;
  const centerY = graphSize / 2;
  const radius = graphSize / 2 - 45;

  const nodes = DOMAINS.map((d, i) => {
    const angle = (i / DOMAINS.length) * 2 * Math.PI - Math.PI / 2;
    return {
      ...d,
      x: centerX + Math.cos(angle) * radius - 32,
      y: centerY + Math.sin(angle) * radius - 32,
      stats: stats[d.id] || { quizzes: 0, level: 0, avgScore: 0, iqEarned: 0 },
    };
  });

  const totalQuizzes = Object.values(stats).reduce((a, s) => a + (s.quizzes || 0), 0);
  const totalIQ = Object.values(stats).reduce((a, s) => a + (s.iqEarned || 0), 0);
  const masteredCount = Object.values(stats).filter(s => s.level >= 4).length;

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      <View style={s.ruledBg} pointerEvents="none">
        {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
        <View style={s.margin} />
      </View>

      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>Knowledge Graph</Text>
          <Text style={s.subtitle}>Your learning universe</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
        {/* Stats strip */}
        <FadeInView>
          <View style={s.statsStrip}>
            <View style={s.statItem}>
              <AnimatedCounter value={totalQuizzes} style={s.statNum} />
              <Text style={s.statLabel}>Quizzes</Text>
            </View>
            <View style={s.divider} />
            <View style={s.statItem}>
              <AnimatedCounter value={totalIQ} style={s.statNum} />
              <Text style={s.statLabel}>IQ Earned</Text>
            </View>
            <View style={s.divider} />
            <View style={s.statItem}>
              <AnimatedCounter value={masteredCount} style={s.statNum} />
              <Text style={s.statLabel}>Mastered</Text>
            </View>
          </View>
        </FadeInView>

        <MarkerUnderline color={ACCENT} width={100} style={{ alignSelf: 'center', marginVertical: 14 }} />

        {/* Graph visualization */}
        <FadeInView delay={150}>
          <View style={{ width: graphSize, height: graphSize, alignSelf: 'center', marginBottom: 20 }}>
            {/* Connection lines from center to each node */}
            {nodes.map((n, i) => {
              const dx = n.x + 32 - centerX;
              const dy = n.y + 32 - centerY;
              const len = Math.sqrt(dx * dx + dy * dy);
              const angle = Math.atan2(dy, dx) * 180 / Math.PI;
              const isActive = (stats[n.id]?.quizzes || 0) > 0;
              return (
                <View key={`line-${i}`} style={{
                  position: 'absolute', left: centerX, top: centerY - 1.5,
                  width: len, height: 2,
                  backgroundColor: isActive ? n.color + '60' : '#C4AA78',
                  opacity: isActive ? 0.8 : 0.3,
                  transform: [{ translateX: 0 }, { rotate: `${angle}deg` }],
                  transformOrigin: 'left center',
                }} />
              );
            })}

            {/* Central You node */}
            <Animated.View style={[s.centerNode, {
              left: centerX - 40, top: centerY - 40,
              transform: [{ scale: pulseAnim }],
            }]}>
              <View style={s.centerInner}>
                <Ionicons name="person" size={28} color={INK} />
              </View>
              <Text style={s.centerLabel}>YOU</Text>
            </Animated.View>

            {/* Domain nodes */}
            {nodes.map((n, i) => {
              const nodeStats = stats[n.id] || { level: 0, quizzes: 0 };
              const isActive = nodeStats.quizzes > 0;
              const size = 64 + (nodeStats.level * 3);
              return (
                <TouchableOpacity
                  key={n.id}
                  style={[s.domainNode, {
                    left: n.x - (size - 64) / 2,
                    top: n.y - (size - 64) / 2,
                    width: size, height: size,
                    borderRadius: size / 2,
                    backgroundColor: isActive ? n.color : '#F3EACD',
                    borderColor: isActive ? INK : '#C4AA78',
                    opacity: isActive ? 1 : 0.5,
                  }]}
                  onPress={() => setSelected(selected?.id === n.id ? null : { ...n, stats: nodeStats })}
                >
                  <Ionicons name={n.icon} size={isActive ? 26 : 22} color={isActive ? '#fff' : n.color} />
                  {nodeStats.level > 0 && (
                    <View style={[s.levelBadge, { backgroundColor: ACCENT }]}>
                      <Text style={s.levelText}>{nodeStats.level}</Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </FadeInView>

        {/* Legend */}
        <View style={s.legend}>
          <View style={s.legendItem}>
            <View style={[s.legendDot, { backgroundColor: ACCENT }]} />
            <Text style={s.legendText}>Level shown on each node</Text>
          </View>
          <View style={s.legendItem}>
            <View style={[s.legendDot, { backgroundColor: '#F3EACD', borderWidth: 1.5, borderColor: '#C4AA78' }]} />
            <Text style={s.legendText}>Unexplored domain</Text>
          </View>
        </View>

        {/* Selected node details */}
        {selected && (
          <FadeInView>
            <View style={[s.detailCard, { borderLeftColor: selected.color }]}>
              <View style={s.detailHeader}>
                <View style={[s.detailIcon, { backgroundColor: selected.color + '20' }]}>
                  <Ionicons name={selected.icon} size={22} color={selected.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.detailTitle}>{selected.label}</Text>
                  <View style={s.levelBar}>
                    {[1, 2, 3, 4, 5].map(l => (
                      <View key={l} style={[s.levelSegment, l <= selected.stats.level && { backgroundColor: selected.color }]} />
                    ))}
                  </View>
                </View>
                <TouchableOpacity onPress={() => setSelected(null)}>
                  <Ionicons name="close" size={20} color="#8A7558" />
                </TouchableOpacity>
              </View>
              <DoodleDivider style={{ marginVertical: 10 }} />
              <View style={s.detailStats}>
                <View style={s.detailStat}>
                  <Text style={[s.detailNum, { color: selected.color }]}>{selected.stats.quizzes}</Text>
                  <Text style={s.detailLabel}>Quizzes</Text>
                </View>
                <View style={s.detailStat}>
                  <Text style={[s.detailNum, { color: selected.color }]}>{selected.stats.avgScore}%</Text>
                  <Text style={s.detailLabel}>Avg Score</Text>
                </View>
                <View style={s.detailStat}>
                  <Text style={[s.detailNum, { color: selected.color }]}>+{selected.stats.iqEarned}</Text>
                  <Text style={s.detailLabel}>IQ Earned</Text>
                </View>
              </View>
              <TouchableOpacity
                style={[s.studyBtn, { backgroundColor: selected.color }]}
                onPress={() => { setSelected(null); navigation.navigate('Quiz', { domain: selected.id }); }}
              >
                <Ionicons name="bulb" size={16} color="#fff" />
                <Text style={s.studyBtnText}>Study {selected.label}</Text>
              </TouchableOpacity>
            </View>
          </FadeInView>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },
  ruledBg: { ...StyleSheet.absoluteFillObject },
  ruled: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.06)' },
  margin: { position: 'absolute', left: 44, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)' },

  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 52, paddingBottom: 14 },
  backBtn: { width: 36, height: 36, borderRadius: 18, borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  subtitle: { fontSize: 12, color: '#8A7558', fontStyle: 'italic' },

  scroll: { paddingHorizontal: 16 },
  statsStrip: { flexDirection: 'row', backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK, borderRadius: 12, paddingVertical: 14, marginBottom: 8,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  statItem: { flex: 1, alignItems: 'center' },
  statNum: { fontSize: 22, fontWeight: '900', color: INK },
  statLabel: { fontSize: 10, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase', marginTop: 2 },
  divider: { width: 1, backgroundColor: '#E6D5B8', marginVertical: 8 },

  centerNode: { position: 'absolute', width: 80, height: 80, alignItems: 'center' },
  centerInner: { width: 80, height: 80, borderRadius: 40, backgroundColor: ACCENT, borderWidth: 3, borderColor: INK, justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },
  centerLabel: { position: 'absolute', bottom: -20, fontSize: 10, fontWeight: '900', color: INK, letterSpacing: 2 },

  domainNode: { position: 'absolute', justifyContent: 'center', alignItems: 'center', borderWidth: 2.5, overflow: 'visible',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  levelBadge: { position: 'absolute', top: -4, right: -4, width: 20, height: 20, borderRadius: 10, borderWidth: 1.5, borderColor: INK, justifyContent: 'center', alignItems: 'center' },
  levelText: { fontSize: 11, fontWeight: '900', color: INK },

  legend: { flexDirection: 'row', justifyContent: 'center', gap: 20, marginBottom: 16, flexWrap: 'wrap' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 12, height: 12, borderRadius: 6 },
  legendText: { fontSize: 11, color: '#8A7558' },

  detailCard: { backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK, borderLeftWidth: 5, borderRadius: 12, padding: 16, marginBottom: 16 },
  detailHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  detailIcon: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  detailTitle: { fontSize: 18, fontWeight: '900', color: INK },
  levelBar: { flexDirection: 'row', gap: 3, marginTop: 4 },
  levelSegment: { flex: 1, height: 4, borderRadius: 2, backgroundColor: '#E6D5B8' },

  detailStats: { flexDirection: 'row', marginVertical: 10 },
  detailStat: { flex: 1, alignItems: 'center' },
  detailNum: { fontSize: 22, fontWeight: '900' },
  detailLabel: { fontSize: 10, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase', marginTop: 2 },

  studyBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 12, borderRadius: 10, borderWidth: 2, borderColor: INK, marginTop: 8 },
  studyBtnText: { fontSize: 14, fontWeight: '800', color: '#fff' },
});
