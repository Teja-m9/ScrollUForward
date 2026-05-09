import React, { useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Dimensions, StatusBar,
  Platform, Animated, Easing, ActivityIndicator, ScrollView, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { AuthContext } from '../../App';
import { battleAPI, teamAPI } from '../api';
import {
  RuledPaperBg, MarkerUnderline, Tape, DoodleDivider, Stamp,
} from '../components/SketchComponents';
import { FadeInView, PressableCard } from '../components/AnimatedComponents';

const { width: SCREEN_W } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const GREEN = '#059669';
const RED = '#DC2626';
const PINK = '#EC4899';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

// Domain metadata re-used here
const DOMAIN_META = {
  physics:               { icon: 'planet',       color: '#EA580C', label: 'Physics' },
  ai:                    { icon: 'hardware-chip',color: '#0D9488', label: 'AI' },
  space:                 { icon: 'rocket',       color: '#4F46E5', label: 'Space' },
  biology:               { icon: 'flask',        color: '#16A34A', label: 'Biology' },
  history:               { icon: 'library',      color: '#7C3AED', label: 'History' },
  technology:            { icon: 'code-slash',   color: '#2563EB', label: 'Technology' },
  nature:                { icon: 'leaf',         color: '#059669', label: 'Nature' },
  mathematics:           { icon: 'calculator',   color: '#F59E0B', label: 'Math' },
  chemistry:             { icon: 'beaker',       color: '#DB2777', label: 'Chemistry' },
  philosophy:            { icon: 'bulb',         color: '#6B7280', label: 'Philosophy' },
  engineering:           { icon: 'construct',    color: '#CA8A04', label: 'Engineering' },
  ancient_civilizations: { icon: 'diamond',      color: '#92400E', label: 'Ancients' },
};
const metaFor = (d) => DOMAIN_META[d] || { icon: 'help-circle', color: '#8A7558', label: d };

// ═══════════════════════════════════════════════════════════════
//  MAIN  ROUTER
// ═══════════════════════════════════════════════════════════════
export default function BattleScreen({ navigation, route }) {
  const { user } = useContext(AuthContext);
  const routeMode = route?.params?.mode;
  const routeBattleId = route?.params?.battleId;
  const [phase, setPhase] = useState(routeBattleId ? 'battle' : 'lobby'); // lobby | matching | battle | result | leaderboard
  const [mode, setMode] = useState(routeMode || 'solo'); // solo | team
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [battleId, setBattleId] = useState(routeBattleId || null);
  const [finalState, setFinalState] = useState(null);

  const startMatch = (domain) => {
    setSelectedDomain(domain);
    setPhase('matching');
  };

  if (phase === 'leaderboard') {
    return <LeaderboardView onBack={() => setPhase('lobby')} />;
  }

  if (phase === 'matching') {
    return (
      <MatchmakingView
        domain={selectedDomain}
        onCancel={() => setPhase('lobby')}
        onMatched={(bid) => { setBattleId(bid); setPhase('battle'); }}
      />
    );
  }

  if (phase === 'battle') {
    return (
      <BattleLiveView
        battleId={battleId}
        onEnd={(state) => { setFinalState(state); setPhase('result'); }}
        onQuit={() => { setBattleId(null); setPhase('lobby'); }}
      />
    );
  }

  if (phase === 'result') {
    return (
      <BattleResultView
        state={finalState}
        me={user}
        onRematch={() => { setFinalState(null); setBattleId(null); setPhase('matching'); }}
        onHome={() => { setFinalState(null); setBattleId(null); setPhase('lobby'); }}
        onLeaderboard={() => setPhase('leaderboard')}
      />
    );
  }

  // Lobby — domain select + leaderboard entry
  return (
    <LobbyView
      navigation={navigation}
      onPickDomain={startMatch}
      onLeaderboard={() => setPhase('leaderboard')}
    />
  );
}

// ═══════════════════════════════════════════════════════════════
//  LOBBY
// ═══════════════════════════════════════════════════════════════
function LobbyView({ navigation, onPickDomain, onLeaderboard }) {
  const domains = Object.keys(DOMAIN_META);

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.iconBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>Knowledge Battle</Text>
          <MarkerUnderline color={ACCENT} width={130} />
        </View>
        <TouchableOpacity
          onPress={() => navigation.navigate('Teams')}
          style={[s.iconBtn, { backgroundColor: '#C4B5FD' }]}
        >
          <Ionicons name="people" size={18} color={INK} />
        </TouchableOpacity>
        <TouchableOpacity onPress={onLeaderboard} style={[s.iconBtn, { backgroundColor: ACCENT }]}>
          <Ionicons name="trophy" size={18} color={INK} />
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Hero sketch card */}
        <View style={s.heroCard}>
          <Tape color="yellow" rotate={-4} style={{ left: 16, top: -10 }} />
          <Tape color="pink" rotate={5} style={{ right: 18, top: -8 }} width={58} />
          <View style={{ alignItems: 'center', marginVertical: 6 }}>
            <View style={s.vsRow}>
              <View style={[s.vsBubble, { backgroundColor: BLUE + '22', borderColor: BLUE }]}>
                <Ionicons name="person" size={24} color={BLUE} />
              </View>
              <View style={s.vsMiddle}>
                <Ionicons name="flash" size={20} color={ACCENT} />
                <Text style={s.vsText}>VS</Text>
                <Ionicons name="flash" size={20} color={ACCENT} />
              </View>
              <View style={[s.vsBubble, { backgroundColor: RED + '22', borderColor: RED }]}>
                <Ionicons name="skull" size={24} color={RED} />
              </View>
            </View>
            <Text style={s.heroTitle}>Duel a stranger</Text>
            <Text style={s.heroSub}>
              5 questions · 10 seconds each · speed = more points
            </Text>
          </View>
        </View>

        {/* Team battle CTA */}
        <TouchableOpacity
          style={s.teamCta}
          onPress={() => navigation.navigate('Teams')}
          activeOpacity={0.88}
        >
          <View style={s.teamCtaIcons}>
            {['#2563EB', '#DC2626', '#059669', '#7C3AED'].map((c, i) => (
              <View key={i} style={[s.teamCtaBubble, { backgroundColor: c + '22', borderColor: c, marginLeft: i === 0 ? 0 : -12 }]}>
                <Ionicons name="person" size={12} color={c} />
              </View>
            ))}
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={s.teamCtaTitle}>Team Battles · up to 4v4</Text>
            <Text style={s.teamCtaSub}>Squad up → duel same-size teams</Text>
          </View>
          <View style={s.teamCtaArrow}>
            <Ionicons name="chevron-forward" size={16} color={INK} />
          </View>
        </TouchableOpacity>

        {/* Rules — sketchy bullet list */}
        <View style={s.rulesWrap}>
          {[
            { icon: 'timer-outline', text: 'Each question has 10s — faster answers earn more' },
            { icon: 'trending-up',   text: 'Win = rating up · lose = rating down (ELO)' },
            { icon: 'trophy-outline', text: 'Climb the ranked leaderboard' },
          ].map((r, i) => (
            <View key={i} style={s.ruleRow}>
              <Ionicons name={r.icon} size={16} color={INK} />
              <Text style={s.ruleText}>{r.text}</Text>
            </View>
          ))}
        </View>

        <Text style={s.pickLabel}>Pick a battleground</Text>
        <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />

        <View style={s.domainGrid}>
          {domains.map((d, i) => {
            const m = metaFor(d);
            return (
              <FadeInView key={d} delay={i * 50}>
                <PressableCard
                  style={[s.domainCard, { borderColor: m.color }]}
                  onPress={() => onPickDomain(d)}
                >
                  <View style={[s.domainIcon, { backgroundColor: m.color + '22', borderColor: m.color }]}>
                    <Ionicons name={m.icon} size={22} color={m.color} />
                  </View>
                  <Text style={[s.domainName, { color: m.color }]}>{m.label}</Text>
                  <View style={[s.duelBadge, { backgroundColor: m.color + '15', borderColor: m.color }]}>
                    <Ionicons name="flash" size={10} color={m.color} />
                    <Text style={[s.duelBadgeText, { color: m.color }]}>DUEL</Text>
                  </View>
                </PressableCard>
              </FadeInView>
            );
          })}
        </View>
      </ScrollView>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
//  MATCHMAKING
// ═══════════════════════════════════════════════════════════════
function MatchmakingView({ domain, onCancel, onMatched }) {
  const m = metaFor(domain);
  const [elapsed, setElapsed] = useState(0);
  const [status, setStatus] = useState('searching'); // searching | none | error
  const cancelled = useRef(false);
  const spin = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    cancelled.current = false;
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);

    Animated.loop(
      Animated.timing(spin, { toValue: 1, duration: 4000, easing: Easing.linear, useNativeDriver: true })
    ).start();
    Animated.loop(
      Animated.timing(pulse, { toValue: 1, duration: 1200, useNativeDriver: true, easing: Easing.out(Easing.quad) })
    ).start();

    (async () => {
      try {
        const res = await battleAPI.queue(domain);
        if (cancelled.current) return;
        if (res.data?.matched && res.data.battle_id) {
          onMatched(res.data.battle_id);
        } else {
          setStatus('none');
        }
      } catch (e) {
        if (!cancelled.current) setStatus('error');
      }
    })();

    return () => {
      cancelled.current = true;
      clearInterval(t);
      battleAPI.cancelQueue(domain).catch(() => {});
    };
  }, []);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const pulseSc = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.35] });
  const pulseOp = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.7, 0] });

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      <View style={s.header}>
        <TouchableOpacity onPress={onCancel} style={s.iconBtn}>
          <Ionicons name="close" size={22} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Finding opponent…</Text>
          <MarkerUnderline color={ACCENT} width={140} />
        </View>
      </View>

      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20 }}>
        {/* Spinning dashed ring */}
        <View style={{ width: 200, height: 200, justifyContent: 'center', alignItems: 'center' }}>
          <Animated.View style={{
            position: 'absolute',
            width: 200, height: 200, borderRadius: 100,
            borderWidth: 2, borderColor: m.color,
            borderStyle: 'dashed',
            opacity: pulseOp,
            transform: [{ scale: pulseSc }],
          }} />
          <Animated.View style={{
            width: 180, height: 180, borderRadius: 90,
            borderWidth: 2.5, borderColor: INK,
            borderStyle: 'dashed',
            justifyContent: 'center', alignItems: 'center',
            transform: [{ rotate }],
          }}>
            <View style={[s.magnify, { backgroundColor: m.color + '22', borderColor: m.color }]}>
              <Ionicons name={m.icon} size={44} color={m.color} />
            </View>
          </Animated.View>
        </View>

        <Text style={[s.heroTitle, { marginTop: 24 }]}>{m.label} Arena</Text>
        <Text style={s.heroSub}>{status === 'none' ? 'No opponents found' : `Searching… ${elapsed}s`}</Text>

        {status === 'none' && (
          <View style={{ marginTop: 16, alignItems: 'center' }}>
            <Text style={{ color: '#8A7558', fontStyle: 'italic', textAlign: 'center', paddingHorizontal: 30 }}>
              Nobody queued for {m.label} right now. Try another domain or come back soon.
            </Text>
          </View>
        )}
        {status === 'error' && (
          <Text style={{ color: RED, marginTop: 12 }}>Connection error. Try again.</Text>
        )}

        <TouchableOpacity style={s.cancelBtn} onPress={onCancel}>
          <Ionicons name="close-circle-outline" size={16} color={INK} />
          <Text style={s.cancelText}>{status === 'searching' ? 'Cancel search' : 'Back'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
//  LIVE BATTLE
// ═══════════════════════════════════════════════════════════════
function BattleLiveView({ battleId, onEnd, onQuit }) {
  const [state, setState] = useState(null);
  const [err, setErr] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(null);
  const questionStartRef = useRef(Date.now());
  const lastIdxRef = useRef(-1);
  const lastSubmittedRef = useRef(-1);
  const pollRef = useRef(null);

  const isTeam = state?.mode === 'team';

  // Poll state every 900ms
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const res = await battleAPI.state(battleId);
        if (!alive) return;
        setState(res.data);
        if (res.data?.status === 'finished') {
          clearInterval(pollRef.current);
          setTimeout(() => onEnd(res.data), 800);
        }
      } catch (e) {
        if (!alive) return;
        setErr(e?.response?.data?.detail || 'Connection lost');
      }
    };
    tick();
    pollRef.current = setInterval(tick, 900);
    return () => { alive = false; clearInterval(pollRef.current); };
  }, [battleId]);

  // Reset per-question state when idx changes
  useEffect(() => {
    if (!state) return;
    if (state.current_idx !== lastIdxRef.current) {
      lastIdxRef.current = state.current_idx;
      questionStartRef.current = Date.now();
      setSelectedIdx(null);
    }
  }, [state?.current_idx]);

  const handleAnswer = (idx) => {
    if (!state || selectedIdx != null || state.me_answered) return;
    if (lastSubmittedRef.current === state.current_idx) return;
    lastSubmittedRef.current = state.current_idx;
    setSelectedIdx(idx);
    const timeMs = Math.max(0, Date.now() - questionStartRef.current);
    const submitter = state.mode === 'team' ? battleAPI.teamAnswer : battleAPI.answer;
    submitter(battleId, {
      question_idx: state.current_idx,
      answer_idx: idx,
      time_ms: timeMs,
    }).then((res) => setState(res.data)).catch(() => {});
  };

  const confirmQuit = () => {
    Alert.alert('Forfeit battle?', 'Your opponent will win this duel.', [
      { text: 'Keep fighting', style: 'cancel' },
      { text: 'Forfeit', style: 'destructive', onPress: () => {
        battleAPI.leave(battleId).catch(() => {});
        onQuit();
      }},
    ]);
  };

  if (!state) {
    return (
      <View style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <StatusBar barStyle="dark-content" />
        <RuledPaperBg />
        <ActivityIndicator color={INK} size="large" />
        <Text style={{ marginTop: 10, color: INK, fontStyle: 'italic' }}>Entering the arena…</Text>
        {err && <Text style={{ color: RED, marginTop: 8 }}>{err}</Text>}
      </View>
    );
  }

  const m = metaFor(state.domain);
  const total = state.question_count || 5;
  const idx = state.current_idx;
  const q = state.question;
  const timeLeft = state.seconds_left;

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      {/* Top: quit + domain stamp + progress */}
      <View style={s.battleTop}>
        <TouchableOpacity style={s.iconBtn} onPress={confirmQuit}>
          <Ionicons name="close" size={22} color={INK} />
        </TouchableOpacity>
        <View style={[s.domainPill, { borderColor: m.color, backgroundColor: m.color + '22' }]}>
          <Ionicons name={m.icon} size={14} color={m.color} />
          <Text style={[s.domainPillText, { color: m.color }]}>{m.label.toUpperCase()}</Text>
        </View>
        <View style={s.qCounter}>
          <Text style={s.qCounterText}>Q{idx + 1}/{total}</Text>
        </View>
      </View>

      {/* Score comparison — team vs team OR player vs player */}
      {isTeam ? (
        <View style={s.scoreRow}>
          <TeamScorePanel team={state.my_team} color={BLUE} isMe me_id={state.my_team?.members?.find?.((m) => m.score != null)?.user_id} />
          <View style={s.vsDivider}>
            <Ionicons name="flash" size={14} color={ACCENT} />
            <Text style={{ fontWeight: '900', color: INK, fontSize: 12, letterSpacing: 1 }}>VS</Text>
            <Ionicons name="flash" size={14} color={ACCENT} />
          </View>
          <TeamScorePanel team={state.opponent_team} color={RED} />
        </View>
      ) : (
        <View style={s.scoreRow}>
          <PlayerScorePanel player={state.me} color={BLUE} isMe label="YOU" answered={state.me_answered} />
          <View style={s.vsDivider}>
            <Ionicons name="flash" size={14} color={ACCENT} />
            <Text style={{ fontWeight: '900', color: INK, fontSize: 12, letterSpacing: 1 }}>VS</Text>
            <Ionicons name="flash" size={14} color={ACCENT} />
          </View>
          <PlayerScorePanel player={state.opponent} color={RED} label="OPP" answered={state.opp_answered} />
        </View>
      )}

      {/* Timer bar */}
      <View style={s.timerBarWrap}>
        <View style={[s.timerBar, {
          width: `${(timeLeft / 10) * 100}%`,
          backgroundColor: timeLeft <= 3 ? RED : timeLeft <= 6 ? '#EA580C' : GREEN,
        }]} />
      </View>
      <Text style={[s.timerText, { color: timeLeft <= 3 ? RED : INK }]}>{timeLeft}s</Text>

      {/* Progress dots */}
      <View style={s.dotsRow}>
        {Array.from({ length: total }, (_, i) => (
          <View key={i} style={[
            s.dot,
            i < idx ? s.dotDone : null,
            i === idx ? s.dotActive : null,
          ]} />
        ))}
      </View>

      {/* Question */}
      {q && (
        <View style={{ paddingHorizontal: 16 }}>
          <View style={s.questionCard}>
            <View style={s.qBadge}>
              <Text style={s.qBadgeText}>Q{idx + 1}</Text>
            </View>
            <Text style={s.questionText}>{q.q}</Text>
          </View>

          {/* Options */}
          <View style={{ gap: 10, marginTop: 14 }}>
            {q.options.map((opt, i) => {
              const chosen = selectedIdx === i || (state.me_answered && state.me?.last === i);
              const optStyle = [s.option, chosen && s.optionPicked];
              return (
                <TouchableOpacity
                  key={i}
                  style={optStyle}
                  onPress={() => handleAnswer(i)}
                  activeOpacity={0.8}
                  disabled={selectedIdx != null || state.me_answered}
                >
                  <View style={s.optLetter}>
                    <Text style={s.optLetterText}>{String.fromCharCode(65 + i)}</Text>
                  </View>
                  <Text style={s.optText}>{opt}</Text>
                  {chosen && <Ionicons name="checkmark-circle" size={20} color={BLUE} />}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Waiting state */}
          {state.me_answered && !state.opp_answered && (
            <View style={s.waitingPill}>
              <ActivityIndicator size="small" color={INK} />
              <Text style={s.waitingText}>Waiting for opponent…</Text>
            </View>
          )}
          {!state.me_answered && state.opp_answered && (
            <View style={[s.waitingPill, { backgroundColor: RED + '22', borderColor: RED }]}>
              <Ionicons name="alert-circle-outline" size={16} color={RED} />
              <Text style={[s.waitingText, { color: RED }]}>Opponent answered — hurry!</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

function PlayerScorePanel({ player, color, label, isMe, answered }) {
  return (
    <View style={[s.playerPanel, { borderColor: color }]}>
      <View style={[s.playerAvatar, { backgroundColor: color + '22', borderColor: color }]}>
        <Text style={[s.playerAvatarText, { color }]}>
          {(player?.username || '?')[0]?.toUpperCase()}
        </Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={s.playerName} numberOfLines={1}>
          {isMe ? 'You' : (player?.username || 'Rival')}
        </Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Text style={[s.playerScore, { color }]}>{player?.score || 0}</Text>
          {answered && <Ionicons name="checkmark-circle" size={12} color={GREEN} />}
        </View>
      </View>
    </View>
  );
}

function TeamScorePanel({ team, color, isMe }) {
  if (!team) return <View style={[s.playerPanel, { borderColor: color }]} />;
  return (
    <View style={[s.playerPanel, { borderColor: color, flexDirection: 'column', alignItems: 'stretch', gap: 4 }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
        <View style={[s.teamStripe, { backgroundColor: color }]} />
        <Text style={[s.playerName, { flex: 1 }]} numberOfLines={1}>
          {isMe ? 'Your team' : team.name}
        </Text>
        <Text style={[s.playerScore, { color, fontSize: 20 }]}>{team.score || 0}</Text>
      </View>
      <View style={{ flexDirection: 'row', gap: 4, flexWrap: 'wrap' }}>
        {(team.members || []).slice(0, 4).map((m, i) => {
          const ans = team.answered_count != null; // proxy; backend sends per-member indirectly via all_answered
          return (
            <View key={m.user_id} style={[s.memberChip, { borderColor: color + '88' }]}>
              <View style={[s.memberChipDot, { backgroundColor: color }]}>
                <Text style={s.memberChipDotText}>{(m.username || '?')[0]?.toUpperCase()}</Text>
              </View>
              <Text style={s.memberChipScore}>{m.score || 0}</Text>
            </View>
          );
        })}
      </View>
      <Text style={{ fontSize: 9, color: '#8A7558', fontStyle: 'italic' }}>
        {team.answered_count || 0}/{team.members?.length || 0} answered
      </Text>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
//  RESULT
// ═══════════════════════════════════════════════════════════════
function BattleResultView({ state, me, onRematch, onHome, onLeaderboard }) {
  if (!state) return null;
  const isTeam = state.mode === 'team';
  const myUid = me?.user_id || me?.sub;

  let isWinner, isDraw, myDelta, myScore, oppScore, myLabel, oppLabel, myCorrect, oppCorrect;
  if (isTeam) {
    isWinner = state.winner_team_id === state.my_team?.team_id;
    isDraw = !state.winner_team_id;
    myDelta = state.rating_deltas?.[myUid] || 0;
    myScore = state.my_team?.score || 0;
    oppScore = state.opponent_team?.score || 0;
    myLabel = 'YOUR TEAM';
    oppLabel = (state.opponent_team?.name || 'RIVALS').toUpperCase();
    myCorrect = state.my_team?.correct || 0;
    oppCorrect = state.opponent_team?.correct || 0;
  } else {
    isWinner = state.winner_id === state.me?.user_id;
    isDraw = !state.winner_id;
    myDelta = state.rating_deltas?.[state.me?.user_id] || 0;
    myScore = state.me?.score || 0;
    oppScore = state.opponent?.score || 0;
    myLabel = 'YOU';
    oppLabel = (state.opponent?.username || 'Rival').slice(0, 14);
    myCorrect = state.me?.correct || 0;
    oppCorrect = state.opponent?.correct || 0;
  }
  const m = metaFor(state.domain);
  const resultColor = isDraw ? '#8A7558' : (isWinner ? GREEN : RED);
  const resultLabel = isDraw ? 'DRAW' : (isWinner ? 'VICTORY' : 'DEFEAT');

  const scale = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.spring(scale, { toValue: 1, friction: 5, tension: 80, useNativeDriver: true }).start();
  }, []);

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40, paddingTop: Platform.OS === 'android' ? 40 : 60 }}>
        <Animated.View style={[s.resultCard, { transform: [{ scale }], borderColor: resultColor }]}>
          {/* Stamp */}
          <View style={[s.resultStamp, { borderColor: resultColor, transform: [{ rotate: isWinner ? '-6deg' : '4deg' }] }]}>
            <Text style={[s.resultStampText, { color: resultColor }]}>{resultLabel}</Text>
          </View>

          <View style={{ alignItems: 'center', marginTop: 16 }}>
            <Ionicons name={isWinner ? 'trophy' : (isDraw ? 'medal-outline' : 'flash-off-outline')} size={48} color={resultColor} />
            <Text style={[s.resultTitle, { color: resultColor }]}>{resultLabel}</Text>
            <Text style={s.resultSub}>{m.label} arena</Text>
          </View>

          {/* Score comparison */}
          <View style={s.resultScoreRow}>
            <View style={[s.resultPlayer, { borderColor: BLUE }]}>
              <Text style={[s.resultPlayerLabel, { color: BLUE }]}>{myLabel}</Text>
              <Text style={s.resultPlayerScore}>{myScore}</Text>
              <Text style={s.resultPlayerMeta}>{myCorrect}/{state.question_count} correct</Text>
            </View>
            <Text style={{ fontSize: 26, fontWeight: '900', color: INK, marginHorizontal: 10 }}>vs</Text>
            <View style={[s.resultPlayer, { borderColor: RED }]}>
              <Text style={[s.resultPlayerLabel, { color: RED }]} numberOfLines={1}>{oppLabel}</Text>
              <Text style={s.resultPlayerScore}>{oppScore}</Text>
              <Text style={s.resultPlayerMeta}>{oppCorrect}/{state.question_count} correct</Text>
            </View>
          </View>

          {/* Rating delta */}
          <View style={[s.ratingPill, {
            backgroundColor: myDelta >= 0 ? GREEN + '22' : RED + '22',
            borderColor: myDelta >= 0 ? GREEN : RED,
          }]}>
            <Ionicons name={myDelta >= 0 ? 'trending-up' : 'trending-down'} size={16} color={myDelta >= 0 ? GREEN : RED} />
            <Text style={[s.ratingText, { color: myDelta >= 0 ? GREEN : RED }]}>
              {myDelta >= 0 ? '+' : ''}{myDelta} rating
            </Text>
          </View>

          <DoodleDivider style={{ marginVertical: 14 }} />

          {/* Actions */}
          <TouchableOpacity style={s.rematchBtn} onPress={onRematch}>
            <Ionicons name="flash" size={18} color={INK} />
            <Text style={s.rematchBtnText}>Rematch</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.secondaryBtn} onPress={onLeaderboard}>
            <Ionicons name="trophy-outline" size={16} color={INK} />
            <Text style={s.secondaryBtnText}>View leaderboard</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.secondaryBtn, { marginTop: 8 }]} onPress={onHome}>
            <Text style={{ color: '#8A7558', fontSize: 13 }}>Back to lobby</Text>
          </TouchableOpacity>
        </Animated.View>
      </ScrollView>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
//  LEADERBOARD
// ═══════════════════════════════════════════════════════════════
function LeaderboardView({ onBack }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    battleAPI.leaderboard()
      .then((r) => setItems(r.data?.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const rankColor = (rank) => rank === 1 ? '#F59E0B' : rank === 2 ? '#94A3B8' : rank === 3 ? '#CA8A04' : INK;

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" />
      <RuledPaperBg />

      <View style={s.header}>
        <TouchableOpacity onPress={onBack} style={s.iconBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View>
          <Text style={s.title}>Ranked Leaderboard</Text>
          <MarkerUnderline color={ACCENT} width={150} />
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        {loading ? (
          <View style={{ alignItems: 'center', paddingVertical: 40 }}>
            <ActivityIndicator color={INK} />
          </View>
        ) : items.length === 0 ? (
          <View style={{ alignItems: 'center', paddingVertical: 60 }}>
            <Ionicons name="trophy-outline" size={48} color="#C4AA78" />
            <Text style={{ marginTop: 10, fontWeight: '800', color: INK }}>No duelists yet</Text>
            <Text style={{ color: '#8A7558', marginTop: 4 }}>Play a battle to appear here</Text>
          </View>
        ) : (
          <View style={{ paddingHorizontal: 16, paddingTop: 4 }}>
            {items.map((item) => (
              <View key={item.user_id} style={[s.lbRow, { borderLeftColor: rankColor(item.rank) }]}>
                <View style={[s.lbRankBadge, { backgroundColor: rankColor(item.rank) + '22', borderColor: rankColor(item.rank) }]}>
                  <Text style={[s.lbRankText, { color: rankColor(item.rank) }]}>
                    {item.rank <= 3 ? ['🥇','🥈','🥉'][item.rank - 1] : `#${item.rank}`}
                  </Text>
                </View>
                <View style={{ flex: 1, marginLeft: 10 }}>
                  <Text style={s.lbName} numberOfLines={1}>{item.username}</Text>
                  <Text style={s.lbMeta}>{item.wins}W · {item.losses}L{item.draws ? ` · ${item.draws}D` : ''}</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={s.lbRating}>{item.rating}</Text>
                  <Text style={s.lbRatingLabel}>rating</Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
//  STYLES
// ═══════════════════════════════════════════════════════════════
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

  // Team CTA
  teamCta: {
    marginHorizontal: 16, marginTop: 12,
    paddingHorizontal: 14, paddingVertical: 12,
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#FFFCF2',
    borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 14,
    borderBottomLeftRadius: 14, borderBottomRightRadius: 4,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 3 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  teamCtaIcons: { flexDirection: 'row' },
  teamCtaBubble: {
    width: 28, height: 28, borderRadius: 14, borderWidth: 1.5,
    justifyContent: 'center', alignItems: 'center',
  },
  teamCtaTitle: { fontSize: 13, fontWeight: '900', color: INK },
  teamCtaSub: { fontSize: 10, color: '#8A7558', fontStyle: 'italic', marginTop: 1 },
  teamCtaArrow: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: '#C4B5FD', borderWidth: 1.5, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
  },

  // Team score panel chips
  teamStripe: { width: 4, height: 18, borderRadius: 2 },
  memberChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 4, paddingVertical: 2,
    borderWidth: 1, borderRadius: 6,
    backgroundColor: '#FFFCF2',
  },
  memberChipDot: {
    width: 16, height: 16, borderRadius: 8,
    justifyContent: 'center', alignItems: 'center',
  },
  memberChipDotText: { color: '#fff', fontSize: 9, fontWeight: '900' },
  memberChipScore: { fontSize: 10, fontWeight: '900', color: INK },

  // Hero
  heroCard: {
    marginHorizontal: 16, marginTop: 12, padding: 16,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  vsRow: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 12 },
  vsBubble: {
    width: 60, height: 60, borderRadius: 30, borderWidth: 2.5,
    justifyContent: 'center', alignItems: 'center',
  },
  vsMiddle: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  vsText: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: 1.5 },
  heroTitle: { fontSize: 20, fontWeight: '900', color: INK, marginTop: 4, fontFamily: SERIF },
  heroSub: { fontSize: 12, color: '#8A7558', fontStyle: 'italic', marginTop: 4, textAlign: 'center' },

  // Rules
  rulesWrap: { marginHorizontal: 20, marginTop: 16, gap: 6 },
  ruleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  ruleText: { fontSize: 12, color: INK, flex: 1, fontStyle: 'italic' },

  pickLabel: { fontSize: 14, fontWeight: '900', color: INK, marginLeft: 20, marginTop: 18, letterSpacing: 0.5 },

  // Domain cards
  domainGrid: { paddingHorizontal: 12, marginTop: 8, flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  domainCard: {
    width: (SCREEN_W - 34) / 2,
    backgroundColor: '#FFFCF2',
    borderWidth: 2, borderRadius: 12,
    padding: 14, flexDirection: 'row', alignItems: 'center', gap: 10,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  domainIcon: { width: 40, height: 40, borderRadius: 20, borderWidth: 1.5, justifyContent: 'center', alignItems: 'center' },
  domainName: { fontSize: 13, fontWeight: '800', flex: 1 },
  duelBadge: {
    paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, borderWidth: 1,
    flexDirection: 'row', alignItems: 'center', gap: 2,
  },
  duelBadgeText: { fontSize: 9, fontWeight: '900', letterSpacing: 1 },

  // Matchmaking
  magnify: {
    width: 90, height: 90, borderRadius: 45, borderWidth: 2,
    justifyContent: 'center', alignItems: 'center',
  },
  cancelBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 20,
    paddingHorizontal: 18, paddingVertical: 10, borderRadius: 12,
    borderWidth: 1.5, borderColor: INK, backgroundColor: '#FFFCF2',
  },
  cancelText: { fontSize: 13, fontWeight: '800', color: INK },

  // Battle header
  battleTop: {
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54,
    paddingHorizontal: 16, paddingBottom: 8,
    flexDirection: 'row', alignItems: 'center', gap: 10,
  },
  domainPill: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    paddingVertical: 8, paddingHorizontal: 10, borderRadius: 20, borderWidth: 1.8,
  },
  domainPillText: { fontSize: 11, fontWeight: '900', letterSpacing: 1 },
  qCounter: {
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10,
    backgroundColor: ACCENT, borderWidth: 1.5, borderColor: INK,
  },
  qCounterText: { fontSize: 12, fontWeight: '900', color: INK, letterSpacing: 1 },

  // Score panels
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, marginTop: 6 },
  playerPanel: {
    flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingVertical: 8, paddingHorizontal: 10,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderRadius: 12,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 2 },
    }),
  },
  playerAvatar: {
    width: 38, height: 38, borderRadius: 19, borderWidth: 1.5,
    justifyContent: 'center', alignItems: 'center',
  },
  playerAvatarText: { fontWeight: '900', fontSize: 16 },
  playerName: { fontSize: 12, fontWeight: '800', color: INK },
  playerScore: { fontSize: 22, fontWeight: '900' },
  vsDivider: { alignItems: 'center', gap: 2 },

  // Timer
  timerBarWrap: {
    height: 6, marginHorizontal: 16, marginTop: 10, borderRadius: 3,
    backgroundColor: '#E6D5B8', overflow: 'hidden',
    borderWidth: 1, borderColor: '#C4AA78',
  },
  timerBar: { height: '100%', borderRadius: 3 },
  timerText: { textAlign: 'center', fontSize: 12, fontWeight: '900', marginTop: 4 },

  // Progress
  dotsRow: { flexDirection: 'row', justifyContent: 'center', gap: 6, marginTop: 6, marginBottom: 10 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#E6D5B8', borderWidth: 1, borderColor: '#C4AA78' },
  dotDone: { backgroundColor: GREEN, borderColor: GREEN },
  dotActive: { backgroundColor: ACCENT, borderColor: INK, transform: [{ scale: 1.25 }] },

  // Question
  questionCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 16, borderBottomLeftRadius: 16, borderBottomRightRadius: 4,
    padding: 16, marginTop: 8,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  qBadge: {
    position: 'absolute', top: -10, left: 14,
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, borderRadius: 4,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  qBadgeText: { fontSize: 10, fontWeight: '900', color: INK, letterSpacing: 1 },
  questionText: { fontSize: 16, fontWeight: '700', color: INK, lineHeight: 24, marginTop: 8, fontFamily: SERIF },

  option: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#C4AA78',
    borderRadius: 12, padding: 12,
  },
  optionPicked: { backgroundColor: BLUE + '15', borderColor: BLUE },
  optLetter: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: '#F3EACD', borderWidth: 1.5, borderColor: '#C4AA78',
    justifyContent: 'center', alignItems: 'center',
  },
  optLetterText: { fontSize: 13, fontWeight: '900', color: INK },
  optText: { flex: 1, fontSize: 14, fontWeight: '600', color: INK },

  waitingPill: {
    marginTop: 12, paddingVertical: 8, paddingHorizontal: 12,
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: '#FFF7ED', borderWidth: 1.5, borderColor: '#EA580C40',
    borderRadius: 10, alignSelf: 'center',
  },
  waitingText: { fontSize: 11, fontWeight: '700', color: INK, fontStyle: 'italic' },

  // Result
  resultCard: {
    marginHorizontal: 16,
    backgroundColor: '#FFFCF2', borderWidth: 2.5,
    borderTopLeftRadius: 4, borderTopRightRadius: 22, borderBottomLeftRadius: 22, borderBottomRightRadius: 4,
    padding: 18,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 10 },
    }),
  },
  resultStamp: {
    position: 'absolute', top: 14, right: 14,
    borderWidth: 2, borderRadius: 3, paddingHorizontal: 10, paddingVertical: 4,
  },
  resultStampText: { fontSize: 10, fontWeight: '900', letterSpacing: 2 },
  resultTitle: { fontSize: 28, fontWeight: '900', letterSpacing: -0.5, marginTop: 8, fontFamily: SERIF },
  resultSub: { fontSize: 12, color: '#8A7558', fontStyle: 'italic' },

  resultScoreRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 20, marginBottom: 10 },
  resultPlayer: {
    alignItems: 'center', padding: 12, minWidth: 110,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderRadius: 12,
  },
  resultPlayerLabel: { fontSize: 10, fontWeight: '900', letterSpacing: 1 },
  resultPlayerScore: { fontSize: 28, fontWeight: '900', color: INK, marginTop: 2 },
  resultPlayerMeta: { fontSize: 10, color: '#8A7558', marginTop: 4 },
  ratingPill: {
    alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 12,
    borderWidth: 1.5, marginTop: 6,
  },
  ratingText: { fontSize: 13, fontWeight: '900' },

  rematchBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center',
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK,
    paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  rematchBtnText: { fontSize: 15, fontWeight: '900', color: INK, letterSpacing: 0.5 },
  secondaryBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center',
    paddingVertical: 8, marginTop: 10,
  },
  secondaryBtnText: { fontSize: 13, fontWeight: '700', color: INK },

  // Leaderboard
  lbRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: '#E6D5B8',
    borderLeftWidth: 5,
    borderRadius: 10, padding: 12, marginVertical: 4,
  },
  lbRankBadge: {
    width: 42, height: 42, borderRadius: 21, borderWidth: 1.5,
    justifyContent: 'center', alignItems: 'center',
  },
  lbRankText: { fontSize: 13, fontWeight: '900' },
  lbName: { fontSize: 14, fontWeight: '800', color: INK },
  lbMeta: { fontSize: 11, color: '#8A7558', marginTop: 2 },
  lbRating: { fontSize: 18, fontWeight: '900', color: INK },
  lbRatingLabel: { fontSize: 9, color: '#8A7558', letterSpacing: 0.5 },
});
