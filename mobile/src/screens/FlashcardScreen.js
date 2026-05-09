import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
  StatusBar, Platform, Dimensions, Animated, Easing, Alert, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { flashcardAPI, contentAPI } from '../api';
import { FadeInView, SuccessCheck } from '../components/AnimatedComponents';
import { AnimatedCounter, ConfettiBurst } from '../components/PremiumAnimations';
import { DoodleDivider, MarkerUnderline, Stamp } from '../components/SketchComponents';

const { width } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const GREEN = '#059669';
const RED = '#DC2626';
const PURPLE = '#7C3AED';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

const SUGGESTED_TOPICS = [
  { label: 'Quantum Physics', icon: 'planet', color: '#EA580C' },
  { label: 'Machine Learning', icon: 'hardware-chip', color: '#0D9488' },
  { label: 'Black Holes', icon: 'rocket', color: '#4F46E5' },
  { label: 'CRISPR Gene Editing', icon: 'flask', color: '#059669' },
  { label: 'Ancient Rome', icon: 'library', color: '#7C3AED' },
  { label: 'Blockchain Basics', icon: 'code-slash', color: '#2563EB' },
  { label: 'Photosynthesis', icon: 'leaf', color: '#10B981' },
  { label: 'Calculus Fundamentals', icon: 'calculator', color: '#EC4899' },
];

export default function FlashcardScreen({ navigation, route }) {
  const [phase, setPhase] = useState('select'); // select, loading, study, results
  const [deck, setDeck] = useState(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState([]);
  const [review, setReview] = useState([]);
  const [customInput, setCustomInput] = useState('');
  const [savedDecks, setSavedDecks] = useState([]);
  const [recentArticles, setRecentArticles] = useState([]);
  const [showCelebration, setShowCelebration] = useState(false);

  // Animations
  const flipAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const cardOpacity = useRef(new Animated.Value(1)).current;
  const cardScale = useRef(new Animated.Value(1)).current;
  const isAnimating = useRef(false);

  useEffect(() => {
    loadSavedDecks();
    loadRecentArticles();
  }, []);

  const loadSavedDecks = async () => {
    try {
      const saved = await AsyncStorage.getItem('flashcard_decks');
      if (saved) setSavedDecks(JSON.parse(saved));
    } catch {}
  };

  const loadRecentArticles = async () => {
    try {
      const res = await contentAPI.list({ content_type: 'article', limit: 5 });
      setRecentArticles(res.data || []);
    } catch {}
  };

  const generateFromText = async (source, topic = '') => {
    setPhase('loading');
    try {
      const res = await flashcardAPI.generate({ source, count: 7, topic });
      const newDeck = {
        id: `deck_${Date.now()}`,
        topic: res.data.topic,
        cards: res.data.cards,
        createdAt: new Date().toISOString(),
      };
      setDeck(newDeck);
      setCurrentIdx(0);
      setKnown([]);
      setReview([]);
      flipAnim.setValue(0);
      slideAnim.setValue(0);
      cardOpacity.setValue(1);
      cardScale.setValue(1);
      setFlipped(false);
      isAnimating.current = false;
      setPhase('study');
      // Save to AsyncStorage
      try {
        const updated = [newDeck, ...savedDecks].slice(0, 20);
        await AsyncStorage.setItem('flashcard_decks', JSON.stringify(updated));
        setSavedDecks(updated);
      } catch {}
    } catch (e) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to generate flashcards. Try again.');
      setPhase('select');
    }
  };

  const loadSavedDeck = (saved) => {
    setDeck(saved);
    setCurrentIdx(0);
    setKnown([]);
    setReview([]);
    flipAnim.setValue(0);
    slideAnim.setValue(0);
    cardOpacity.setValue(1);
    cardScale.setValue(1);
    setFlipped(false);
    isAnimating.current = false;
    setPhase('study');
  };

  const flipCard = () => {
    if (isAnimating.current) return;
    isAnimating.current = true;
    const targetValue = flipped ? 0 : 1;
    setFlipped(f => !f);
    Animated.timing(flipAnim, {
      toValue: targetValue,
      duration: 400,
      easing: Easing.inOut(Easing.cubic),
      useNativeDriver: true,
    }).start(() => { isAnimating.current = false; });
  };

  const swipeAction = (direction) => {
    if (isAnimating.current) return;
    isAnimating.current = true;

    const isKnown = direction === 'right';
    const slideTo = direction === 'right' ? width : -width;
    const nextIdx = currentIdx + 1;
    const isLast = nextIdx >= deck.cards.length;

    // Update tracking arrays immediately
    if (isKnown) setKnown(prev => [...prev, currentIdx]);
    else setReview(prev => [...prev, currentIdx]);

    // Animate current card out
    Animated.parallel([
      Animated.timing(slideAnim, { toValue: slideTo, duration: 280, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      Animated.timing(cardOpacity, { toValue: 0, duration: 280, useNativeDriver: true }),
      Animated.timing(cardScale, { toValue: 0.85, duration: 280, useNativeDriver: true }),
    ]).start(() => {
      if (isLast) {
        // Show results
        setPhase('results');
        isAnimating.current = false;
        if (known.length + (isKnown ? 1 : 0) >= deck.cards.length * 0.7) {
          setShowCelebration(true);
          setTimeout(() => setShowCelebration(false), 2500);
        }
        return;
      }

      // Reset everything for next card BEFORE advancing
      flipAnim.setValue(0);
      setFlipped(false);
      slideAnim.setValue(-40);
      cardOpacity.setValue(0);
      cardScale.setValue(0.9);

      // Advance index
      setCurrentIdx(nextIdx);

      // Animate new card in
      Animated.parallel([
        Animated.timing(slideAnim, { toValue: 0, duration: 280, easing: Easing.out(Easing.back(1.2)), useNativeDriver: true }),
        Animated.timing(cardOpacity, { toValue: 1, duration: 220, useNativeDriver: true }),
        Animated.timing(cardScale, { toValue: 1, duration: 280, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      ]).start(() => { isAnimating.current = false; });
    });
  };

  const restartDeck = () => {
    setCurrentIdx(0);
    setKnown([]);
    setReview([]);
    flipAnim.setValue(0);
    slideAnim.setValue(0);
    cardOpacity.setValue(1);
    cardScale.setValue(1);
    setFlipped(false);
    isAnimating.current = false;
    setPhase('study');
  };

  // ─── SELECT SCREEN ───
  if (phase === 'select') {
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>

        <View style={s.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
            <Ionicons name="arrow-back" size={20} color={INK} />
          </TouchableOpacity>
          <View style={{ flex: 1 }}>
            <Text style={s.title}>Flashcard Generator</Text>
            <Text style={s.subtitle}>AI-powered study cards</Text>
          </View>
          <View style={s.aiBadge}>
            <Ionicons name="sparkles" size={10} color="#fff" />
            <Text style={s.aiBadgeText}>AI</Text>
          </View>
        </View>

        <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
          {/* Hero */}
          <FadeInView>
            <View style={s.heroCard}>
              <View style={s.heroIconWrap}>
                <Text style={{ fontSize: 40 }}>🎴</Text>
              </View>
              <Text style={s.heroTitle}>Create a Study Deck</Text>
              <Text style={s.heroDesc}>Generate flashcards from articles, topics, or any text</Text>
            </View>
          </FadeInView>

          {/* Custom topic input */}
          <FadeInView delay={100}>
            <View style={s.inputCard}>
              <Text style={s.cardLabel}>
                <Ionicons name="create-outline" size={14} color={INK} /> Type a topic or paste text
              </Text>
              <TextInput
                style={s.inputBox}
                value={customInput}
                onChangeText={setCustomInput}
                placeholder="e.g. 'Photosynthesis' or paste an article..."
                placeholderTextColor="#8A7558"
                multiline
                maxLength={2000}
              />
              <TouchableOpacity
                style={[s.genBtn, (!customInput.trim() || customInput.trim().length < 3) && { opacity: 0.5 }]}
                onPress={() => generateFromText(customInput.trim())}
                disabled={!customInput.trim() || customInput.trim().length < 3}
              >
                <Ionicons name="sparkles" size={16} color={INK} />
                <Text style={s.genBtnText}>Generate Flashcards</Text>
              </TouchableOpacity>
            </View>
          </FadeInView>

          {/* Suggested topics */}
          <FadeInView delay={150}>
            <View style={{ marginBottom: 18 }}>
              <Text style={s.sectionLabel}>POPULAR TOPICS</Text>
              <View style={s.topicsGrid}>
                {SUGGESTED_TOPICS.map((t, i) => (
                  <TouchableOpacity
                    key={i}
                    style={[s.topicChip, { borderColor: t.color }]}
                    onPress={() => generateFromText(`Explain ${t.label} in detail with key concepts, examples, and applications`, t.label)}
                  >
                    <Ionicons name={t.icon} size={14} color={t.color} />
                    <Text style={[s.topicText, { color: t.color }]}>{t.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </FadeInView>

          {/* From articles */}
          {recentArticles.length > 0 && (
            <FadeInView delay={200}>
              <View style={{ marginBottom: 18 }}>
                <Text style={s.sectionLabel}>FROM RECENT ARTICLES</Text>
                {recentArticles.slice(0, 3).map((art, i) => (
                  <TouchableOpacity
                    key={i}
                    style={s.articleCard}
                    onPress={() => generateFromText(`Article: ${art.title}\n\n${art.body?.substring(0, 3000) || ''}`, art.title)}
                  >
                    <View style={s.articleIcon}>
                      <Ionicons name="document-text" size={18} color={BLUE} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.articleTitle} numberOfLines={2}>{art.title}</Text>
                      <Text style={s.articleMeta}>{art.domain} · Tap to generate cards</Text>
                    </View>
                    <Ionicons name="arrow-forward" size={16} color="#8A7558" />
                  </TouchableOpacity>
                ))}
              </View>
            </FadeInView>
          )}

          {/* Saved decks */}
          {savedDecks.length > 0 && (
            <FadeInView delay={250}>
              <View style={{ marginBottom: 40 }}>
                <Text style={s.sectionLabel}>YOUR DECKS ({savedDecks.length})</Text>
                {savedDecks.slice(0, 5).map((d, i) => (
                  <TouchableOpacity key={d.id} style={s.savedDeckCard} onPress={() => loadSavedDeck(d)}>
                    <View style={s.deckStack}>
                      <View style={[s.deckCardMini, { transform: [{ rotate: '-4deg' }], zIndex: 1 }]} />
                      <View style={[s.deckCardMini, { transform: [{ rotate: '2deg' }], zIndex: 2 }]} />
                      <View style={[s.deckCardMini, { zIndex: 3, backgroundColor: '#FFFCF2' }]}>
                        <Text style={{ fontSize: 20 }}>🎴</Text>
                      </View>
                    </View>
                    <View style={{ flex: 1, marginLeft: 14 }}>
                      <Text style={s.deckName} numberOfLines={1}>{d.topic}</Text>
                      <Text style={s.deckMeta}>{d.cards.length} cards · {new Date(d.createdAt).toLocaleDateString()}</Text>
                    </View>
                    <TouchableOpacity
                      onPress={(e) => {
                        e.stopPropagation();
                        Alert.alert('Delete Deck?', d.topic, [
                          { text: 'Cancel' },
                          { text: 'Delete', style: 'destructive', onPress: async () => {
                            const updated = savedDecks.filter(x => x.id !== d.id);
                            setSavedDecks(updated);
                            AsyncStorage.setItem('flashcard_decks', JSON.stringify(updated));
                          }},
                        ]);
                      }}
                    >
                      <Ionicons name="trash-outline" size={18} color="#8A7558" />
                    </TouchableOpacity>
                  </TouchableOpacity>
                ))}
              </View>
            </FadeInView>
          )}
        </ScrollView>
      </View>
    );
  }

  // ─── LOADING ───
  if (phase === 'loading') {
    return (
      <View style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>
        <View style={{ alignItems: 'center' }}>
          <View style={s.loadingStack}>
            <View style={[s.loadingCard, { transform: [{ rotate: '-6deg' }] }]} />
            <View style={[s.loadingCard, { transform: [{ rotate: '3deg' }] }]} />
            <View style={[s.loadingCard, { transform: [{ rotate: '-1deg' }] }]}>
              <Text style={{ fontSize: 28 }}>🎴</Text>
            </View>
          </View>
          <Text style={{ fontSize: 18, fontWeight: '900', color: INK, marginTop: 24 }}>Generating Deck...</Text>
          <Text style={{ fontSize: 12, color: '#8A7558', marginTop: 6, fontStyle: 'italic' }}>AI is crafting your flashcards</Text>
          <ActivityIndicator size="small" color={INK} style={{ marginTop: 16 }} />
        </View>
      </View>
    );
  }

  // ─── RESULTS ───
  if (phase === 'results') {
    const total = deck.cards.length;
    const accuracy = Math.round((known.length / total) * 100);
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>

        {showCelebration && (
          <View style={s.celebration} pointerEvents="none">
            <ConfettiBurst visible={true} count={25} />
          </View>
        )}

        <ScrollView contentContainerStyle={{ paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 30 : 70, paddingBottom: 30, paddingHorizontal: 20 }}>
          <FadeInView>
            <View style={s.resultCard}>
              <View style={s.resultStamp}>
                <Text style={s.resultStampText}>COMPLETE</Text>
              </View>

              <Text style={s.resultTitle}>{deck.topic}</Text>
              <MarkerUnderline color={ACCENT} width={100} style={{ alignSelf: 'center', marginTop: 6, marginBottom: 18 }} />

              <View style={s.resultScore}>
                <AnimatedCounter value={accuracy} style={s.resultScoreNum} suffix="%" />
                <Text style={s.resultScoreLabel}>Accuracy</Text>
              </View>

              <View style={s.resultStatsRow}>
                <View style={s.resultStatBox}>
                  <Ionicons name="checkmark-circle" size={20} color={GREEN} />
                  <AnimatedCounter value={known.length} style={[s.resultStatNum, { color: GREEN }]} />
                  <Text style={s.resultStatLabel}>Knew It</Text>
                </View>
                <View style={s.resultStatBox}>
                  <Ionicons name="refresh-circle" size={20} color={RED} />
                  <AnimatedCounter value={review.length} style={[s.resultStatNum, { color: RED }]} />
                  <Text style={s.resultStatLabel}>Review</Text>
                </View>
              </View>

              <DoodleDivider style={{ marginVertical: 14 }} />

              <TouchableOpacity style={s.restartBtn} onPress={restartDeck}>
                <Ionicons name="reload" size={16} color={INK} />
                <Text style={s.restartBtnText}>Study Again</Text>
              </TouchableOpacity>

              {review.length > 0 && (
                <TouchableOpacity
                  style={s.reviewBtn}
                  onPress={() => {
                    setDeck({ ...deck, cards: review.map(i => deck.cards[i]) });
                    restartDeck();
                  }}
                >
                  <Ionicons name="refresh" size={14} color={RED} />
                  <Text style={s.reviewBtnText}>Review {review.length} Missed</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity style={s.newDeckBtn} onPress={() => setPhase('select')}>
                <Text style={s.newDeckBtnText}>Create New Deck</Text>
              </TouchableOpacity>
            </View>
          </FadeInView>
        </ScrollView>
      </View>
    );
  }

  // ─── STUDY SCREEN ───
  const currentCard = deck.cards[currentIdx];
  const frontRotate = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });
  const backRotate = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['180deg', '360deg'] });
  const frontOpacity = flipAnim.interpolate({ inputRange: [0, 0.5, 0.5, 1], outputRange: [1, 1, 0, 0] });
  const backOpacity = flipAnim.interpolate({ inputRange: [0, 0.5, 0.5, 1], outputRange: [0, 0, 1, 1] });

  const diffColor = { easy: GREEN, medium: '#EA580C', hard: RED }[currentCard.difficulty] || INK;

  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
      <View style={s.ruledBg} pointerEvents="none">
        {Array.from({ length: 40 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
        <View style={s.margin} />
      </View>

      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => {
          Alert.alert('Exit Deck?', 'Your progress will be lost', [
            { text: 'Cancel' }, { text: 'Exit', style: 'destructive', onPress: () => setPhase('select') },
          ]);
        }} style={s.backBtn}>
          <Ionicons name="close" size={22} color={INK} />
        </TouchableOpacity>
        <View style={{ flex: 1, alignItems: 'center' }}>
          <Text style={s.studyTopic} numberOfLines={1}>{deck.topic}</Text>
          <Text style={s.studyProgress}>Card {currentIdx + 1} of {deck.cards.length}</Text>
        </View>
        <View style={[s.diffBadge, { borderColor: diffColor }]}>
          <Text style={[s.diffText, { color: diffColor }]}>{currentCard.difficulty.toUpperCase()}</Text>
        </View>
      </View>

      {/* Progress bar */}
      <View style={s.progressBarBg}>
        <View style={[s.progressBarFill, { width: `${((currentIdx + 1) / deck.cards.length) * 100}%` }]} />
      </View>

      {/* Flashcard */}
      <View style={s.cardWrap}>
        <Animated.View style={{
          transform: [{ translateX: slideAnim }, { scale: cardScale }],
          opacity: cardOpacity,
        }}>
          <TouchableOpacity activeOpacity={0.95} onPress={flipCard}>
            <View style={s.cardContainer}>
              {/* Card stack shadow */}
              <View style={[s.cardStackBg, { transform: [{ rotate: '-3deg' }], top: 6 }]} />
              <View style={[s.cardStackBg, { transform: [{ rotate: '2deg' }], top: 3 }]} />

              {/* FRONT — Question */}
              <Animated.View style={[s.card, s.cardFront, {
                transform: [{ perspective: 1000 }, { rotateY: frontRotate }],
                opacity: frontOpacity,
              }]}>
                <View style={s.cardCornerTL} />
                <View style={s.cardCornerBR} />
                <View style={s.cardHoles}>
                  {[0, 1, 2].map(i => <View key={i} style={s.cardHole} />)}
                </View>
                <View style={s.cardLabel}>
                  <Text style={s.cardLabelText}>QUESTION</Text>
                </View>
                <View style={s.cardContent}>
                  <Text style={s.cardQuestion}>{currentCard.front}</Text>
                </View>
                <View style={s.cardFooter}>
                  <Ionicons name="hand-left" size={12} color="#8A7558" />
                  <Text style={s.cardHint}>Tap to flip</Text>
                </View>
              </Animated.View>

              {/* BACK — Answer */}
              <Animated.View style={[s.card, s.cardBack, {
                transform: [{ perspective: 1000 }, { rotateY: backRotate }],
                opacity: backOpacity,
              }]}>
                <View style={[s.cardCornerTL, { borderColor: ACCENT }]} />
                <View style={[s.cardCornerBR, { borderColor: ACCENT }]} />
                <View style={[s.cardLabel, { backgroundColor: ACCENT }]}>
                  <Text style={s.cardLabelText}>ANSWER</Text>
                </View>
                <View style={s.cardContent}>
                  <Text style={s.cardAnswer}>{currentCard.back}</Text>
                </View>
                <View style={s.cardFooter}>
                  <Ionicons name="swap-horizontal" size={12} color="#8A7558" />
                  <Text style={s.cardHint}>Swipe to rate</Text>
                </View>
              </Animated.View>
            </View>
          </TouchableOpacity>
        </Animated.View>
      </View>

      {/* Actions */}
      <View style={s.actions}>
        <TouchableOpacity style={[s.actionBtn, { backgroundColor: '#FEE2E2', borderColor: RED }]} onPress={() => swipeAction('left')}>
          <Ionicons name="close" size={24} color={RED} />
          <Text style={[s.actionText, { color: RED }]}>Review</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.flipBtn} onPress={flipCard}>
          <Ionicons name="reload" size={18} color={INK} />
        </TouchableOpacity>
        <TouchableOpacity style={[s.actionBtn, { backgroundColor: '#ECFDF5', borderColor: GREEN }]} onPress={() => swipeAction('right')}>
          <Ionicons name="checkmark" size={24} color={GREEN} />
          <Text style={[s.actionText, { color: GREEN }]}>Knew It</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },
  ruledBg: { ...StyleSheet.absoluteFillObject },
  ruled: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.06)' },
  margin: { position: 'absolute', left: 44, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)' },

  header: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 52, paddingBottom: 14,
  },
  backBtn: { width: 36, height: 36, borderRadius: 18, borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  subtitle: { fontSize: 11, color: '#8A7558', fontStyle: 'italic' },
  aiBadge: { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: PURPLE, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  aiBadgeText: { color: '#fff', fontSize: 10, fontWeight: '900', letterSpacing: 1 },

  scroll: { paddingHorizontal: 16, paddingBottom: 30 },

  heroCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    padding: 20, alignItems: 'center', marginBottom: 18,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  heroIconWrap: { width: 70, height: 70, borderRadius: 35, backgroundColor: 'rgba(255,214,10,0.15)', justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
  heroTitle: { fontSize: 20, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  heroDesc: { fontSize: 12, color: '#8A7558', textAlign: 'center', marginTop: 4, fontStyle: 'italic' },

  inputCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK, borderRadius: 12,
    padding: 14, marginBottom: 18,
  },
  cardLabel: { fontSize: 11, fontWeight: '800', color: '#8A7558', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 },
  inputBox: { borderWidth: 1.5, borderColor: '#C4AA78', borderRadius: 8, padding: 12, minHeight: 80, fontSize: 14, color: INK, textAlignVertical: 'top', backgroundColor: '#FFFEFC' },
  genBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, paddingVertical: 12, borderRadius: 10, marginTop: 12 },
  genBtnText: { fontSize: 14, fontWeight: '800', color: INK, letterSpacing: 0.5 },

  sectionLabel: { fontSize: 11, fontWeight: '800', color: '#8A7558', letterSpacing: 2, marginBottom: 10, marginTop: 4 },
  topicsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  topicChip: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6 },
  topicText: { fontSize: 12, fontWeight: '700' },

  articleCard: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#E6D5B8', borderRadius: 10, padding: 12, marginBottom: 8 },
  articleIcon: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#EFF6FF', justifyContent: 'center', alignItems: 'center' },
  articleTitle: { fontSize: 13, fontWeight: '700', color: INK },
  articleMeta: { fontSize: 11, color: '#8A7558', marginTop: 2 },

  savedDeckCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#E6D5B8', borderRadius: 10, padding: 12, marginBottom: 8 },
  deckStack: { width: 50, height: 50, justifyContent: 'center', alignItems: 'center' },
  deckCardMini: { position: 'absolute', width: 36, height: 46, backgroundColor: '#F3EACD', borderWidth: 1.5, borderColor: '#C4AA78', borderRadius: 4, justifyContent: 'center', alignItems: 'center' },
  deckName: { fontSize: 14, fontWeight: '800', color: INK },
  deckMeta: { fontSize: 11, color: '#8A7558', marginTop: 2 },

  // ─── Loading ───
  loadingStack: { width: 140, height: 180, alignItems: 'center', justifyContent: 'center' },
  loadingCard: { position: 'absolute', width: 100, height: 140, backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },

  // ─── Study Screen ───
  studyTopic: { fontSize: 15, fontWeight: '900', color: INK, maxWidth: 200 },
  studyProgress: { fontSize: 11, color: '#8A7558', marginTop: 2 },
  diffBadge: { borderWidth: 2, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  diffText: { fontSize: 9, fontWeight: '900', letterSpacing: 1 },

  progressBarBg: { height: 4, backgroundColor: '#E6D5B8', marginHorizontal: 16, borderRadius: 2, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: ACCENT, borderRadius: 2 },

  cardWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 20 },
  cardContainer: { width: width - 40, height: 380, position: 'relative' },
  cardStackBg: { position: 'absolute', width: '100%', height: '100%', backgroundColor: '#F3EACD', borderWidth: 2, borderColor: '#C4AA78', borderRadius: 14, left: 0 },

  card: {
    position: 'absolute', width: '100%', height: '100%',
    backgroundColor: '#FFFCF2', borderWidth: 2.5, borderColor: INK, borderRadius: 14,
    padding: 24, justifyContent: 'space-between', backfaceVisibility: 'hidden',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 10 },
    }),
  },
  cardFront: {},
  cardBack: {},
  cardHoles: { position: 'absolute', left: 8, top: 20, bottom: 20, justifyContent: 'space-between' },
  cardHole: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#E6D5B8', borderWidth: 1, borderColor: '#C4AA78' },
  cardCornerTL: { position: 'absolute', top: 8, left: 8, width: 14, height: 14, borderLeftWidth: 2, borderTopWidth: 2, borderColor: INK },
  cardCornerBR: { position: 'absolute', bottom: 8, right: 8, width: 14, height: 14, borderRightWidth: 2, borderBottomWidth: 2, borderColor: INK },
  cardLabel: { alignSelf: 'center', backgroundColor: INK, paddingHorizontal: 14, paddingVertical: 5, borderRadius: 4, marginTop: 4 },
  cardLabelText: { fontSize: 10, fontWeight: '900', color: '#fff', letterSpacing: 2.5 },
  cardContent: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16 },
  cardQuestion: { fontSize: 22, fontWeight: '800', color: INK, textAlign: 'center', lineHeight: 32, fontFamily: SERIF },
  cardAnswer: { fontSize: 18, color: INK, textAlign: 'center', lineHeight: 28, fontFamily: SERIF, fontStyle: 'italic' },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  cardHint: { fontSize: 10, color: '#8A7558', fontWeight: '600', letterSpacing: 1 },

  actions: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 16, paddingHorizontal: 20, paddingBottom: 30 },
  actionBtn: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4, paddingVertical: 14, borderWidth: 2, borderRadius: 12 },
  actionText: { fontSize: 12, fontWeight: '900', letterSpacing: 1 },
  flipBtn: { width: 48, height: 48, borderRadius: 24, backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, justifyContent: 'center', alignItems: 'center' },

  // ─── Results ───
  resultCard: { backgroundColor: '#FFFCF2', borderWidth: 2.5, borderColor: INK, borderRadius: 16, padding: 24, alignItems: 'center', position: 'relative',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 10 },
    }),
  },
  resultStamp: { position: 'absolute', top: 14, right: 14, borderWidth: 2, borderColor: GREEN, borderRadius: 3, paddingHorizontal: 10, paddingVertical: 4, opacity: 0.6, transform: [{ rotate: '-4deg' }] },
  resultStampText: { fontSize: 9, fontWeight: '900', color: GREEN, letterSpacing: 2 },
  resultTitle: { fontSize: 22, fontWeight: '900', color: INK, marginTop: 8, textAlign: 'center' },
  resultScore: { alignItems: 'center', marginVertical: 14 },
  resultScoreNum: { fontSize: 54, fontWeight: '900', color: INK },
  resultScoreLabel: { fontSize: 12, color: '#8A7558', fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase' },
  resultStatsRow: { flexDirection: 'row', gap: 14, width: '100%' },
  resultStatBox: { flex: 1, backgroundColor: '#F3EACD', borderRadius: 10, padding: 12, alignItems: 'center', gap: 4 },
  resultStatNum: { fontSize: 22, fontWeight: '900' },
  resultStatLabel: { fontSize: 10, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase' },
  restartBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 10 },
  restartBtnText: { fontSize: 14, fontWeight: '800', color: INK },
  reviewBtn: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 10, paddingHorizontal: 14, paddingVertical: 8 },
  reviewBtnText: { fontSize: 12, fontWeight: '700', color: RED },
  newDeckBtn: { marginTop: 10 },
  newDeckBtnText: { fontSize: 12, color: '#8A7558', textDecorationLine: 'underline' },

  celebration: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center', zIndex: 999 },
});
