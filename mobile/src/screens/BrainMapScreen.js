import React, { useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Dimensions, StatusBar,
  Platform, Animated, Easing, ActivityIndicator, ScrollView, Modal, FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';

import { AuthContext } from '../../App';
import { brainAPI } from '../api';
import { RuledPaperBg, MarkerUnderline, Tape, DoodleDivider } from '../components/SketchComponents';
import { FadeInView } from '../components/AnimatedComponents';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';

// ─── Visible viewport vs. internal (pannable) canvas ───
const CANVAS_PAD = 12;
const VIEW_W = SCREEN_W - CANVAS_PAD * 2;
const CANVAS_W = Math.round(VIEW_W * 1.55);
const CANVAS_H = Math.round(SCREEN_H * 0.58);

// ─── Domain metadata ─────────────────────────────────────────
const DOMAIN_META = {
  technology:            { icon: 'code-slash',   color: '#2563EB', label: 'Technology' },
  history:               { icon: 'library',      color: '#7C3AED', label: 'History' },
  nature:                { icon: 'leaf',         color: '#059669', label: 'Nature' },
  physics:               { icon: 'planet',       color: '#EA580C', label: 'Physics' },
  ai:                    { icon: 'hardware-chip',color: '#0D9488', label: 'AI' },
  ancient_civilizations: { icon: 'diamond',      color: '#92400E', label: 'Ancients' },
  space:                 { icon: 'rocket',       color: '#4F46E5', label: 'Space' },
  biology:               { icon: 'flask',        color: '#16A34A', label: 'Biology' },
  chemistry:             { icon: 'beaker',       color: '#DB2777', label: 'Chemistry' },
  mathematics:           { icon: 'calculator',   color: '#F59E0B', label: 'Math' },
  philosophy:            { icon: 'bulb',         color: '#6B7280', label: 'Philosophy' },
  engineering:           { icon: 'construct',    color: '#CA8A04', label: 'Engineering' },
};
const metaFor = (d) => DOMAIN_META[d] || { icon: 'help-circle', color: '#8A7558', label: d };

// ─── Sketch-scattered layout anchors (normalised 0..1 within canvas) ─────
// 12 positions, hand-placed so no circle ever overlaps another.
// Pattern echoes the reference mind-map: central hub + scattered satellites.
const ANCHORS = [
  { x: 0.50, y: 0.45, rank: 0 },   // CENTRE HUB (biggest)
  { x: 0.18, y: 0.22, rank: 1 },   // top-left
  { x: 0.82, y: 0.20, rank: 2 },   // top-right
  { x: 0.35, y: 0.76, rank: 3 },   // bottom-left-mid
  { x: 0.72, y: 0.78, rank: 4 },   // bottom-right-mid
  { x: 0.12, y: 0.55, rank: 5 },   // left-mid
  { x: 0.92, y: 0.52, rank: 6 },   // right-mid
  { x: 0.58, y: 0.18, rank: 7 },   // top-centre-right
  { x: 0.28, y: 0.48, rank: 8 },   // inner-left
  { x: 0.68, y: 0.50, rank: 9 },   // inner-right
  { x: 0.50, y: 0.82, rank: 10 },  // bottom-centre
  { x: 0.88, y: 0.82, rank: 11 },  // bottom-far-right
];

function assignPositions(sortedNodes) {
  return sortedNodes.map((node, i) => {
    const a = ANCHORS[i % ANCHORS.length];
    return { ...node, nx: a.x, ny: a.y, x: a.x * CANVAS_W, y: a.y * CANVAS_H };
  });
}

// ─── Decorative doodles sprinkled in the empty sketch spaces ────────────
const DOODLES = [
  { kind: 'star',   x: 0.06, y: 0.10, size: 14, color: '#059669' },
  { kind: 'star',   x: 0.46, y: 0.08, size: 16, color: '#EA580C' },
  { kind: 'star',   x: 0.94, y: 0.08, size: 12, color: '#DB2777' },
  { kind: 'star',   x: 0.06, y: 0.92, size: 12, color: '#F59E0B' },
  { kind: 'star',   x: 0.94, y: 0.92, size: 14, color: '#7C3AED' },
  { kind: 'arrowR', x: 0.24, y: 0.40, color: INK },
  { kind: 'arrowL', x: 0.78, y: 0.40, color: INK },
  { kind: 'dashes', x: 0.50, y: 0.65, w: 80, color: INK },
  { kind: 'square', x: 0.88, y: 0.35, size: 10, color: '#2563EB' },
  { kind: 'square', x: 0.14, y: 0.70, size: 8,  color: '#DB2777' },
  { kind: 'triangle', x: 0.62, y: 0.30, size: 10, color: '#EA580C' },
];

// ─── Hatched-fill circle (diagonal stripes inside) ─────────────
function HatchedFill({ size, color, stripeCount = 6, angle = -30 }) {
  const s = size - 10;
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: 5, top: 5,
        width: s, height: s,
        borderRadius: s / 2,
        overflow: 'hidden',
        backgroundColor: color + '55',
      }}
    >
      {[...Array(stripeCount)].map((_, i) => (
        <View
          key={i}
          style={{
            position: 'absolute',
            left: -s,
            top: (i * s) / stripeCount + s / (stripeCount * 2),
            width: s * 3,
            height: 1.8,
            backgroundColor: color,
            opacity: 0.55,
            transform: [{ rotate: `${angle}deg` }],
          }}
        />
      ))}
    </View>
  );
}

// ─── Doodle primitives ────────────────────────────────────────
function Doodle({ kind, x, y, size = 12, color = INK, w }) {
  const left = x * CANVAS_W;
  const top = y * CANVAS_H;

  if (kind === 'star') {
    return (
      <View style={{ position: 'absolute', left: left - size, top: top - size }} pointerEvents="none">
        {/* 5-pointed star via 2 crossed rectangles */}
        <View style={{
          position: 'absolute',
          width: size * 2, height: size * 0.5,
          backgroundColor: 'transparent',
          borderColor: color, borderWidth: 1.2,
          top: size * 0.75,
        }} />
        <View style={{
          position: 'absolute',
          width: size * 2, height: size * 0.5,
          backgroundColor: 'transparent',
          borderColor: color, borderWidth: 1.2,
          top: size * 0.75,
          transform: [{ rotate: '72deg' }],
        }} />
        <View style={{
          position: 'absolute',
          width: size * 2, height: size * 0.5,
          backgroundColor: 'transparent',
          borderColor: color, borderWidth: 1.2,
          top: size * 0.75,
          transform: [{ rotate: '-72deg' }],
        }} />
      </View>
    );
  }
  if (kind === 'arrowR' || kind === 'arrowL') {
    const rot = kind === 'arrowR' ? 0 : 180;
    return (
      <View style={{
        position: 'absolute', left: left - 14, top: top - 6,
        flexDirection: 'row', alignItems: 'center',
        transform: [{ rotate: `${rot}deg` }],
      }} pointerEvents="none">
        <View style={{ width: 24, height: 2, backgroundColor: color, borderRadius: 1 }} />
        <View style={{
          width: 0, height: 0,
          borderLeftWidth: 8, borderLeftColor: color,
          borderTopWidth: 5, borderTopColor: 'transparent',
          borderBottomWidth: 5, borderBottomColor: 'transparent',
        }} />
      </View>
    );
  }
  if (kind === 'dashes') {
    const total = 6;
    return (
      <View style={{ position: 'absolute', left: left - (w || 60) / 2, top: top - 1, flexDirection: 'row', gap: 4 }} pointerEvents="none">
        {[...Array(total)].map((_, i) => (
          <View key={i} style={{ width: 8, height: 2, backgroundColor: color, borderRadius: 1 }} />
        ))}
      </View>
    );
  }
  if (kind === 'square') {
    return (
      <View style={{
        position: 'absolute', left: left - size / 2, top: top - size / 2,
        width: size, height: size,
        borderWidth: 1.5, borderColor: color,
        transform: [{ rotate: '14deg' }],
      }} pointerEvents="none" />
    );
  }
  if (kind === 'triangle') {
    return (
      <View style={{ position: 'absolute', left: left - size, top: top - size }} pointerEvents="none">
        <View style={{
          width: 0, height: 0,
          borderLeftWidth: size, borderLeftColor: 'transparent',
          borderRightWidth: size, borderRightColor: 'transparent',
          borderBottomWidth: size * 1.6, borderBottomColor: color,
          opacity: 0.7,
        }} />
      </View>
    );
  }
  return null;
}

// ─── Edge: mix of solid and dashed ink lines ───────────────────
function Edge({ x1, y1, x2, y2, strength, dashed }) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  const weight = 1.3 + strength * 2.2;

  if (dashed) {
    const dashCount = Math.max(4, Math.floor(len / 10));
    return (
      <View
        pointerEvents="none"
        style={{
          position: 'absolute',
          left: x1, top: y1 - weight / 2,
          width: len, height: weight,
          transform: [{ rotate: `${angle}deg` }],
          transformOrigin: '0 50%',
          flexDirection: 'row', alignItems: 'center',
        }}
      >
        {[...Array(dashCount)].map((_, i) => (
          <View key={i} style={{
            width: 6, height: weight, marginRight: 4,
            backgroundColor: INK, opacity: 0.32 + strength * 0.45, borderRadius: 1,
          }} />
        ))}
      </View>
    );
  }

  return (
    <View pointerEvents="none" style={{
      position: 'absolute',
      left: x1, top: y1 - weight / 2,
      width: len, height: weight,
      backgroundColor: INK,
      borderRadius: weight / 2,
      opacity: 0.28 + strength * 0.55,
      transform: [{ rotate: `${angle}deg` }],
      transformOrigin: '0 50%',
    }} />
  );
}

// ─── Sketch node ──────────────────────────────────────────────
function Node({ node, size, delay, onPress }) {
  const meta = metaFor(node.domain);
  const scale = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(scale, {
      toValue: 1, delay, friction: 5, tension: 80, useNativeDriver: true,
    }).start();
    Animated.loop(
      Animated.timing(pulse, { toValue: 1, duration: 2400, useNativeDriver: true, easing: Easing.out(Easing.quad) })
    ).start();
  }, []);

  const pulseOp = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0] });
  const pulseSc = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.45] });

  // Slight hand-drawn tilt per node (deterministic by domain hash)
  const tilt = ((node.domain || '').charCodeAt(0) % 7 - 3) * 0.8;

  const iconSize = Math.max(16, Math.min(34, size / 2.4));
  const fontSize = Math.max(9, Math.min(12, size / 5.5));

  return (
    <Animated.View
      style={{
        position: 'absolute',
        left: node.x - size / 2,
        top: node.y - size / 2,
        width: size,
        height: size + 22,
        alignItems: 'center',
        transform: [{ scale }, { rotate: `${tilt}deg` }],
      }}
    >
      <Animated.View style={{
        position: 'absolute', top: 0, width: size, height: size, borderRadius: size / 2,
        borderWidth: 2, borderColor: meta.color,
        opacity: pulseOp, transform: [{ scale: pulseSc }],
      }} pointerEvents="none" />
      <TouchableOpacity
        activeOpacity={0.75}
        onPress={onPress}
        style={[nStyles.bubble, {
          width: size, height: size, borderRadius: size / 2,
          borderColor: meta.color,
        }]}
      >
        <HatchedFill size={size} color={meta.color} />
        <View style={{
          width: size - 16, height: size - 16, borderRadius: (size - 16) / 2,
          backgroundColor: '#FFFCF2',
          borderWidth: 1.2, borderColor: meta.color,
          justifyContent: 'center', alignItems: 'center',
        }}>
          <Ionicons name={meta.icon} size={iconSize} color={meta.color} />
        </View>
      </TouchableOpacity>
      <Text style={[nStyles.label, {
        fontSize,
        backgroundColor: '#FFFCF2', color: INK, borderColor: meta.color,
      }]} numberOfLines={1}>
        {meta.label}
      </Text>
    </Animated.View>
  );
}

const nStyles = StyleSheet.create({
  bubble: {
    borderWidth: 2.5,
    backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  label: {
    marginTop: 4,
    paddingHorizontal: 7,
    paddingVertical: 1.5,
    borderRadius: 4,
    borderWidth: 1.2,
    fontWeight: '900',
    letterSpacing: 0.5,
    textAlign: 'center',
    maxWidth: 100,
    textTransform: 'uppercase',
  },
});

// ─── Node history modal ───────────────────────────────────────
function NodeHistoryModal({ domain, visible, onClose }) {
  const meta = domain ? metaFor(domain) : null;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!visible || !domain) return;
    setLoading(true);
    setError(null);
    brainAPI.history(domain)
      .then((res) => setItems(res.data?.items || []))
      .catch((e) => {
        const s = e?.response?.status;
        if (s === 404) setItems([]);
        else setError(e?.response?.data?.detail || 'Failed to load history');
      })
      .finally(() => setLoading(false));
  }, [visible, domain]);

  if (!domain) return null;

  const ICON_BY_TYPE = {
    watch_reel:      'play-circle-outline',
    view:            'eye-outline',
    like:            'heart-outline',
    save:            'bookmark-outline',
    share:           'share-social-outline',
    comment:         'chatbubble-outline',
    read_article:    'book-outline',
    complete_quiz:   'trophy-outline',
    post_discussion: 'pencil-outline',
  };
  const LABEL_BY_TYPE = {
    watch_reel: 'Watched reel',
    view: 'Viewed',
    like: 'Liked',
    save: 'Saved',
    share: 'Shared',
    comment: 'Commented',
    read_article: 'Read article',
    complete_quiz: 'Completed quiz',
    post_discussion: 'Posted',
  };

  const fmtDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const now = Date.now();
    const diff = now - d.getTime();
    if (diff < 60_000) return 'Just now';
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <View style={modalStyles.backdrop}>
        <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={onClose} />

        <View style={[modalStyles.card, { borderColor: meta.color }]}>
          <Tape color="yellow" rotate={-4} style={{ left: 20, top: -10 }} />

          {/* Header */}
          <View style={modalStyles.header}>
            <View style={[modalStyles.iconWrap, { backgroundColor: meta.color + '22', borderColor: meta.color }]}>
              <Ionicons name={meta.icon} size={22} color={meta.color} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={modalStyles.domainName}>{meta.label}</Text>
              <Text style={modalStyles.domainSub}>Your history with this topic</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={modalStyles.closeBtn}>
              <Ionicons name="close" size={18} color={INK} />
            </TouchableOpacity>
          </View>

          <DoodleDivider style={{ marginVertical: 6 }} />

          {/* Content */}
          {loading ? (
            <View style={{ padding: 32, alignItems: 'center' }}>
              <ActivityIndicator color={INK} />
              <Text style={{ marginTop: 10, color: '#8A7558', fontStyle: 'italic' }}>Looking up your memories…</Text>
            </View>
          ) : error ? (
            <View style={{ padding: 20, alignItems: 'center' }}>
              <Ionicons name="alert-circle-outline" size={28} color="#DC2626" />
              <Text style={{ marginTop: 8, color: '#DC2626', textAlign: 'center' }}>{error}</Text>
            </View>
          ) : items.length === 0 ? (
            <View style={{ padding: 28, alignItems: 'center' }}>
              <Ionicons name="leaf-outline" size={34} color={INK} />
              <Text style={{ marginTop: 8, fontWeight: '800', color: INK }}>Nothing here yet</Text>
              <Text style={{ color: '#8A7558', marginTop: 4, textAlign: 'center' }}>
                Interact with {meta.label} content and it will show up here.
              </Text>
            </View>
          ) : (
            <FlatList
              data={items}
              keyExtractor={(it) => it.id || it.content_id || Math.random().toString()}
              style={{ maxHeight: SCREEN_H * 0.5 }}
              contentContainerStyle={{ paddingVertical: 6 }}
              renderItem={({ item }) => (
                <View style={[modalStyles.row, { borderLeftColor: meta.color }]}>
                  <View style={[modalStyles.rowIcon, { backgroundColor: meta.color + '18', borderColor: meta.color }]}>
                    <Ionicons name={ICON_BY_TYPE[item.interaction_type] || 'ellipse-outline'} size={16} color={meta.color} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={modalStyles.rowType} numberOfLines={1}>
                      {LABEL_BY_TYPE[item.interaction_type] || item.interaction_type}
                    </Text>
                    <Text style={modalStyles.rowTitle} numberOfLines={2}>{item.title}</Text>
                  </View>
                  <Text style={modalStyles.rowTime}>{fmtDate(item.at)}</Text>
                </View>
              )}
            />
          )}

          <DoodleDivider style={{ marginVertical: 4 }} />
          <View style={modalStyles.footerRow}>
            <Text style={modalStyles.footerMeta}>{items.length} interaction{items.length === 1 ? '' : 's'}</Text>
            <TouchableOpacity style={[modalStyles.doneBtn, { backgroundColor: meta.color }]} onPress={onClose}>
              <Text style={modalStyles.doneText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const modalStyles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(44,24,16,0.72)',
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    backgroundColor: '#FFFCF2',
    borderWidth: 2.5,
    borderTopLeftRadius: 4, borderTopRightRadius: 22,
    borderBottomLeftRadius: 22, borderBottomRightRadius: 4,
    padding: 16,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 12 },
    }),
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 4 },
  iconWrap: {
    width: 44, height: 44, borderRadius: 22, borderWidth: 2,
    justifyContent: 'center', alignItems: 'center',
  },
  domainName: { fontSize: 18, fontWeight: '900', color: INK, letterSpacing: -0.3 },
  domainSub: { fontSize: 11, color: '#8A7558', fontStyle: 'italic', marginTop: 2 },
  closeBtn: {
    width: 32, height: 32, borderRadius: 16,
    borderWidth: 1.5, borderColor: INK, backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
  },
  row: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    marginVertical: 4, padding: 10,
    backgroundColor: '#FFFCF2',
    borderLeftWidth: 4, borderRadius: 8,
    borderWidth: 1.2, borderColor: '#EFE4CB',
  },
  rowIcon: {
    width: 32, height: 32, borderRadius: 16,
    borderWidth: 1.2, justifyContent: 'center', alignItems: 'center',
  },
  rowType: { fontSize: 11, fontWeight: '900', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase' },
  rowTitle: { fontSize: 13, fontWeight: '700', color: INK, marginTop: 2 },
  rowTime: { fontSize: 10, color: '#8A7558', fontWeight: '700' },
  footerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
  footerMeta: { fontSize: 11, color: '#8A7558', fontStyle: 'italic' },
  doneBtn: {
    paddingHorizontal: 18, paddingVertical: 8,
    borderRadius: 14, borderWidth: 2, borderColor: INK,
  },
  doneText: { color: '#fff', fontWeight: '900', fontSize: 12, letterSpacing: 1 },
});

// ─── Screen ────────────────────────────────────────────────
export default function BrainMapScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeDomain, setActiveDomain] = useState(null);

  // Zoom — buttons + pinch gesture, clamped 0.6..2.2
  const MIN_ZOOM = 0.6;
  const MAX_ZOOM = 2.2;
  const [zoom, setZoom] = useState(1);
  const zoomAnim = useRef(new Animated.Value(1)).current;
  const pinchBaseRef = useRef(1);

  useEffect(() => {
    Animated.spring(zoomAnim, {
      toValue: zoom, friction: 7, tension: 80, useNativeDriver: true,
    }).start();
  }, [zoom]);

  const applyZoom = (z) => setZoom(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, +z.toFixed(2))));
  const zoomIn = () => applyZoom(zoom + 0.2);
  const zoomOut = () => applyZoom(zoom - 0.2);
  const resetZoom = () => applyZoom(1);

  // Pinch-to-zoom — multiplies the base zoom by the pinch scale live, commits on end
  const pinch = useMemo(
    () =>
      Gesture.Pinch()
        .onStart(() => {
          pinchBaseRef.current = zoom;
        })
        .onUpdate((e) => {
          const next = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, pinchBaseRef.current * e.scale));
          zoomAnim.setValue(next);
        })
        .onEnd((e) => {
          const next = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, pinchBaseRef.current * e.scale));
          setZoom(+next.toFixed(2));
        }),
    [zoom]
  );

  // Horizontal auto-centre
  const hScrollRef = useRef(null);
  useEffect(() => {
    const centre = (CANVAS_W - VIEW_W) / 2;
    const t = setTimeout(() => {
      hScrollRef.current?.scrollTo({ x: centre, y: 0, animated: false });
    }, 60);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await brainAPI.get();
        setData(res.data);
      } catch (e) {
        const status = e?.response?.status;
        if (status === 404 || status === 401) {
          setData({ nodes: [], edges: [], total_interactions: 0, total_posts: 0, unique_domains: 0 });
        } else {
          setError(e?.response?.data?.detail || e?.message || 'Could not load your brain map yet.');
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const { placedNodes, edges, maxWeight } = useMemo(() => {
    if (!data || !data.nodes?.length) return { placedNodes: [], edges: [], maxWeight: 0 };
    const sorted = [...data.nodes].sort((a, b) => (b.weight || 0) - (a.weight || 0));
    const placed = assignPositions(sorted);
    const mw = Math.max(...sorted.map((n) => n.weight || 0), 1);
    return { placedNodes: placed, edges: data.edges || [], maxWeight: mw };
  }, [data]);

  const nodeSize = (w, isCentral) => {
    const base = isCentral ? 72 : 46;
    const bonus = (maxWeight > 0 ? (w || 0) / maxWeight : 0) * (isCentral ? 30 : 22);
    return Math.round(base + bonus);
  };
  const topDomains = useMemo(() => (data?.nodes || []).slice(0, 3), [data]);

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
      <RuledPaperBg />

      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Brain Fingerprint</Text>
          <MarkerUnderline color={ACCENT} width={130} />
        </View>
        <View style={{ flex: 1 }} />
        <View style={s.uniqueBadge}>
          <Ionicons name="finger-print" size={12} color={INK} />
          <Text style={s.uniqueText}>UNIQUE</Text>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        <View style={s.introWrap}>
          <Text style={s.intro}>
            Every node is a topic you've explored. Bigger means deeper. Tap any circle to open your history with it.
            <Text style={{ fontWeight: '900', color: INK }}> No two maps are alike.</Text>
          </Text>
        </View>

        {/* ── Sketch canvas (pan + zoom) ── */}
        <View style={s.canvasWrap}>
          <View style={s.canvasFrame}>
            <ScrollView
              ref={hScrollRef}
              horizontal
              showsHorizontalScrollIndicator={false}
              bounces
              decelerationRate="fast"
            >
              <GestureDetector gesture={pinch}>
                <Animated.View style={[s.canvasInner, { transform: [{ scale: zoomAnim }] }]}>
                {/* Decorations (drawn behind edges and nodes) */}
                {DOODLES.map((d, i) => <Doodle key={`doo${i}`} {...d} />)}

                {/* Edges — alternate solid/dashed for sketch feel */}
                {placedNodes.length > 0 && edges.map((e, i) => {
                  const a = placedNodes.find((p) => p.domain === e.from);
                  const b = placedNodes.find((p) => p.domain === e.to);
                  if (!a || !b) return null;
                  return (
                    <Edge key={`e${i}`}
                      x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                      strength={e.strength}
                      dashed={i % 2 === 1}
                    />
                  );
                })}

                {/* Nodes */}
                {placedNodes.map((n, i) => (
                  <Node
                    key={n.domain}
                    node={n}
                    size={nodeSize(n.weight, i === 0)}
                    delay={i * 55}
                    onPress={() => setActiveDomain(n.domain)}
                  />
                ))}
                </Animated.View>
              </GestureDetector>
            </ScrollView>

            {/* Tape corners stay fixed on the frame */}
            <Tape color="yellow" rotate={-5} style={{ left: 10, top: 10 }} />
            <Tape color="pink" rotate={6} style={{ right: 10, top: 10 }} />

            {/* Zoom controls — big, visible, bottom-right */}
            <View style={s.zoomWrap}>
              <TouchableOpacity style={[s.zoomBtn, { backgroundColor: ACCENT }]} onPress={zoomIn} activeOpacity={0.7}>
                <Ionicons name="add" size={24} color={INK} />
              </TouchableOpacity>
              <View style={s.zoomBadge}>
                <Text style={s.zoomBadgeText}>{Math.round(zoom * 100)}%</Text>
              </View>
              <TouchableOpacity style={s.zoomBtn} onPress={zoomOut} activeOpacity={0.7}>
                <Ionicons name="remove" size={24} color={INK} />
              </TouchableOpacity>
              <TouchableOpacity style={s.zoomReset} onPress={resetZoom} activeOpacity={0.7}>
                <Ionicons name="contract" size={14} color={INK} />
                <Text style={s.zoomResetText}>1:1</Text>
              </TouchableOpacity>
            </View>

            {/* Pan / pinch hint */}
            <View style={s.panHint} pointerEvents="none">
              <Ionicons name="swap-horizontal" size={11} color={INK} />
              <Text style={s.panHintText}>drag · pinch · tap node</Text>
            </View>

            {/* Overlays */}
            {loading && (
              <View style={s.empty}>
                <ActivityIndicator color={INK} />
                <Text style={[s.emptyTitle, { marginTop: 8 }]}>Mapping your mind…</Text>
              </View>
            )}
            {!loading && error && (
              <View style={s.empty}>
                <Ionicons name="alert-circle-outline" size={36} color="#DC2626" />
                <Text style={[s.emptyTitle, { color: '#DC2626' }]}>Oops</Text>
                <Text style={s.emptySub}>{error}</Text>
              </View>
            )}
            {!loading && !error && placedNodes.length === 0 && (
              <View style={s.empty}>
                <Ionicons name="sparkles-outline" size={44} color={INK} />
                <Text style={s.emptyTitle}>Your map is still blank</Text>
                <Text style={s.emptySub}>Read an article, watch a reel, take a quiz — each action lights up a neuron.</Text>
              </View>
            )}
          </View>
        </View>

        {/* Stats */}
        {!loading && data && (
          <FadeInView>
            <View style={s.statsRow}>
              <View style={s.statBox}>
                <Text style={s.statNum}>{data.unique_domains || 0}</Text>
                <Text style={s.statLabel}>Domains</Text>
              </View>
              <View style={s.statBox}>
                <Text style={s.statNum}>{data.total_interactions || 0}</Text>
                <Text style={s.statLabel}>Interactions</Text>
              </View>
              <View style={s.statBox}>
                <Text style={s.statNum}>{data.total_posts || 0}</Text>
                <Text style={s.statLabel}>Posts</Text>
              </View>
            </View>
          </FadeInView>
        )}

        {topDomains.length > 0 && (
          <View style={{ marginTop: 18 }}>
            <Text style={s.sectionHeading}>Your top circles</Text>
            <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />
            {topDomains.map((n) => {
              const m = metaFor(n.domain);
              const percent = maxWeight > 0 ? Math.round((n.weight / maxWeight) * 100) : 0;
              return (
                <TouchableOpacity
                  key={n.domain}
                  style={s.topRow}
                  onPress={() => setActiveDomain(n.domain)}
                  activeOpacity={0.75}
                >
                  <View style={[s.topIcon, { backgroundColor: m.color + '20', borderColor: m.color }]}>
                    <Ionicons name={m.icon} size={18} color={m.color} />
                  </View>
                  <View style={{ flex: 1, marginHorizontal: 12 }}>
                    <Text style={s.topLabel}>{m.label}</Text>
                    <View style={s.barBg}>
                      <View style={[s.barFill, { width: `${percent}%`, backgroundColor: m.color }]} />
                    </View>
                  </View>
                  <Text style={s.topWeight}>{Math.round(n.weight)}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      <NodeHistoryModal
        domain={activeDomain}
        visible={activeDomain != null}
        onClose={() => setActiveDomain(null)}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },

  header: {
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54,
    paddingHorizontal: 16, paddingBottom: 10,
    flexDirection: 'row', alignItems: 'center', gap: 12,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 19,
    borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  uniqueBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: ACCENT, borderWidth: 1.5, borderColor: INK,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6,
  },
  uniqueText: { fontSize: 9, fontWeight: '900', color: INK, letterSpacing: 1.2 },

  introWrap: { paddingHorizontal: 22, paddingVertical: 10 },
  intro: { fontSize: 13, color: '#5A4A30', lineHeight: 19, fontStyle: 'italic' },

  canvasWrap: { paddingHorizontal: CANVAS_PAD },
  canvasFrame: {
    width: VIEW_W, height: CANVAS_H,
    backgroundColor: '#FFFCF2',
    borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18,
    borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    overflow: 'hidden',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  canvasInner: { width: CANVAS_W, height: CANVAS_H },

  zoomWrap: {
    position: 'absolute', right: 12, bottom: 46, gap: 8, alignItems: 'center',
  },
  zoomBtn: {
    width: 46, height: 46, borderRadius: 23,
    backgroundColor: '#FFFCF2', borderWidth: 2.2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  zoomBadge: {
    paddingHorizontal: 8, paddingVertical: 2,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: INK,
    borderRadius: 10,
    minWidth: 44, alignItems: 'center',
  },
  zoomBadgeText: { fontSize: 10, fontWeight: '900', color: INK, letterSpacing: 0.5 },
  zoomReset: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    paddingHorizontal: 10, paddingVertical: 6,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.8, borderColor: INK,
    borderRadius: 14,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.7, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  zoomResetText: { fontSize: 10, fontWeight: '900', color: INK, letterSpacing: 0.5 },

  panHint: {
    position: 'absolute', bottom: 8, left: 12,
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#FFFCF2', borderWidth: 1.2, borderColor: INK,
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10,
    opacity: 0.88,
  },
  panHintText: { fontSize: 9, fontWeight: '800', color: INK, letterSpacing: 0.8 },

  empty: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    justifyContent: 'center', alignItems: 'center', gap: 6, padding: 32,
  },
  emptyTitle: { fontSize: 15, fontWeight: '900', color: INK, marginTop: 4 },
  emptySub: { fontSize: 12, color: '#8A7558', textAlign: 'center', lineHeight: 18 },

  statsRow: {
    flexDirection: 'row', gap: 10,
    marginHorizontal: CANVAS_PAD + 4, marginTop: 14,
  },
  statBox: {
    flex: 1, backgroundColor: '#FFFCF2',
    borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 12,
    borderBottomLeftRadius: 12, borderBottomRightRadius: 4,
    paddingVertical: 12, alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  statNum: { fontSize: 22, fontWeight: '900', color: INK },
  statLabel: { fontSize: 10, fontWeight: '800', color: '#8A7558', letterSpacing: 1.2, marginTop: 2, textTransform: 'uppercase' },

  sectionHeading: { fontSize: 16, fontWeight: '900', color: INK, marginLeft: 20, marginBottom: 6 },
  topRow: {
    flexDirection: 'row', alignItems: 'center',
    marginHorizontal: 20, marginVertical: 6,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: '#C4AA78',
    borderRadius: 10, padding: 10,
  },
  topIcon: {
    width: 36, height: 36, borderRadius: 18, borderWidth: 1.5,
    justifyContent: 'center', alignItems: 'center',
  },
  topLabel: { fontSize: 13, fontWeight: '800', color: INK },
  barBg: { marginTop: 6, height: 6, borderRadius: 3, backgroundColor: '#EFE4CB' },
  barFill: { height: '100%', borderRadius: 3 },
  topWeight: { fontSize: 14, fontWeight: '900', color: INK, minWidth: 30, textAlign: 'right' },
});
