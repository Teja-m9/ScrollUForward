import React, { useState, useEffect, useRef, useContext } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
  StatusBar, Platform, KeyboardAvoidingView, Animated, Easing, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext } from '../../App';
import { discussionsAPI } from '../api';
import { PressableCard, FadeInView } from '../components/AnimatedComponents';
import { AnimatedCounter, ProgressRing } from '../components/PremiumAnimations';
import { DoodleDivider, MarkerUnderline, Stamp } from '../components/SketchComponents';

const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const GREEN = '#059669';
const PURPLE = '#7C3AED';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

const DOMAINS_INFO = {
  physics: { icon: 'planet', color: '#EA580C' },
  ai: { icon: 'hardware-chip', color: '#0D9488' },
  space: { icon: 'rocket', color: '#4F46E5' },
  biology: { icon: 'flask', color: '#059669' },
  history: { icon: 'library', color: '#7C3AED' },
  technology: { icon: 'code-slash', color: '#2563EB' },
  nature: { icon: 'leaf', color: '#10B981' },
  mathematics: { icon: 'calculator', color: '#EA580C' },
};

export default function AIStudyBuddyScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const [messages, setMessages] = useState([
    { role: 'ai', text: `Hi ${user?.username || 'there'}! I'm your study buddy. I'll track your progress, identify weak spots, and build custom learning plans.\n\nWhat would you like to learn today?` },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [weakSpots, setWeakSpots] = useState([]);
  const [activePlan, setActivePlan] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const quizHistory = await AsyncStorage.getItem('quiz_history');
        if (quizHistory) {
          const hist = JSON.parse(quizHistory);
          // Analyze weak spots — domains with <70% accuracy
          const domainStats = {};
          hist.forEach(h => {
            if (!domainStats[h.domain]) domainStats[h.domain] = { total: 0, correct: 0, count: 0 };
            domainStats[h.domain].total += h.total;
            domainStats[h.domain].correct += h.score;
            domainStats[h.domain].count += 1;
          });
          const weaks = Object.entries(domainStats).map(([d, s]) => ({
            domain: d, accuracy: Math.round((s.correct / s.total) * 100), attempts: s.count,
          })).filter(w => w.accuracy < 70).sort((a, b) => a.accuracy - b.accuracy);
          setWeakSpots(weaks);
        }
      } catch {}
    })();
  }, []);

  const suggestedPrompts = [
    "Help me understand quantum physics",
    "Create a study plan for AI",
    "What should I focus on today?",
    "Explain black holes simply",
  ];

  const sendMessage = async (textOverride) => {
    const text = (textOverride || input).trim();
    if (!text || sending) return;
    setInput('');
    const newMessages = [...messages, { role: 'user', text }];
    setMessages(newMessages);
    setSending(true);
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);

    try {
      const res = await discussionsAPI.aiChat({
        domain: 'education',
        history: newMessages.slice(-6).map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.text })),
        message: text,
      });
      const reply = res.data?.reply || res.data?.message || "I'm thinking... let me get back to you.";
      setMessages(prev => [...prev, { role: 'ai', text: reply }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', text: "I'm having trouble connecting right now. Try rephrasing or check your connection!" }]);
    } finally {
      setSending(false);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 150);
    }
  };

  const createPlan = (domain) => {
    setActivePlan({
      domain,
      tasks: [
        { label: `Watch 2 reels on ${domain}`, done: false },
        { label: `Take a ${domain} quiz`, done: false },
        { label: `Read 1 article on ${domain}`, done: false },
        { label: `Join a ${domain} discussion`, done: false },
      ],
    });
    setMessages(prev => [...prev, { role: 'ai', text: `Created a ${domain.toUpperCase()} learning plan for you! Check the Study Plan card above. Complete tasks to boost your score.` }]);
  };

  const toggleTask = (idx) => {
    setActivePlan(p => ({
      ...p,
      tasks: p.tasks.map((t, i) => i === idx ? { ...t, done: !t.done } : t),
    }));
  };

  const progress = activePlan ? Math.round((activePlan.tasks.filter(t => t.done).length / activePlan.tasks.length) * 100) : 0;

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />

      {/* Ruled paper bg */}
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
          <Text style={s.title}>Study Buddy <Text style={{ color: BLUE, fontStyle: 'italic' }}>AI</Text></Text>
          <Text style={s.subtitle}>Your personal learning companion</Text>
        </View>
        <View style={s.aiBadge}>
          <Ionicons name="sparkles" size={10} color="#fff" />
          <Text style={s.aiBadgeText}>AI</Text>
        </View>
      </View>

      <ScrollView ref={scrollRef} contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
        {/* Weak Spots */}
        {weakSpots.length > 0 && (
          <FadeInView>
            <View style={s.card}>
              <View style={s.cardHeader}>
                <Ionicons name="warning" size={18} color="#EA580C" />
                <Text style={s.cardTitle}>Your Weak Spots</Text>
              </View>
              <Text style={s.cardDesc}>Based on your quiz history, focus on these areas:</Text>
              {weakSpots.slice(0, 3).map((w, i) => {
                const info = DOMAINS_INFO[w.domain] || { icon: 'help', color: INK };
                return (
                  <View key={i} style={s.weakItem}>
                    <View style={[s.weakIcon, { backgroundColor: info.color + '20' }]}>
                      <Ionicons name={info.icon} size={16} color={info.color} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.weakName}>{w.domain.charAt(0).toUpperCase() + w.domain.slice(1)}</Text>
                      <View style={s.progressBar}>
                        <View style={[s.progressFill, { width: `${w.accuracy}%`, backgroundColor: w.accuracy < 50 ? '#DC2626' : '#EA580C' }]} />
                      </View>
                    </View>
                    <Text style={[s.weakPct, { color: w.accuracy < 50 ? '#DC2626' : '#EA580C' }]}>{w.accuracy}%</Text>
                    <TouchableOpacity style={s.planBtn} onPress={() => createPlan(w.domain)}>
                      <Text style={s.planBtnText}>Plan</Text>
                    </TouchableOpacity>
                  </View>
                );
              })}
            </View>
          </FadeInView>
        )}

        {/* Active Plan */}
        {activePlan && (
          <FadeInView>
            <View style={[s.card, { borderLeftWidth: 4, borderLeftColor: GREEN }]}>
              <View style={s.cardHeader}>
                <Ionicons name="flag" size={18} color={GREEN} />
                <Text style={s.cardTitle}>Study Plan: {activePlan.domain.toUpperCase()}</Text>
              </View>
              <View style={s.planProgressRow}>
                <View style={s.planProgressBar}>
                  <View style={[s.planProgressFill, { width: `${progress}%` }]} />
                </View>
                <Text style={s.planProgressText}>{progress}%</Text>
              </View>
              {activePlan.tasks.map((task, i) => (
                <TouchableOpacity key={i} style={s.taskItem} onPress={() => toggleTask(i)}>
                  <View style={[s.taskCheck, task.done && s.taskCheckDone]}>
                    {task.done && <Ionicons name="checkmark" size={14} color="#fff" />}
                  </View>
                  <Text style={[s.taskLabel, task.done && s.taskLabelDone]}>{task.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </FadeInView>
        )}

        {/* Chat messages */}
        <View style={{ marginTop: 8 }}>
          {messages.map((msg, i) => (
            <View key={i} style={[s.msgRow, msg.role === 'user' && s.msgRowRight]}>
              {msg.role === 'ai' && (
                <View style={s.aiAvatar}>
                  <Ionicons name="sparkles" size={12} color="#fff" />
                </View>
              )}
              <View style={[s.msgBubble, msg.role === 'user' ? s.msgBubbleUser : s.msgBubbleAi]}>
                <Text style={[s.msgText, msg.role === 'user' && { color: '#fff' }]}>{msg.text}</Text>
              </View>
            </View>
          ))}
          {sending && (
            <View style={s.msgRow}>
              <View style={s.aiAvatar}><Ionicons name="sparkles" size={12} color="#fff" /></View>
              <View style={s.msgBubbleAi}>
                <ActivityIndicator size="small" color={INK} />
              </View>
            </View>
          )}
        </View>

        {/* Suggested prompts */}
        {messages.length <= 1 && (
          <View style={s.suggestedWrap}>
            <Text style={s.suggestedLabel}>Try asking:</Text>
            {suggestedPrompts.map((p, i) => (
              <TouchableOpacity key={i} style={s.suggestedChip} onPress={() => sendMessage(p)}>
                <Text style={s.suggestedText}>{p}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View style={{ height: 20 }} />
      </ScrollView>

      {/* Input bar */}
      <View style={s.inputBar}>
        <TextInput
          style={s.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask your study buddy..."
          placeholderTextColor="#8A7558"
          multiline
        />
        <TouchableOpacity
          style={[s.sendBtn, (!input.trim() || sending) && { opacity: 0.4 }]}
          onPress={() => sendMessage()}
          disabled={!input.trim() || sending}
        >
          <Ionicons name="send" size={18} color={INK} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
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
    paddingBottom: 14, borderBottomWidth: 1.5, borderBottomColor: '#E6D5B8',
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
  },
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  subtitle: { fontSize: 11, color: '#8A7558', fontStyle: 'italic' },
  aiBadge: { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: '#7C3AED', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  aiBadgeText: { color: '#fff', fontSize: 10, fontWeight: '900', letterSpacing: 1 },

  scroll: { paddingHorizontal: 16, paddingTop: 16 },
  card: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    padding: 16, marginBottom: 14,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  cardTitle: { fontSize: 15, fontWeight: '800', color: INK, letterSpacing: -0.3 },
  cardDesc: { fontSize: 12, color: '#8A7558', marginBottom: 12, fontStyle: 'italic' },

  weakItem: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: 'rgba(90,150,210,0.08)' },
  weakIcon: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  weakName: { fontSize: 13, fontWeight: '700', color: INK, textTransform: 'capitalize' },
  progressBar: { height: 5, backgroundColor: '#E6D5B8', borderRadius: 3, overflow: 'hidden', marginTop: 4 },
  progressFill: { height: '100%', borderRadius: 3 },
  weakPct: { fontSize: 13, fontWeight: '800' },
  planBtn: { backgroundColor: ACCENT, borderWidth: 1.5, borderColor: INK, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6 },
  planBtnText: { fontSize: 11, fontWeight: '800', color: INK },

  planProgressRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  planProgressBar: { flex: 1, height: 8, backgroundColor: '#E6D5B8', borderRadius: 4, overflow: 'hidden' },
  planProgressFill: { height: '100%', backgroundColor: GREEN, borderRadius: 4 },
  planProgressText: { fontSize: 12, fontWeight: '800', color: GREEN },
  taskItem: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8 },
  taskCheck: { width: 22, height: 22, borderRadius: 6, borderWidth: 2, borderColor: INK, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2' },
  taskCheckDone: { backgroundColor: GREEN, borderColor: GREEN },
  taskLabel: { fontSize: 13, color: INK, flex: 1 },
  taskLabelDone: { textDecorationLine: 'line-through', color: '#8A7558' },

  msgRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 10, gap: 8 },
  msgRowRight: { justifyContent: 'flex-end' },
  aiAvatar: { width: 28, height: 28, borderRadius: 14, backgroundColor: PURPLE, justifyContent: 'center', alignItems: 'center' },
  msgBubble: { maxWidth: '78%', padding: 12, borderRadius: 14 },
  msgBubbleAi: { backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#E6D5B8', borderTopLeftRadius: 4 },
  msgBubbleUser: { backgroundColor: BLUE, borderTopRightRadius: 4 },
  msgText: { fontSize: 14, lineHeight: 20, color: INK },

  suggestedWrap: { marginTop: 10, gap: 8 },
  suggestedLabel: { fontSize: 11, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 },
  suggestedChip: { backgroundColor: 'rgba(37,99,235,0.06)', borderWidth: 1.5, borderColor: BLUE + '30', borderRadius: 18, paddingHorizontal: 12, paddingVertical: 8, alignSelf: 'flex-start' },
  suggestedText: { fontSize: 12, color: BLUE, fontWeight: '600' },

  inputBar: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 10,
    paddingHorizontal: 14, paddingVertical: 10,
    paddingBottom: Platform.OS === 'ios' ? 22 : 10,
    borderTopWidth: 1.5, borderTopColor: INK, backgroundColor: '#FFFCF2',
  },
  input: { flex: 1, minHeight: 40, maxHeight: 100, borderWidth: 1.5, borderColor: '#C4AA78', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10, fontSize: 14, color: INK },
  sendBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, justifyContent: 'center', alignItems: 'center' },
});
