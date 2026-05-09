import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  StatusBar, Platform, Animated, Easing,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { FadeInView, SuccessCheck } from '../components/AnimatedComponents';
import { AnimatedCounter, ConfettiBurst, ProgressRing } from '../components/PremiumAnimations';
import { DoodleDivider, MarkerUnderline, Stamp } from '../components/SketchComponents';

const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const GREEN = '#059669';
const ORANGE = '#EA580C';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

// 30 daily challenges — rotates by day of year
const CHALLENGES = [
  { icon: 'bulb', color: '#FFD60A', title: 'Learn 3 New AI Concepts', task: 'Watch 3 AI reels and share your favorite takeaway', iq: 50, domain: 'ai' },
  { icon: 'rocket', color: '#4F46E5', title: 'Mars Exploration Day', task: 'Read 1 article about Mars and write a 100-char summary', iq: 40, domain: 'space' },
  { icon: 'flask', color: '#059669', title: 'Biology Deep Dive', task: 'Take the Biology quiz and score at least 70%', iq: 60, domain: 'biology' },
  { icon: 'library', color: '#7C3AED', title: 'History Explorer', task: 'Join a History discussion room and post a thoughtful reply', iq: 55, domain: 'history' },
  { icon: 'code-slash', color: '#2563EB', title: 'Tech Enthusiast', task: 'Save 5 tech reels you want to revisit later', iq: 35, domain: 'technology' },
  { icon: 'leaf', color: '#10B981', title: 'Nature Walk', task: 'Explore Nature category and like 10 posts', iq: 30, domain: 'nature' },
  { icon: 'planet', color: '#EA580C', title: 'Quantum Thinker', task: 'Take the Physics quiz — aim for 80%+ accuracy', iq: 70, domain: 'physics' },
  { icon: 'calculator', color: '#EA580C', title: 'Math Marathon', task: 'Complete 2 Math quizzes back-to-back', iq: 65, domain: 'mathematics' },
  { icon: 'sparkles', color: '#EC4899', title: 'Create & Share', task: 'Post your own content (reel, image, or quote)', iq: 80, domain: 'all' },
  { icon: 'chatbubbles', color: '#0D9488', title: 'Start a Conversation', task: 'Comment on 5 different posts today', iq: 40, domain: 'all' },
  { icon: 'bookmark', color: '#7C3AED', title: 'Curator Mode', task: 'Save 10 pieces of content across any domain', iq: 35, domain: 'all' },
  { icon: 'people', color: '#2563EB', title: 'Social Scholar', task: 'Follow 3 new users with interesting content', iq: 30, domain: 'all' },
  { icon: 'flash', color: '#FFD60A', title: 'Speed Runner', task: 'Complete any quiz in under 60 seconds', iq: 50, domain: 'all' },
  { icon: 'book', color: '#059669', title: 'Knowledge Seeker', task: 'Read 3 full articles end-to-end', iq: 55, domain: 'all' },
  { icon: 'trophy', color: '#EA580C', title: 'Perfect Score Day', task: 'Get 100% on at least one quiz today', iq: 100, domain: 'all' },
];

export default function DailyChallengeScreen({ navigation }) {
  const [challenge, setChallenge] = useState(null);
  const [completed, setCompleted] = useState(false);
  const [streak, setStreak] = useState(0);
  const [totalCompleted, setTotalCompleted] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    loadChallenge();
    const timer = setInterval(updateTimeLeft, 60000);
    updateTimeLeft();
    return () => clearInterval(timer);
  }, []);

  const updateTimeLeft = () => {
    const now = new Date();
    const tomorrow = new Date(now); tomorrow.setDate(now.getDate() + 1); tomorrow.setHours(0, 0, 0, 0);
    const diff = tomorrow - now;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    setTimeLeft(`${hours}h ${mins}m`);
  };

  const loadChallenge = async () => {
    const today = new Date().toDateString();
    const dayOfYear = Math.floor((new Date() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
    const idx = dayOfYear % CHALLENGES.length;
    setChallenge(CHALLENGES[idx]);

    try {
      const data = await AsyncStorage.getItem('daily_challenge_data');
      const state = data ? JSON.parse(data) : { streak: 0, totalCompleted: 0, lastCompleted: null, completedToday: false };
      // Check if today's challenge is already done
      setCompleted(state.lastCompleted === today);
      setStreak(state.streak || 0);
      setTotalCompleted(state.totalCompleted || 0);
    } catch {}
  };

  const markComplete = async () => {
    const today = new Date().toDateString();
    const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toDateString();

    try {
      const data = await AsyncStorage.getItem('daily_challenge_data');
      const state = data ? JSON.parse(data) : { streak: 0, totalCompleted: 0, lastCompleted: null };

      // Build streak: if last completed was yesterday, +1. If same day, no change. Otherwise reset.
      let newStreak = state.streak;
      if (state.lastCompleted === yesterdayStr) newStreak += 1;
      else if (state.lastCompleted !== today) newStreak = 1;

      const newState = {
        streak: newStreak,
        totalCompleted: (state.totalCompleted || 0) + 1,
        lastCompleted: today,
      };
      await AsyncStorage.setItem('daily_challenge_data', JSON.stringify(newState));

      setCompleted(true);
      setStreak(newStreak);
      setTotalCompleted(newState.totalCompleted);
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
    } catch {}
  };

  if (!challenge) return null;

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      <View style={s.ruledBg} pointerEvents="none">
        {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
        <View style={s.margin} />
      </View>

      {/* Celebration */}
      {showCelebration && (
        <View style={s.celebration} pointerEvents="none">
          <ConfettiBurst visible={true} count={30} />
          <View style={{ alignItems: 'center' }}>
            <SuccessCheck visible={true} size={90} color={GREEN} />
            <Text style={s.celebrationText}>+{challenge.iq} IQ!</Text>
          </View>
        </View>
      )}

      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={20} color={INK} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>Daily Challenge</Text>
          <Text style={s.subtitle}>Keep the streak alive</Text>
        </View>
        <View style={s.timeLeft}>
          <Ionicons name="time-outline" size={12} color="#EA580C" />
          <Text style={s.timeLeftText}>{timeLeft}</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
        {/* Streak stats */}
        <FadeInView>
          <View style={s.statsRow}>
            <View style={[s.statCard, { borderColor: ORANGE }]}>
              <Ionicons name="flame" size={24} color={ORANGE} />
              <AnimatedCounter value={streak} style={s.statNum} />
              <Text style={s.statLabel}>Day Streak</Text>
            </View>
            <View style={[s.statCard, { borderColor: GREEN }]}>
              <Ionicons name="trophy" size={24} color={GREEN} />
              <AnimatedCounter value={totalCompleted} style={s.statNum} />
              <Text style={s.statLabel}>Total Done</Text>
            </View>
            <View style={[s.statCard, { borderColor: ACCENT }]}>
              <Ionicons name="flash" size={24} color="#EA580C" />
              <AnimatedCounter value={totalCompleted * 50} style={s.statNum} />
              <Text style={s.statLabel}>IQ Earned</Text>
            </View>
          </View>
        </FadeInView>

        {/* Today's challenge card */}
        <FadeInView delay={150}>
          <View style={[s.challengeCard, { borderColor: challenge.color }]}>
            {/* Top tape */}
            <View style={[s.tape, { backgroundColor: challenge.color + '40' }]} />

            {/* Stamp */}
            <View style={[s.todayStamp, { borderColor: completed ? GREEN : '#DC2626' }]}>
              <Text style={[s.todayStampText, { color: completed ? GREEN : '#DC2626' }]}>
                {completed ? 'COMPLETED' : 'TODAY'}
              </Text>
            </View>

            <View style={[s.challengeIconWrap, { backgroundColor: challenge.color + '20' }]}>
              <Ionicons name={challenge.icon} size={36} color={challenge.color} />
            </View>

            <Text style={s.challengeTitle}>{challenge.title}</Text>
            <MarkerUnderline color={challenge.color} width={80} style={{ alignSelf: 'center', marginTop: 8, marginBottom: 14 }} />

            <Text style={s.challengeDesc}>{challenge.task}</Text>

            {/* Reward */}
            <View style={s.rewardRow}>
              <View style={s.reward}>
                <Ionicons name="flash" size={14} color="#EA580C" />
                <Text style={s.rewardText}>+{challenge.iq} IQ</Text>
              </View>
              <View style={s.reward}>
                <Ionicons name="flame" size={14} color={ORANGE} />
                <Text style={s.rewardText}>+1 Streak</Text>
              </View>
            </View>

            {/* Action button */}
            {!completed ? (
              <TouchableOpacity style={[s.completeBtn, { backgroundColor: challenge.color }]} onPress={markComplete}>
                <Ionicons name="checkmark-circle" size={20} color="#fff" />
                <Text style={s.completeBtnText}>Mark as Completed</Text>
              </TouchableOpacity>
            ) : (
              <View style={[s.completedBadge, { borderColor: GREEN }]}>
                <Ionicons name="checkmark-done" size={20} color={GREEN} />
                <Text style={[s.completedBadgeText, { color: GREEN }]}>Completed! Come back tomorrow</Text>
              </View>
            )}
          </View>
        </FadeInView>

        {/* Streak motivation */}
        <FadeInView delay={300}>
          <View style={s.motivCard}>
            <Text style={s.motivTitle}>
              {streak === 0 && '🌱 Start your journey today!'}
              {streak > 0 && streak < 7 && `🔥 ${streak} day${streak > 1 ? 's' : ''} in a row — keep going!`}
              {streak >= 7 && streak < 30 && `🚀 ${streak} day streak! You're on fire!`}
              {streak >= 30 && `👑 ${streak} days — you're a Knowledge Master!`}
            </Text>
            <DoodleDivider style={{ marginVertical: 10 }} />
            <Text style={s.motivDesc}>
              Complete one challenge every day to build your streak. Miss a day and it resets!
            </Text>
          </View>
        </FadeInView>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },
  ruledBg: { ...StyleSheet.absoluteFillObject },
  ruled: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.08)' },
  margin: { position: 'absolute', left: 44, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.10)' },

  header: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 52,
    paddingBottom: 14,
  },
  backBtn: { width: 36, height: 36, borderRadius: 18, borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  subtitle: { fontSize: 12, color: '#8A7558', fontStyle: 'italic' },
  timeLeft: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(234,88,12,0.1)', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6, borderWidth: 1, borderColor: '#EA580C40' },
  timeLeftText: { fontSize: 11, fontWeight: '800', color: '#EA580C' },

  scroll: { paddingHorizontal: 16, paddingTop: 10 },

  statsRow: { flexDirection: 'row', gap: 10, marginBottom: 18 },
  statCard: {
    flex: 1, backgroundColor: '#FFFCF2', borderWidth: 2, borderRadius: 12,
    padding: 14, alignItems: 'center', gap: 4,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  statNum: { fontSize: 22, fontWeight: '900', color: INK },
  statLabel: { fontSize: 9, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase' },

  challengeCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2.5, borderRadius: 18,
    padding: 20, alignItems: 'center', position: 'relative', marginBottom: 18,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },
  tape: { position: 'absolute', top: -10, alignSelf: 'center', width: 80, height: 20, borderRadius: 1, transform: [{ rotate: '-2deg' }] },
  todayStamp: { position: 'absolute', top: 14, right: 14, borderWidth: 2, borderRadius: 3, paddingHorizontal: 8, paddingVertical: 3, transform: [{ rotate: '-3deg' }], opacity: 0.8 },
  todayStampText: { fontSize: 9, fontWeight: '900', letterSpacing: 2 },

  challengeIconWrap: { width: 74, height: 74, borderRadius: 37, justifyContent: 'center', alignItems: 'center', marginTop: 10, marginBottom: 14 },
  challengeTitle: { fontSize: 22, fontWeight: '900', color: INK, textAlign: 'center', letterSpacing: -0.5 },
  challengeDesc: { fontSize: 14, color: '#4A3520', textAlign: 'center', lineHeight: 21, marginBottom: 16, fontFamily: SERIF, fontStyle: 'italic' },

  rewardRow: { flexDirection: 'row', gap: 14, marginBottom: 18 },
  reward: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#F3EACD', borderWidth: 1.5, borderColor: '#C4AA78', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  rewardText: { fontSize: 12, fontWeight: '800', color: INK },

  completeBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 24, paddingVertical: 14, borderRadius: 12, borderWidth: 2, borderColor: INK,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
  },
  completeBtnText: { fontSize: 15, fontWeight: '900', color: '#fff', letterSpacing: 0.5 },
  completedBadge: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, borderWidth: 2, backgroundColor: '#ECFDF5' },
  completedBadgeText: { fontSize: 14, fontWeight: '800' },

  motivCard: { backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#E6D5B8', borderRadius: 12, padding: 16, marginBottom: 20 },
  motivTitle: { fontSize: 14, fontWeight: '800', color: INK, textAlign: 'center' },
  motivDesc: { fontSize: 12, color: '#8A7558', textAlign: 'center', lineHeight: 18, fontStyle: 'italic' },

  celebration: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center', zIndex: 999, backgroundColor: 'rgba(253,246,227,0.9)' },
  celebrationText: { fontSize: 26, fontWeight: '900', color: GREEN, marginTop: 16, letterSpacing: 1 },
});
