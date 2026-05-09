import React, { useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  StatusBar, Platform, Animated, Easing, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { AuthContext } from '../../App';
import { mapAPI } from '../api';
import {
  RuledPaperBg, MarkerUnderline, Tape, DoodleDivider,
} from '../components/SketchComponents';
import { FadeInView } from '../components/AnimatedComponents';
import { AnimatedCounter } from '../components/PremiumAnimations';
import NotebookWorldMap from '../components/NotebookWorldMap';

const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

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
const metaFor = (d) => DOMAIN_META[d] || { icon: 'globe-outline', color: '#8A7558', label: d || 'Topic' };

export default function LiveMapScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const mapRef = useRef(null);
  const [data, setData] = useState({ live_users: [], trending_domains: [], active_count: 0, total_interactions_24h: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pulse = useRef(new Animated.Value(0)).current;

  // Pulse animation for the LIVE dot
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 900, useNativeDriver: true, easing: Easing.out(Easing.quad) }),
        Animated.timing(pulse, { toValue: 0, duration: 900, useNativeDriver: true, easing: Easing.in(Easing.quad) }),
      ])
    ).start();
  }, []);

  // Poll trending data every 15s
  const fetchTrending = async () => {
    try {
      const res = await mapAPI.trending();
      setData(res.data || { live_users: [], trending_domains: [], active_count: 0 });
      setError(null);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 404 || status === 401) {
        setData({ live_users: [], trending_domains: [], active_count: 0, total_interactions_24h: 0 });
      } else {
        setError(e?.response?.data?.detail || e?.message || 'Could not load live map');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrending();
    const t = setInterval(fetchTrending, 15_000);
    return () => clearInterval(t);
  }, []);

  // Choose a representative user position to centre the map on (first user)
  const initialMe = useMemo(() => {
    const first = data.live_users?.[0];
    if (first) return { lat: first.latitude, lng: first.longitude, name: 'Live' };
    return null;
  }, [data]);

  // Convert live users to "others" pin format the map expects, colored by their top domain
  const liveOthers = useMemo(() => {
    return (data.live_users || []).map((u, i) => {
      const meta = metaFor(u.top_domain);
      return {
        user_id: u.user_id,
        username: u.username,
        display_name: u.top_domain ? `${u.display_name || u.username} · ${meta.label}` : (u.display_name || u.username),
        latitude: u.latitude,
        longitude: u.longitude,
      };
    });
  }, [data]);

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      {/* Real-world notebook map fills the full screen */}
      <NotebookWorldMap
        ref={mapRef}
        me={initialMe}
        others={liveOthers}
        routeTo={null}
      />

      {/* Loading / error overlay */}
      {loading && (
        <View style={s.overlay}>
          <ActivityIndicator color={INK} size="large" />
          <Text style={s.overlayText}>Tuning into the world…</Text>
        </View>
      )}
      {!loading && error && (
        <View style={s.overlay}>
          <Ionicons name="alert-circle-outline" size={36} color="#DC2626" />
          <Text style={[s.overlayText, { color: '#DC2626' }]}>{error}</Text>
        </View>
      )}

      {/* Header strip */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Live World</Text>
          <MarkerUnderline color={ACCENT} width={84} />
        </View>
        <View style={{ flex: 1 }} />
        <Animated.View style={[s.livePill, { transform: [{ scale: pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.08] }) }] }]}>
          <View style={s.liveDot} />
          <Text style={s.liveText}>LIVE</Text>
        </Animated.View>
      </View>

      {/* Stat strip — what's happening RIGHT NOW */}
      <View style={s.statStrip}>
        <Tape color="yellow" rotate={-3} style={{ left: 16, top: -8 }} />
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={s.statBox}>
            <AnimatedCounter value={data.active_count || 0} style={s.statNum} />
            <Text style={s.statLabel}>ACTIVE</Text>
          </View>
          <View style={s.divider} />
          <View style={s.statBox}>
            <AnimatedCounter value={data.total_interactions_24h || 0} style={s.statNum} />
            <Text style={s.statLabel}>24H BUZZ</Text>
          </View>
          <View style={s.divider} />
          <View style={s.statBox}>
            <AnimatedCounter value={(data.trending_domains || []).length} style={s.statNum} />
            <Text style={s.statLabel}>TOPICS</Text>
          </View>
        </View>
      </View>

      {/* Trending bottom sheet */}
      <View style={s.sheet}>
        <Tape color="pink" rotate={2} style={{ left: '50%', marginLeft: -32, top: -10 }} width={62} />
        <View style={s.sheetHandle} />
        <View style={s.sheetHeader}>
          <Ionicons name="trending-up" size={16} color={INK} />
          <Text style={s.sheetTitle}>Trending right now</Text>
          <TouchableOpacity onPress={fetchTrending} style={s.refreshBtn}>
            <Ionicons name="refresh" size={14} color={INK} />
          </TouchableOpacity>
        </View>
        <DoodleDivider style={{ marginVertical: 4 }} />
        {(data.trending_domains || []).length === 0 ? (
          <View style={{ paddingVertical: 18, alignItems: 'center' }}>
            <Text style={{ color: '#8A7558', fontStyle: 'italic', fontSize: 12 }}>
              The world's quiet right now — be the first to spark a topic.
            </Text>
          </View>
        ) : (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8, paddingVertical: 6, paddingHorizontal: 4 }}
          >
            {(data.trending_domains || []).map((d, i) => {
              const m = metaFor(d.domain);
              return (
                <FadeInView key={d.domain} delay={i * 40}>
                  <View style={[s.trendChip, { borderColor: m.color, backgroundColor: m.color + '18' }]}>
                    <View style={[s.trendIcon, { backgroundColor: m.color + '30', borderColor: m.color }]}>
                      <Ionicons name={m.icon} size={14} color={m.color} />
                    </View>
                    <View>
                      <Text style={[s.trendLabel, { color: m.color }]} numberOfLines={1}>{m.label}</Text>
                      <Text style={s.trendCount}>{d.count} hits</Text>
                    </View>
                  </View>
                </FadeInView>
              );
            })}
          </ScrollView>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },

  header: {
    position: 'absolute',
    top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54,
    left: 0, right: 0,
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingHorizontal: 16,
    zIndex: 50,
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
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5, fontFamily: SERIF },
  livePill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 10, paddingVertical: 4,
    backgroundColor: '#FFFCF2', borderRadius: 12, borderWidth: 1.5, borderColor: '#DC2626',
  },
  liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#DC2626' },
  liveText: { fontSize: 10, fontWeight: '900', color: '#DC2626', letterSpacing: 1 },

  statStrip: {
    position: 'absolute',
    top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 60 : 110,
    left: 16, right: 16,
    backgroundColor: '#FFFCF2',
    borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 16, borderBottomLeftRadius: 16, borderBottomRightRadius: 4,
    paddingVertical: 10, paddingHorizontal: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 3 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
    zIndex: 40,
  },
  statBox: { alignItems: 'center', minWidth: 70 },
  statNum: { fontSize: 18, fontWeight: '900', color: INK, fontFamily: SERIF },
  statLabel: { fontSize: 9, fontWeight: '900', color: '#8A7558', letterSpacing: 1.2, marginTop: 2 },
  divider: { width: 1, height: 28, backgroundColor: '#C4AA78', marginHorizontal: 6 },

  sheet: {
    position: 'absolute',
    bottom: 14, left: 12, right: 12,
    backgroundColor: '#FFFCF2',
    borderWidth: 2.5, borderColor: INK,
    borderTopLeftRadius: 6, borderTopRightRadius: 22,
    borderBottomLeftRadius: 22, borderBottomRightRadius: 6,
    paddingVertical: 10, paddingHorizontal: 12,
    zIndex: 100,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 24 },
    }),
  },
  sheetHandle: {
    alignSelf: 'center', width: 38, height: 4, borderRadius: 2,
    backgroundColor: '#C4AA78', marginBottom: 8,
  },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sheetTitle: { flex: 1, fontSize: 13, fontWeight: '900', color: INK, letterSpacing: 0.5 },
  refreshBtn: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: ACCENT, borderWidth: 1.5, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
  },

  trendChip: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: 12, borderWidth: 1.5,
  },
  trendIcon: {
    width: 26, height: 26, borderRadius: 13, borderWidth: 1.5,
    justifyContent: 'center', alignItems: 'center',
  },
  trendLabel: { fontSize: 12, fontWeight: '900', maxWidth: 110 },
  trendCount: { fontSize: 9, fontWeight: '700', color: '#8A7558', marginTop: 1 },

  overlay: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(253,246,227,0.78)',
    justifyContent: 'center', alignItems: 'center', gap: 12, zIndex: 60,
  },
  overlayText: { fontSize: 13, color: INK, fontWeight: '700' },
});
