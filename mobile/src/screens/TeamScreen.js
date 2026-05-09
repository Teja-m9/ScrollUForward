import React, { useContext, useEffect, useState, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, StatusBar, Platform,
  ScrollView, TextInput, ActivityIndicator, Alert, Share,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { AuthContext } from '../../App';
import { teamAPI, battleAPI } from '../api';
import {
  RuledPaperBg, MarkerUnderline, Tape, DoodleDivider,
} from '../components/SketchComponents';
import { FadeInView } from '../components/AnimatedComponents';

const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const RED = '#DC2626';
const GREEN = '#059669';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

const AVATAR_COLORS = ['#2563EB', '#DC2626', '#059669', '#EA580C', '#7C3AED', '#DB2777'];

export default function TeamScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTeam, setActiveTeam] = useState(null);

  // Create form
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  // Join form
  const [joinCode, setJoinCode] = useState('');
  const [joining, setJoining] = useState(false);

  const fetchTeams = async () => {
    try {
      const res = await teamAPI.my();
      setTeams(res.data?.items || []);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTeams(); }, []);

  // Poll active team's state so we can auto-jump into battle when captain queues
  useEffect(() => {
    if (!activeTeam) return;
    const tick = async () => {
      try {
        const res = await teamAPI.get(activeTeam.id);
        const fresh = res.data;
        setActiveTeam(fresh);
        if (fresh.active_battle_id) {
          navigation.replace('Battle', { mode: 'team', battleId: fresh.active_battle_id });
        }
      } catch {}
    };
    const t = setInterval(tick, 2000);
    return () => clearInterval(t);
  }, [activeTeam?.id, activeTeam?.active_battle_id]);

  const handleCreate = async () => {
    if (!newName.trim()) return Alert.alert('Name needed', 'Give your team a name.');
    setCreating(true);
    try {
      const res = await teamAPI.create(newName.trim());
      setTeams((prev) => [...prev, res.data]);
      setActiveTeam(res.data);
      setNewName('');
    } catch (e) {
      Alert.alert('Couldn\'t create team', e?.response?.data?.detail || e?.message || '');
    } finally {
      setCreating(false);
    }
  };

  const handleJoin = async () => {
    const code = joinCode.trim().toUpperCase();
    if (!code) return Alert.alert('Code needed', 'Paste or type the invite code.');
    setJoining(true);
    try {
      const res = await teamAPI.join(code);
      setJoinCode('');
      await fetchTeams();
      setActiveTeam(res.data);
    } catch (e) {
      Alert.alert('Couldn\'t join', e?.response?.data?.detail || e?.message || '');
    } finally {
      setJoining(false);
    }
  };

  const handleLeave = (team) => {
    Alert.alert('Leave team?', `You'll lose your spot on ${team.name}.`, [
      { text: 'Stay', style: 'cancel' },
      { text: 'Leave', style: 'destructive', onPress: async () => {
        try {
          await teamAPI.leave(team.id);
          setActiveTeam(null);
          fetchTeams();
        } catch {}
      }},
    ]);
  };

  const handleKick = (team, member) => {
    Alert.alert('Kick member?', `Remove ${member.username} from ${team.name}?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Kick', style: 'destructive', onPress: async () => {
        try {
          await teamAPI.kick(team.id, member.user_id);
          const res = await teamAPI.get(team.id);
          setActiveTeam(res.data);
          fetchTeams();
        } catch {}
      }},
    ]);
  };

  const handleQueue = async (team, domain = 'physics') => {
    Alert.alert(
      'Start team battle',
      `Queue ${team.name} for a ${team.size}v${team.size} ${domain} duel?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Queue', onPress: async () => {
          try {
            const res = await battleAPI.teamQueue(team.id, domain);
            if (res.data?.matched && res.data.battle_id) {
              navigation.replace('Battle', { mode: 'team', battleId: res.data.battle_id });
            } else {
              Alert.alert('No opponent', 'No team of your size queued right now — try again in a bit.');
            }
          } catch (e) {
            Alert.alert('Queue failed', e?.response?.data?.detail || '');
          }
        }},
      ]
    );
  };

  const handleShareCode = async (team) => {
    try {
      await Share.share({
        message: `Join my ScrollU battle squad "${team.name}" — code: ${team.code}`,
      });
    } catch {}
  };

  // ─── Active team detail view ───
  if (activeTeam) {
    const isOwner = activeTeam.owner_id === (user?.user_id || user?.sub);
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" />
        <RuledPaperBg />

        <View style={s.header}>
          <TouchableOpacity onPress={() => setActiveTeam(null)} style={s.iconBtn}>
            <Ionicons name="arrow-back" size={20} color={INK} />
          </TouchableOpacity>
          <View>
            <Text style={s.title}>{activeTeam.name}</Text>
            <MarkerUnderline color={ACCENT} width={120} />
          </View>
          <View style={{ flex: 1 }} />
          <View style={[s.sizePill, { backgroundColor: ACCENT }]}>
            <Text style={s.sizePillText}>{activeTeam.size}v{activeTeam.size}</Text>
          </View>
        </View>

        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
          {/* Invite code card */}
          <View style={s.codeCard}>
            <Tape color="pink" rotate={-3} style={{ left: 14, top: -10 }} />
            <View style={{ alignItems: 'center' }}>
              <Text style={s.codeLabel}>INVITE CODE</Text>
              <Text style={s.codeText}>{activeTeam.code}</Text>
              <TouchableOpacity style={s.shareBtn} onPress={() => handleShareCode(activeTeam)}>
                <Ionicons name="share-social-outline" size={14} color={INK} />
                <Text style={s.shareBtnText}>Share invite</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Members */}
          <Text style={s.sectionHeading}>Squad · {activeTeam.size}/4</Text>
          <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />

          {activeTeam.members.map((m, i) => (
            <View key={m.user_id} style={s.memberRow}>
              <View style={[s.memberAvatar, { backgroundColor: AVATAR_COLORS[i % AVATAR_COLORS.length] }]}>
                <Text style={s.memberAvatarText}>{(m.username || '?')[0]?.toUpperCase()}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.memberName}>{m.username}</Text>
                <Text style={s.memberRole}>
                  {m.user_id === activeTeam.owner_id ? 'Captain' : 'Member'}
                </Text>
              </View>
              {isOwner && m.user_id !== activeTeam.owner_id && (
                <TouchableOpacity style={s.kickBtn} onPress={() => handleKick(activeTeam, m)}>
                  <Ionicons name="close" size={16} color={RED} />
                </TouchableOpacity>
              )}
              {m.user_id === activeTeam.owner_id && (
                <View style={s.captainBadge}>
                  <Ionicons name="star" size={12} color="#fff" />
                </View>
              )}
            </View>
          ))}

          {/* Actions */}
          <View style={{ marginTop: 18, paddingHorizontal: 16, gap: 10 }}>
            {isOwner && (
              <TouchableOpacity
                style={s.battleBtn}
                onPress={() => handleQueue(activeTeam, 'physics')}
              >
                <Ionicons name="flash" size={18} color={INK} />
                <Text style={s.battleBtnText}>Start {activeTeam.size}v{activeTeam.size} Battle</Text>
              </TouchableOpacity>
            )}
            {isOwner && (
              <Text style={{ color: '#8A7558', fontStyle: 'italic', fontSize: 11, textAlign: 'center' }}>
                Only the captain can queue. Pick a domain on the battle lobby.
              </Text>
            )}

            <TouchableOpacity style={s.secondaryBtn} onPress={() => navigation.navigate('Battle', { teamId: activeTeam.id })}>
              <Ionicons name="trophy-outline" size={16} color={INK} />
              <Text style={s.secondaryBtnText}>Battle lobby</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[s.secondaryBtn, { borderColor: RED }]} onPress={() => handleLeave(activeTeam)}>
              <Ionicons name="log-out-outline" size={16} color={RED} />
              <Text style={[s.secondaryBtnText, { color: RED }]}>
                {isOwner ? 'Disband / Leave' : 'Leave team'}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  // ─── Team list view ───
  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.iconBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Teams</Text>
          <MarkerUnderline color={ACCENT} width={80} />
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        <View style={s.heroCard}>
          <Tape color="yellow" rotate={-4} style={{ left: 16, top: -10 }} />
          <View style={s.iconsRow}>
            {[BLUE, RED, GREEN, '#7C3AED'].map((c, i) => (
              <View key={i} style={[s.squadBubble, { backgroundColor: c + '22', borderColor: c, marginLeft: i === 0 ? 0 : -10 }]}>
                <Ionicons name="person" size={18} color={c} />
              </View>
            ))}
          </View>
          <Text style={s.heroTitle}>Battle squads</Text>
          <Text style={s.heroSub}>Up to 4 players · captain queues · same-size duels only</Text>
        </View>

        {/* Create team */}
        <Text style={s.sectionHeading}>Create a team</Text>
        <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />
        <View style={s.formRow}>
          <TextInput
            style={s.input}
            placeholder="Team name (e.g. The Quark Squad)"
            placeholderTextColor="#8A7558"
            value={newName}
            onChangeText={setNewName}
            maxLength={40}
          />
          <TouchableOpacity
            style={[s.formBtn, { backgroundColor: ACCENT, opacity: creating ? 0.6 : 1 }]}
            onPress={handleCreate}
            disabled={creating}
          >
            {creating ? <ActivityIndicator color={INK} size="small" /> : <Ionicons name="add" size={20} color={INK} />}
          </TouchableOpacity>
        </View>

        {/* Join team */}
        <Text style={[s.sectionHeading, { marginTop: 18 }]}>Join with invite code</Text>
        <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />
        <View style={s.formRow}>
          <TextInput
            style={[s.input, { letterSpacing: 3, fontWeight: '800' }]}
            placeholder="XXXXXX"
            placeholderTextColor="#8A7558"
            value={joinCode}
            onChangeText={(t) => setJoinCode(t.toUpperCase())}
            maxLength={10}
            autoCapitalize="characters"
          />
          <TouchableOpacity
            style={[s.formBtn, { backgroundColor: BLUE, opacity: joining ? 0.6 : 1 }]}
            onPress={handleJoin}
            disabled={joining}
          >
            {joining ? <ActivityIndicator color="#fff" size="small" /> : <Ionicons name="log-in-outline" size={20} color="#fff" />}
          </TouchableOpacity>
        </View>

        {/* My teams */}
        <Text style={[s.sectionHeading, { marginTop: 18 }]}>My squads</Text>
        <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />

        {loading ? (
          <View style={{ alignItems: 'center', padding: 30 }}>
            <ActivityIndicator color={INK} />
          </View>
        ) : teams.length === 0 ? (
          <View style={{ alignItems: 'center', padding: 40 }}>
            <Ionicons name="people-outline" size={40} color="#C4AA78" />
            <Text style={{ marginTop: 8, color: INK, fontWeight: '800' }}>No squads yet</Text>
            <Text style={{ color: '#8A7558', marginTop: 4, textAlign: 'center', paddingHorizontal: 30 }}>
              Create one above or paste a friend's invite code to join.
            </Text>
          </View>
        ) : (
          teams.map((t, i) => (
            <FadeInView key={t.id} delay={i * 60}>
              <TouchableOpacity style={s.teamRow} onPress={() => setActiveTeam(t)} activeOpacity={0.8}>
                <View style={[s.teamIcon, { backgroundColor: AVATAR_COLORS[i % AVATAR_COLORS.length] + '22', borderColor: AVATAR_COLORS[i % AVATAR_COLORS.length] }]}>
                  <Ionicons name="people" size={22} color={AVATAR_COLORS[i % AVATAR_COLORS.length]} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.teamName}>{t.name}</Text>
                  <Text style={s.teamMeta}>
                    {t.size} {t.size === 1 ? 'member' : 'members'} · code {t.code}
                    {t.owner_id === (user?.user_id || user?.sub) ? ' · captain' : ''}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={INK} />
              </TouchableOpacity>
            </FadeInView>
          ))
        )}
      </ScrollView>
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
  iconBtn: {
    width: 38, height: 38, borderRadius: 19,
    borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },

  sizePill: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, borderWidth: 1.5, borderColor: INK },
  sizePillText: { fontSize: 11, fontWeight: '900', color: INK, letterSpacing: 1 },

  heroCard: {
    marginHorizontal: 16, marginTop: 12, padding: 18, alignItems: 'center',
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  iconsRow: { flexDirection: 'row', marginBottom: 10 },
  squadBubble: { width: 46, height: 46, borderRadius: 23, borderWidth: 2, justifyContent: 'center', alignItems: 'center' },
  heroTitle: { fontSize: 20, fontWeight: '900', color: INK, fontFamily: SERIF },
  heroSub: { fontSize: 12, color: '#8A7558', fontStyle: 'italic', marginTop: 4, textAlign: 'center' },

  sectionHeading: { fontSize: 14, fontWeight: '900', color: INK, marginLeft: 20, marginTop: 14, letterSpacing: 0.5 },

  formRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginHorizontal: 16 },
  input: {
    flex: 1, backgroundColor: '#FFFCF2', borderWidth: 1.8, borderColor: INK,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10,
    fontSize: 14, color: INK, fontFamily: SERIF,
  },
  formBtn: {
    width: 46, height: 46, borderRadius: 10,
    borderWidth: 2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },

  teamRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    marginHorizontal: 16, marginVertical: 5,
    paddingVertical: 12, paddingHorizontal: 12,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: '#E6D5B8', borderRadius: 12,
  },
  teamIcon: { width: 44, height: 44, borderRadius: 22, borderWidth: 1.5, justifyContent: 'center', alignItems: 'center' },
  teamName: { fontSize: 14, fontWeight: '900', color: INK },
  teamMeta: { fontSize: 11, color: '#8A7558', marginTop: 2 },

  // Active team view
  codeCard: {
    marginHorizontal: 16, marginTop: 12, paddingVertical: 20,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  codeLabel: { fontSize: 10, fontWeight: '900', color: '#8A7558', letterSpacing: 2 },
  codeText: { fontSize: 36, fontWeight: '900', color: INK, letterSpacing: 6, marginTop: 6, fontFamily: SERIF },
  shareBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginTop: 12, paddingHorizontal: 14, paddingVertical: 6,
    backgroundColor: ACCENT, borderWidth: 1.5, borderColor: INK, borderRadius: 10,
  },
  shareBtnText: { fontSize: 12, fontWeight: '800', color: INK },

  memberRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    marginHorizontal: 16, marginVertical: 4,
    paddingVertical: 10, paddingHorizontal: 12,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: '#E6D5B8', borderRadius: 10,
  },
  memberAvatar: {
    width: 40, height: 40, borderRadius: 20,
    borderWidth: 1.5, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
  },
  memberAvatarText: { color: '#fff', fontWeight: '900', fontSize: 16 },
  memberName: { fontSize: 14, fontWeight: '800', color: INK },
  memberRole: { fontSize: 11, color: '#8A7558', marginTop: 2 },
  kickBtn: {
    width: 30, height: 30, borderRadius: 15,
    borderWidth: 1.5, borderColor: RED,
    justifyContent: 'center', alignItems: 'center',
  },
  captainBadge: {
    width: 22, height: 22, borderRadius: 11, backgroundColor: ACCENT,
    borderWidth: 1.5, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
  },

  battleBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8, justifyContent: 'center',
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK,
    paddingHorizontal: 24, paddingVertical: 14, borderRadius: 12,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  battleBtnText: { fontSize: 14, fontWeight: '900', color: INK, letterSpacing: 0.5 },
  secondaryBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center',
    borderWidth: 1.5, borderColor: INK, backgroundColor: '#FFFCF2',
    paddingHorizontal: 20, paddingVertical: 10, borderRadius: 10,
  },
  secondaryBtnText: { fontSize: 12, fontWeight: '800', color: INK },
});
