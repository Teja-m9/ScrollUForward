import React, { useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Dimensions, StatusBar,
  Platform, ActivityIndicator, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';

import { AuthContext } from '../../App';
import { mapAPI } from '../api';
import { Tape, MarkerUnderline } from '../components/SketchComponents';
import NotebookWorldMap from '../components/NotebookWorldMap';

const { height: SCREEN_H } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const RED = '#DC2626';

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export default function MapScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const [myLoc, setMyLoc] = useState(null);
  const [nearby, setNearby] = useState([]);
  const [loading, setLoading] = useState(true);
  const [permError, setPermError] = useState(null);
  const mapRef = useRef(null);
  const watchRef = useRef(null);
  const pollRef = useRef(null);

  // ─── Location permission + watch ───
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          setPermError('Location permission denied');
          setLoading(false);
          return;
        }
        const initial = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
        if (cancelled) return;
        const p = { lat: initial.coords.latitude, lng: initial.coords.longitude };
        setMyLoc(p);
        setLoading(false);
        mapAPI.updateLocation({ latitude: p.lat, longitude: p.lng }).catch(() => {});
        fetchNearby();
        watchRef.current = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.Balanced, distanceInterval: 10, timeInterval: 15_000 },
          (loc) => {
            const np = { lat: loc.coords.latitude, lng: loc.coords.longitude };
            setMyLoc(np);
            mapAPI.updateLocation({ latitude: np.lat, longitude: np.lng }).catch(() => {});
          }
        );
      } catch (e) {
        setPermError(e?.message || 'Failed to get location');
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      watchRef.current?.remove?.();
      mapAPI.clearLocation().catch(() => {});
    };
  }, []);

  const fetchNearby = async () => {
    try {
      const res = await mapAPI.nearby();
      setNearby(res.data || []);
    } catch {}
  };

  useEffect(() => {
    pollRef.current = setInterval(fetchNearby, 10_000);
    return () => clearInterval(pollRef.current);
  }, []);

  // ─── Enrich friends with haversine distance + prep for map ───
  const friends = useMemo(() => {
    if (!myLoc) return [];
    return nearby
      .filter(u => !u.is_me)
      .map(u => ({ ...u, km: haversineKm(myLoc.lat, myLoc.lng, u.latitude, u.longitude) }))
      .sort((a, b) => a.km - b.km);
  }, [myLoc, nearby]);

  const closest = friends.length ? friends[0] : null;

  const meForMap = useMemo(
    () => (myLoc ? {
      lat: myLoc.lat,
      lng: myLoc.lng,
      name: user?.display_name || user?.username || 'You',
    } : null),
    [myLoc, user]
  );

  const routeTo = closest ? { lat: closest.latitude, lng: closest.longitude } : null;

  // ─── UI ─────────────────────────────────────────────
  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      {/* ── Real-world notebook-styled map ── */}
      <NotebookWorldMap
        ref={mapRef}
        me={meForMap}
        others={friends}
        routeTo={routeTo}
      />

      {/* ── Loading / error overlay ── */}
      {loading && (
        <View style={s.overlay}>
          <ActivityIndicator color={INK} size="large" />
          <Text style={s.overlayText}>Locating you…</Text>
        </View>
      )}
      {permError && (
        <View style={s.overlay}>
          <Ionicons name="location-outline" size={40} color={RED} />
          <Text style={[s.overlayText, { color: RED }]}>{permError}</Text>
          <TouchableOpacity style={s.retryBtn} onPress={() => navigation.replace('Map')}>
            <Text style={s.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ── Top header strip ── */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Friends Map</Text>
          <MarkerUnderline color={ACCENT} width={96} />
        </View>
        <View style={{ flex: 1 }} />
        <View style={s.livePill}>
          <View style={s.liveDot} />
          <Text style={s.liveText}>LIVE</Text>
        </View>
      </View>

      {/* ── Top turn-by-turn card (like the reference) ── */}
      <View style={s.topCard}>
        <Tape color="yellow" rotate={-4} style={{ left: 14, top: -6 }} />
        <View style={s.topCardInner}>
          <View style={{ flex: 1 }}>
            <Text style={s.topDistance}>
              {closest ? (closest.km < 1 ? `${Math.round(closest.km * 1000)} m` : `${closest.km.toFixed(1)} km`) : '—'}
            </Text>
            <Text style={s.topDirection} numberOfLines={1}>
              {closest ? `Head toward ${closest.display_name || closest.username}` : 'Waiting for friends…'}
            </Text>
          </View>
          <View style={s.turnIcon}>
            <Ionicons name="navigate" size={22} color="#fff" />
          </View>
        </View>
      </View>

      {/* ── Right floating controls ── */}
      <View style={s.floatingControls}>
        <TouchableOpacity
          style={s.fab}
          onPress={() => myLoc && mapRef.current?.recenter(myLoc.lat, myLoc.lng, 15)}
        >
          <Ionicons name="locate" size={18} color={INK} />
        </TouchableOpacity>
        <View style={{ height: 10 }} />
        <TouchableOpacity style={[s.fab, { backgroundColor: ACCENT }]} onPress={fetchNearby}>
          <Ionicons name="refresh" size={18} color={INK} />
        </TouchableOpacity>
        <View style={{ height: 10 }} />
        <TouchableOpacity
          style={[s.fab, { backgroundColor: RED }]}
          onPress={() => {
            if (closest) {
              mapRef.current?.recenter(closest.latitude, closest.longitude, 15);
            } else if (myLoc) {
              Alert.alert('Your location', `${myLoc.lat.toFixed(5)}, ${myLoc.lng.toFixed(5)}`);
            }
          }}
        >
          <Ionicons name="flag" size={18} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* ── Bottom destination card ── */}
      <View style={s.bottomCardWrap}>
        <View style={s.bottomCard}>
          <Tape color="pink" rotate={2} style={{ left: '50%', marginLeft: -32, top: -8 }} width={62} />
          <View style={s.bottomCardInner}>
            <View style={s.bottomAvatar}>
              <Ionicons name={friends.length ? 'people' : 'person-outline'} size={22} color={INK} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.bottomTitle}>
                {friends.length ? `${friends.length} friend${friends.length > 1 ? 's' : ''} nearby` : 'No friends on the map yet'}
              </Text>
              <Text style={s.bottomSub}>
                {closest
                  ? `Closest: ${closest.display_name || closest.username} · ${closest.km < 1 ? `${Math.round(closest.km * 1000)}m` : `${closest.km.toFixed(1)}km`} away`
                  : 'Drag & pinch to explore · Invite friends to share live location'}
              </Text>
            </View>
            <TouchableOpacity style={s.endBtn} onPress={() => navigation.goBack()}>
              <Text style={s.endBtnText}>End</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },

  header: {
    position: 'absolute',
    top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54,
    left: 0, right: 0, flexDirection: 'row', alignItems: 'center', gap: 12,
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
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  livePill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 10, paddingVertical: 4, backgroundColor: '#FFFCF2',
    borderRadius: 12, borderWidth: 1.5, borderColor: RED,
  },
  liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: RED },
  liveText: { fontSize: 10, fontWeight: '900', color: RED, letterSpacing: 1 },

  topCard: {
    position: 'absolute',
    top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 58 : 104,
    left: 16, right: 16,
    backgroundColor: '#FFFCF2',
    borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 16, borderBottomLeftRadius: 16, borderBottomRightRadius: 4,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
    zIndex: 40,
  },
  topCardInner: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingHorizontal: 14, paddingVertical: 12,
  },
  topDistance: { fontSize: 24, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  topDirection: { fontSize: 12, color: '#8A7558', fontStyle: 'italic' },
  turnIcon: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: BLUE,
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 2, borderColor: INK,
  },

  floatingControls: {
    position: 'absolute', right: 14, top: SCREEN_H * 0.42, zIndex: 40,
  },
  fab: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },

  bottomCardWrap: {
    position: 'absolute', bottom: 20, left: 16, right: 16, zIndex: 40,
  },
  bottomCard: {
    backgroundColor: '#FFFCF2',
    borderWidth: 2.5, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 4,
    padding: 14,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 10 },
    }),
  },
  bottomCardInner: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bottomAvatar: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
  },
  bottomTitle: { fontSize: 15, fontWeight: '900', color: INK },
  bottomSub: { fontSize: 11, color: '#8A7558', marginTop: 2 },
  endBtn: {
    paddingHorizontal: 18, paddingVertical: 10, borderRadius: 20,
    backgroundColor: RED, borderWidth: 2, borderColor: INK,
  },
  endBtnText: { color: '#fff', fontWeight: '900', fontSize: 13, letterSpacing: 1 },

  overlay: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(253,246,227,0.88)',
    justifyContent: 'center', alignItems: 'center', gap: 12, zIndex: 60,
  },
  overlayText: { fontSize: 13, color: INK, fontWeight: '700' },
  retryBtn: {
    paddingHorizontal: 24, paddingVertical: 10, borderRadius: 10,
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, marginTop: 8,
  },
  retryText: { color: INK, fontWeight: '900', letterSpacing: 1 },
});
