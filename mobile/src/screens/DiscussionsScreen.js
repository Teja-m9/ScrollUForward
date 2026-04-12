import React, { useState, useContext, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  StatusBar, TextInput, ScrollView, Modal, KeyboardAvoidingView,
  Platform, Dimensions, Alert, Image, ImageBackground, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext, ThemeContext } from '../../App';
import { discussionsAPI } from '../api';
import { Tape, Stamp, DoodleDivider, PaperCorner, StickyNote, SketchSectionHeader } from '../components/SketchComponents';

const { width } = Dimensions.get('window');

const DEMO_DISCUSSIONS = [
  {
    id: 'd1', title: 'The Ethics of AGI Development',
    body: 'Should we pause models larger than GPT-4? What are the real risks of misaligned advanced AI?',
    domain: 'ai', participantCount: 142, messageCount: 890,
    creator_username: 'alice_quantum', created_at: '2 hours ago',
    keywords: ['Ethics', 'AGI', 'Alignment', 'Safety', 'Models'],
    speakers: ['alice_quantum', 'bob_tech', 'neural_nomad'],
  },
  {
    id: 'd2', title: 'New Room-Temp Superconductor Claim',
    body: 'Another paper just dropped on arXiv claiming room temperature superconductivity at ambient pressure.',
    domain: 'physics', participantCount: 350, messageCount: 1200,
    creator_username: 'science_buff', created_at: '5 hours ago',
    keywords: ['Physics', 'Superconductor', 'Materials', 'ArXiv'],
    speakers: ['science_buff', 'quantum_coder'],
  },
  {
    id: 'd3', title: 'Did the Maya Predict Eclipses?',
    body: 'Looking at the Dresden Codex, it seems they had the math worked out centuries before European contact.',
    domain: 'history', participantCount: 84, messageCount: 230,
    creator_username: 'marcus_history', created_at: '1 day ago',
    keywords: ['Maya', 'Astronomy', 'Ancient', 'Eclipse', 'Codex'],
    speakers: ['marcus_history'],
  },
  {
    id: 'd4', title: 'Protein Folding Breakthroughs post-AlphaFold',
    body: 'AlphaFold 3 was just announced. How does this change the landscape for drug discovery?',
    domain: 'biology', participantCount: 210, messageCount: 540,
    creator_username: 'elena_nature', created_at: '2 days ago',
    keywords: ['Biology', 'AlphaFold', 'Protein', 'Drug Discovery'],
    speakers: ['elena_nature', 'bio_hack'],
  },
  {
    id: 'd5', title: 'Quantum Error Correction Progress',
    body: 'Recent breakthroughs in topological qubits look very promising for quantum computing.',
    domain: 'technology', participantCount: 95, messageCount: 320,
    creator_username: 'quantum_coder', created_at: '3 days ago',
    keywords: ['Quantum', 'Qubits', 'Computing', 'Error Correction'],
    speakers: ['quantum_coder'],
  },
];

const DOMAIN_COLORS = {
  physics: '#D35400', nature: '#2ECC71', ai: '#1A9A7A',
  history: '#8E44AD', technology: '#3A5A9C', space: '#3A5A9C',
  biology: '#27AE60', mathematics: '#F39C12', philosophy: '#8E44AD',
  engineering: '#E67E22', chemistry: '#16A085', economics: '#F1C40F',
  psychology: '#E91E63',
};

const DOMAIN_ICONS = {
  ai: 'hardware-chip', physics: 'planet', history: 'library',
  technology: 'code-slash', biology: 'flask', space: 'rocket',
  nature: 'leaf', mathematics: 'calculator', philosophy: 'school',
  engineering: 'construct', chemistry: 'beaker', economics: 'trending-up',
  psychology: 'brain',
};

const INITIAL_MESSAGES = {
  d1: [
    { id: 'm1', username: 'alice_quantum', text: 'I think the alignment problem is harder than we realize. Current RLHF approaches only scratch the surface.', time: '1h ago', isMe: false, likes: 24, replies: [
      { id: 'r1a', username: 'bob_tech', text: 'Agreed, but interpretability is catching up fast.', time: '55m ago', likes: 8 },
      { id: 'r1b', username: 'neural_nomad', text: 'We need better benchmarks for alignment, not just capabilities.', time: '45m ago', likes: 12 },
    ]},
    { id: 'm2', username: 'bob_tech', text: 'But pausing just gives bad actors a lead. We need responsible acceleration.', time: '55m ago', isMe: false, likes: 18, replies: [
      { id: 'r2a', username: 'alice_quantum', text: 'That assumes bad actors are resource-limited, which may not be true.', time: '50m ago', likes: 6 },
    ]},
    { id: 'm3', username: 'neural_nomad', text: 'We need better interpretability tools, not pauses. Mechanistic interpretability is the way forward.', time: '40m ago', isMe: false, likes: 31, replies: [] },
  ],
  d2: [
    { id: 'm1', username: 'science_buff', text: 'The crystal structure looks legit this time. The Meissner effect measurements are clean.', time: '4h ago', isMe: false, likes: 45, replies: [
      { id: 'r1a', username: 'quantum_coder', text: 'Waiting for replication by independent labs before getting excited.', time: '3h ago', likes: 22 },
    ]},
    { id: 'm2', username: 'quantum_coder', text: 'The sample preparation method is the key question here. Can others reproduce it?', time: '3h ago', isMe: false, likes: 38, replies: [] },
  ],
  d3: [
    { id: 'm1', username: 'marcus_history', text: 'Their long count calendar is incredibly precise. The math in the Dresden Codex is genuinely remarkable.', time: '20h ago', isMe: false, likes: 15, replies: [] },
  ],
  d4: [
    { id: 'm1', username: 'elena_nature', text: 'The accuracy improvements in AF3 are staggering. This changes everything for structural biology.', time: '1d ago', isMe: false, likes: 52, replies: [
      { id: 'r1a', username: 'bio_hack', text: 'Drug design pipelines will be completely transformed.', time: '20h ago', likes: 28 },
    ]},
  ],
  d5: [
    { id: 'm1', username: 'quantum_coder', text: 'Microsoft\'s approach to topological qubits is groundbreaking. The error rates are unprecedented.', time: '2d ago', isMe: false, likes: 27, replies: [] },
  ],
};

export default function DiscussionsScreen() {
  const { user } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newBody, setNewBody] = useState('');
  const [newDomain, setNewDomain] = useState('technology');
  const [discussions, setDiscussions] = useState([]);
  const [loadingDisc, setLoadingDisc] = useState(true);
  const [selectedDiscussion, setSelectedDiscussion] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [allMessages, setAllMessages] = useState({});
  const [replyingTo, setReplyingTo] = useState(null);
  const [expandedReplies, setExpandedReplies] = useState({});
  const scrollViewRef = useRef(null);
  const [aiMessageCount, setAiMessageCount] = useState(0);

  const currentMessages = selectedDiscussion ? (allMessages[selectedDiscussion.id] || []) : [];

  // Fetch discussions from API, fallback to demo
  useEffect(() => {
    (async () => {
      setLoadingDisc(true);
      try {
        const res = await discussionsAPI.list({ limit: 20 });
        const apiDiscs = (res.data || []).map(d => ({
          id: d.id, title: d.title, body: d.description || '',
          domain: d.domain || 'technology',
          participantCount: d.participants_count || 0,
          messageCount: d.comments_count || 0,
          creator_username: d.creator_username || 'unknown',
          created_at: d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Recently',
          keywords: [d.domain || 'general'],
          speakers: [d.creator_username || 'unknown'],
        }));
        setDiscussions(apiDiscs);
      } catch {
        setDiscussions([]);
      }
      setLoadingDisc(false);
    })();
  }, []);

  // Load comments when opening a discussion
  useEffect(() => {
    if (!selectedDiscussion) return;
    (async () => {
      try {
        const res = await discussionsAPI.listComments(selectedDiscussion.id);
        const comments = (Array.isArray(res.data) ? res.data : []).map(c => ({
          id: c.id, username: c.username || 'user', text: c.body,
          time: c.created_at ? new Date(c.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '',
          isMe: c.username === (user?.username), likes: c.likes_count || 0, replies: [],
          isAI: c.username === 'ScrollU AI',
        }));
        if (comments.length > 0) {
          setAllMessages(prev => ({ ...prev, [selectedDiscussion.id]: comments }));
        } else if (!allMessages[selectedDiscussion.id]) {
          setAllMessages(prev => ({ ...prev, [selectedDiscussion.id]: [] }));
        }
      } catch {
        if (!allMessages[selectedDiscussion.id]) {
          setAllMessages(prev => ({ ...prev, [selectedDiscussion.id]: INITIAL_MESSAGES[selectedDiscussion.id] || [] }));
        }
      }
    })();
    setAiMessageCount(0);
  }, [selectedDiscussion]);

  useEffect(() => {
    if (scrollViewRef.current && selectedDiscussion) {
      setTimeout(() => scrollViewRef.current?.scrollToEnd?.({ animated: true }), 100);
    }
  }, [currentMessages.length]);

  const handleCreate = () => {
    if (!newTitle.trim() || !newBody.trim()) return;
    const d = {
      id: 'd' + Date.now(), title: newTitle.trim(), body: newBody.trim(),
      domain: newDomain, participantCount: 1, messageCount: 0,
      creator_username: user?.username || 'you', created_at: 'Just now',
      keywords: [newDomain], speakers: [user?.username || 'you'],
    };
    setDiscussions(prev => [d, ...prev]);
    setAllMessages(prev => ({ ...prev, [d.id]: [] }));
    setShowCreateModal(false);
    setNewTitle(''); setNewBody('');
  };

  const [aiTyping, setAiTyping] = useState(false);

  const handleSendReply = async () => {
    if (!replyText.trim()) return;
    const me = user?.username || 'you';
    const userMsg = replyText.trim();
    setReplyText('');

    if (replyingTo) {
      setAllMessages(prev => {
        const msgs = [...(prev[selectedDiscussion.id] || [])];
        const idx = msgs.findIndex(m => m.id === replyingTo);
        if (idx !== -1) {
          msgs[idx] = { ...msgs[idx], replies: [...(msgs[idx].replies || []), { id: 'r' + Date.now(), username: me, text: userMsg, time: 'Just now', likes: 0 }] };
        }
        return { ...prev, [selectedDiscussion.id]: msgs };
      });
      setReplyingTo(null);
    } else {
      setAllMessages(prev => ({
        ...prev,
        [selectedDiscussion.id]: [...(prev[selectedDiscussion.id] || []), {
          id: 'm' + Date.now(), username: me, text: userMsg, time: 'Just now', isMe: true, likes: 0, replies: [],
        }]
      }));
    }

    // ── Persist user message to backend ───────────────────────
    if (selectedDiscussion.id && !selectedDiscussion.id.startsWith('d')) {
      // Only persist for real API-backed discussions (not local demo ones starting with 'd')
      discussionsAPI.addComment(selectedDiscussion.id, { body: userMsg, citation_url: '' })
        .catch(e => console.log('[Discussion] Failed to save user message:', e));
    }

    // AI responds in category rooms always, in custom rooms only on questions or every 3rd msg
    const isCategoryRoom = selectedDiscussion.creator_username === 'ScrollU AI';
    const isQuestion = /\?|how|why|what|explain|tell me|can you/i.test(userMsg);
    const newCount = aiMessageCount + 1;
    setAiMessageCount(newCount);
    const shouldAIRespond = isCategoryRoom || isQuestion || newCount % 3 === 0;

    if (shouldAIRespond) {
      setAiTyping(true);
      try {
        const history = (allMessages[selectedDiscussion.id] || []).slice(-6).map(m => ({
          text: m.text, isAI: m.username === 'ScrollU AI',
        }));
        const res = await discussionsAPI.aiChat({
          message: userMsg,
          topic: selectedDiscussion.title,
          domain: selectedDiscussion.domain,
          history,
          discussion_id: selectedDiscussion.id || '',  // backend persists AI reply
          user_id: user?.user_id || '',
        });
        const aiReply = res.data?.reply || res.data?.message;
        if (aiReply) {
          setAllMessages(prev => ({
            ...prev,
            [selectedDiscussion.id]: [...(prev[selectedDiscussion.id] || []), {
              id: 'ai_' + Date.now(), username: 'ScrollU AI', text: aiReply, time: 'Just now', isMe: false, isAI: true, likes: 0, replies: [],
            }]
          }));
        }
      } catch (e) {
        console.log('AI response failed', e);
      } finally {
        setAiTyping(false);
      }
    }
  };

  const formatCount = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'K' : (n || 0).toString();

  const filteredDiscussions = discussions.filter(d =>
    !searchQuery.trim() || d.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categoryRooms = filteredDiscussions.filter(d => d.creator_username === 'ScrollU AI');
  const customRooms = filteredDiscussions.filter(d => d.creator_username !== 'ScrollU AI');

  // ─── DETAIL VIEW — Chat-style like reference ─────────
  if (selectedDiscussion) {
    const d = selectedDiscussion;
    const dc = DOMAIN_COLORS[d.domain] || '#F9D84A';
    const me = user?.username || 'you';

    const isCategoryRoom = d.creator_username === 'ScrollU AI';
    const domainIcon = DOMAIN_ICONS[d.domain] || 'chatbubbles';

    return (
      <View style={s.container}>
        {/* Notebook ruled lines */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.10)', zIndex: 0 }} pointerEvents="none" />
        <StatusBar barStyle="dark-content" />

        <ScrollView ref={scrollViewRef} style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
          {/* Room Profile Header */}
          <View style={{ backgroundColor: '#FFFCF2' }}>
            {/* Top bar with back button */}
            <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 54, paddingBottom: 12 }}>
              <TouchableOpacity onPress={() => { setSelectedDiscussion(null); setReplyingTo(null); }} style={{ padding: 6, marginRight: 12 }}>
                <Ionicons name="arrow-back" size={24} color="#2C1810" />
              </TouchableOpacity>
              <View style={{ flex: 1 }}>
                <Text style={{ color: '#2C1810', fontSize: 17, fontWeight: '700' }} numberOfLines={1}>{d.title}</Text>
                <Text style={{ color: '#8A7860', fontSize: 12, marginTop: 1 }}>
                  {isCategoryRoom ? 'AI-Powered Room' : `by @${d.creator_username}`}
                </Text>
              </View>
              <TouchableOpacity style={{ padding: 6 }}>
                <Ionicons name="ellipsis-vertical" size={20} color="#8A7860" />
              </TouchableOpacity>
            </View>

            {/* Room info card */}
            <View style={{ marginHorizontal: 16, marginBottom: 12, padding: 14, backgroundColor: '#FFFCF2', borderRadius: 16, borderWidth: 1.5, borderColor: '#2C1810', shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.2, shadowRadius: 0, elevation: 3 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: dc + '20', justifyContent: 'center', alignItems: 'center' }}>
                  <Ionicons name={domainIcon} size={24} color={dc} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: '#2C1810', fontSize: 15, fontWeight: '700' }}>{d.title}</Text>
                  {d.body ? <Text style={{ color: '#8A7860', fontSize: 12, marginTop: 2 }} numberOfLines={2}>{d.body}</Text> : null}
                </View>
              </View>
              <View style={{ flexDirection: 'row', marginTop: 12, gap: 16 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <View style={[s.heroTag, { backgroundColor: dc, paddingHorizontal: 8, paddingVertical: 3 }]}>
                    <Text style={{ color: '#2C1810', fontSize: 10, fontWeight: '700' }}>#{d.domain}</Text>
                  </View>
                </View>
                {isCategoryRoom && (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#7f5af0' + '18', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 }}>
                    <Ionicons name="sparkles" size={11} color="#7f5af0" />
                    <Text style={{ color: '#7f5af0', fontSize: 10, fontWeight: '700' }}>AI Active</Text>
                  </View>
                )}
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Ionicons name="chatbubble-outline" size={12} color="#8A7860" />
                  <Text style={{ color: '#8A7860', fontSize: 11 }}>{formatCount(currentMessages.length)}</Text>
                </View>
              </View>
            </View>
          </View>

          {/* Keywords chips */}
          <View style={s.chipsRow}>
            {(d.keywords || [d.domain]).map((kw, i) => (
              <View key={i} style={[s.kwChip, { borderColor: dc + '40' }]}>
                <Text style={[s.kwChipText, { color: dc }]}>{kw}</Text>
              </View>
            ))}
          </View>

          {/* Chat-style messages */}
          <View style={{ paddingHorizontal: 16, paddingTop: 10, paddingBottom: 20 }}>
            {currentMessages.map((msg) => {
              const isMe = msg.username === me || msg.isMe;
              const isAI = msg.isAI || msg.username === 'ScrollU AI';
              return (
                <View key={msg.id} style={{ marginBottom: 12 }}>
                  {/* Bubble */}
                  <View style={[s.chatBubble, isMe ? s.chatBubbleMe : s.chatBubbleOther, isAI && { backgroundColor: '#7f5af0' + '20', borderColor: '#7f5af0', borderWidth: 1 }]}>
                    {isAI && (
                      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 4 }}>
                        <Ionicons name="sparkles" size={12} color="#7f5af0" />
                        <Text style={{ color: '#7f5af0', fontSize: 11, fontWeight: '700' }}>ScrollU AI</Text>
                      </View>
                    )}
                    <Text style={[s.chatBubbleText, isMe && { color: '#2C1810' }, isAI && { color: '#2C1810' }]}>{msg.text}</Text>
                  </View>

                  {/* Author + time below bubble */}
                  <View style={[s.chatMeta, isMe ? { alignSelf: 'flex-end' } : { alignSelf: 'flex-start' }]}>
                    {!isMe && (
                      <View style={[s.chatMetaAvatar, { backgroundColor: isAI ? '#7f5af0' + '30' : dc + '30' }]}>
                        <Text style={{ color: isAI ? '#7f5af0' : dc, fontSize: 9, fontWeight: '700' }}>{isAI ? 'AI' : msg.username[0].toUpperCase()}</Text>
                      </View>
                    )}
                    <Text style={s.chatMetaUser}>{msg.username}</Text>
                    <Text style={s.chatMetaTime}>{msg.time}</Text>
                  </View>

                  {/* Replies */}
                  {(msg.replies || []).length > 0 && (
                    <TouchableOpacity style={s.chatRepliesBtn} onPress={() => setExpandedReplies(prev => ({ ...prev, [msg.id]: !prev[msg.id] }))}>
                      <Ionicons name={expandedReplies[msg.id] ? 'chevron-up' : 'chevron-down'} size={14} color={dc} />
                      <Text style={[s.chatRepliesBtnText, { color: dc }]}>{msg.replies.length} replies</Text>
                    </TouchableOpacity>
                  )}
                  {expandedReplies[msg.id] && (msg.replies || []).map(r => (
                    <View key={r.id} style={[s.chatBubble, s.chatBubbleReply, { marginLeft: 30, marginTop: 6 }]}>
                      <Text style={s.chatBubbleText}>{r.text}</Text>
                      <View style={[s.chatMeta, { marginTop: 4 }]}>
                        <Text style={s.chatMetaUser}>{r.username}</Text>
                        <Text style={s.chatMetaTime}>{r.time}</Text>
                      </View>
                    </View>
                  ))}

                  {/* Tap to reply */}
                  <TouchableOpacity style={[s.chatReplyTap, isMe ? { alignSelf: 'flex-end' } : { alignSelf: 'flex-start' }]} onPress={() => setReplyingTo(msg.id)}>
                    <Ionicons name="chatbubble-outline" size={12} color="#555" />
                  </TouchableOpacity>
                </View>
              );
            })}
            {currentMessages.length === 0 && (
              <View style={{ alignItems: 'center', paddingVertical: 50 }}>
                <Ionicons name="chatbubble-ellipses-outline" size={40} color="#333" />
                <Text style={{ color: '#8A7860', marginTop: 10 }}>Be the first to speak</Text>
              </View>
            )}
          </View>
        </ScrollView>

        {/* Start Listening / Reply bar */}
        <KeyboardAvoidingView behavior="padding" keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
          <View style={s.replyBar}>
            {/* AI typing indicator */}
            {aiTyping && (
              <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 8, gap: 8 }}>
                <Ionicons name="sparkles" size={14} color="#7f5af0" />
                <Text style={{ color: '#7f5af0', fontSize: 13, fontWeight: '600' }}>ScrollU AI is thinking...</Text>
                <ActivityIndicator size="small" color="#7f5af0" />
              </View>
            )}
            {replyingTo && (
              <View style={s.replyingBanner}>
                <Text style={s.replyingText}>Replying to {currentMessages.find(m => m.id === replyingTo)?.username || '...'}...</Text>
                <TouchableOpacity onPress={() => setReplyingTo(null)}>
                  <Ionicons name="close-circle" size={18} color="#666" />
                </TouchableOpacity>
              </View>
            )}
            <View style={s.replyInputRow}>
              {/* Ask AI button — quick trigger */}
              {selectedDiscussion.creator_username !== 'ScrollU AI' && !replyText.trim() && (
                <TouchableOpacity
                  style={{ paddingHorizontal: 10, paddingVertical: 8, backgroundColor: '#7f5af0' + '20', borderRadius: 16, marginRight: 4 }}
                  onPress={async () => {
                    setAiTyping(true);
                    try {
                      const history = (allMessages[selectedDiscussion.id] || []).slice(-4).map(m => ({ text: m.text, isAI: m.isAI }));
                      const res = await discussionsAPI.aiChat({
                        message: 'Share an interesting insight or fact about this topic',
                        topic: selectedDiscussion.title, domain: selectedDiscussion.domain, history,
                      });
                      const aiReply = res.data?.reply;
                      if (aiReply) {
                        setAllMessages(prev => ({ ...prev, [selectedDiscussion.id]: [...(prev[selectedDiscussion.id] || []), {
                          id: 'ai_' + Date.now(), username: 'ScrollU AI', text: aiReply, time: 'Just now', isMe: false, isAI: true, likes: 0, replies: [],
                        }] }));
                      }
                    } catch {} finally { setAiTyping(false); }
                  }}
                  disabled={aiTyping}
                >
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    <Ionicons name="sparkles" size={14} color="#7f5af0" />
                    <Text style={{ color: '#7f5af0', fontSize: 12, fontWeight: '600' }}>Ask AI</Text>
                  </View>
                </TouchableOpacity>
              )}
              <TextInput
                style={s.replyInput}
                placeholder={selectedDiscussion.creator_username === 'ScrollU AI' ? "Chat with AI..." : "Join the discussion..."}
                placeholderTextColor="#555" value={replyText} onChangeText={setReplyText} multiline
                returnKeyType="send" onSubmitEditing={handleSendReply}
              />
              <TouchableOpacity style={[s.sendBtn, { backgroundColor: replyText.trim() ? '#FFD60A' : '#E0D8C4' }]} onPress={handleSendReply} disabled={aiTyping}>
                <Ionicons name="arrow-up" size={20} color="#2C1810" />
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    );
  }

  // ─── LIST VIEW ─────────────────────────────────────
  return (
    <View style={s.container}>
        {/* Notebook margin */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)', zIndex: 0 }} pointerEvents="none" />
      <StatusBar barStyle="dark-content" />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Hero section — notebook style */}
        <View style={s.hero}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <View style={{ flexDirection: 'row', gap: 4 }}>
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            </View>
            <Ionicons name="chatbubbles" size={20} color="#F9D84A" />
          </View>
          <Text style={s.heroTitle}>Make your learning more{'\n'}<Text style={{ color: '#F9D84A' }}>productive</Text> and collaborative</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 8 }}>
            <View style={{ height: 2.5, backgroundColor: '#F9D84A', width: 50, borderRadius: 2 }} />
            <View style={{ height: 1, backgroundColor: '#C8BFA8', width: 80, marginLeft: 4 }} />
          </View>
        </View>

        <DoodleDivider style={{ marginHorizontal: 20, marginBottom: 8 }} />

        {/* Featured cards — horizontal scroll */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, gap: 12, paddingBottom: 8 }}>
          {/* Tutorial card */}
          <View style={[s.featuredCard, { backgroundColor: '#F0FFF0' }]}>
            <Tape color="green" style={{ right: 15, left: 'auto' }} />
            <Text style={s.featuredCardLabel}>Tutorial</Text>
            <Text style={s.featuredCardTitle}>Discussion{'\n'}Basics</Text>
            <Text style={s.featuredCardDesc}>Quick walkthrough so you can discuss like a pro.</Text>
            <TouchableOpacity style={s.featuredCardBtn}>
              <Text style={s.featuredCardBtnText}>Get Started</Text>
              <Ionicons name="arrow-forward" size={14} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* New Room card */}
          <TouchableOpacity style={[s.featuredCard, { backgroundColor: '#FFFCF2' }]} onPress={() => setShowCreateModal(true)}>
            <Tape color="purple" style={{ left: 20 }} />
            <Text style={s.featuredCardLabel}>Public Room</Text>
            <Text style={s.featuredCardTitle}>Create New{'\n'}Discussion</Text>
            <Text style={s.featuredCardDesc}>Start a room on any topic and invite the community.</Text>
            <View style={s.featuredCardBtn}>
              <Text style={s.featuredCardBtnText}>Go</Text>
              <Ionicons name="chevron-forward" size={14} color="#2C1810" />
            </View>
          </TouchableOpacity>
        </ScrollView>

        {/* Search */}
        <View style={s.searchWrap}>
          <View style={s.searchBar}>
            <Ionicons name="search" size={18} color="#555" />
            <TextInput style={s.searchInput} placeholder="Search discussions..." placeholderTextColor="#555"
              value={searchQuery} onChangeText={setSearchQuery} />
          </View>
        </View>

        {/* AI-Powered Category Rooms */}
        {categoryRooms.length > 0 && (
          <>
            <SketchSectionHeader title="AI-Powered Rooms" color="#7f5af0" />
            {categoryRooms.map(item => {
              const dc = DOMAIN_COLORS[item.domain] || '#F9D84A';
              return (
                <TouchableOpacity key={item.id} style={s.meetingCard} onPress={() => { setSelectedDiscussion(item); setExpandedReplies({}); setAiMessageCount(0); }}>
                  <View style={[s.meetingIcon, { backgroundColor: dc + '18' }]}>
                    <Ionicons name={DOMAIN_ICONS[item.domain] || 'chatbubbles'} size={20} color={dc} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Text style={s.meetingTitle} numberOfLines={1}>{item.title}</Text>
                    </View>
                    <View style={s.meetingMeta}>
                      <Ionicons name="sparkles" size={12} color="#7f5af0" />
                      <Text style={[s.meetingMetaText, { color: '#7f5af0' }]}>AI-Powered</Text>
                      <Text style={s.meetingMetaDot}>·</Text>
                      <Ionicons name="chatbubbles-outline" size={12} color="#777" />
                      <Text style={s.meetingMetaText}>{formatCount(item.messageCount)}</Text>
                    </View>
                  </View>
                  <View style={[s.liveDot, { backgroundColor: '#7f5af0' + '20' }]}><View style={[s.liveDotInner, { backgroundColor: '#7f5af0' }]} /></View>
                </TouchableOpacity>
              );
            })}
          </>
        )}

        {/* Custom Discussion Rooms */}
        {customRooms.length > 0 && (
          <>
            <SketchSectionHeader title="Community Rooms" />
            {customRooms.map(item => (
              <TouchableOpacity key={item.id} style={s.meetingCard} onPress={() => { setSelectedDiscussion(item); setExpandedReplies({}); setAiMessageCount(0); }}>
                <View style={[s.meetingIcon, { backgroundColor: (DOMAIN_COLORS[item.domain] || '#F9D84A') + '18' }]}>
                  <Ionicons name={DOMAIN_ICONS[item.domain] || 'chatbubbles'} size={20} color={DOMAIN_COLORS[item.domain] || '#F9D84A'} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.meetingTitle} numberOfLines={1}>{item.title}</Text>
                  <View style={s.meetingMeta}>
                    <Ionicons name="person-outline" size={12} color="#777" />
                    <Text style={s.meetingMetaText}>@{item.creator_username}</Text>
                    <Text style={s.meetingMetaDot}>·</Text>
                    <Ionicons name="chatbubbles-outline" size={12} color="#777" />
                    <Text style={s.meetingMetaText}>{formatCount(item.messageCount)}</Text>
                  </View>
                </View>
                <Text style={s.meetingTime}>{item.created_at}</Text>
              </TouchableOpacity>
            ))}
          </>
        )}

        {filteredDiscussions.length === 0 && !loadingDisc && (
          <View style={{ height: 280, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '2deg' }], marginBottom: 16 }}>
              <Ionicons name="chatbubbles-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>No discussions yet</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>The forum is quiet! Start a discussion and spark a great conversation.</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        )}
      </ScrollView>

      {/* FAB */}
      <TouchableOpacity style={s.fab} onPress={() => setShowCreateModal(true)}>
        <Ionicons name="add" size={26} color="#2C1810" />
      </TouchableOpacity>

      {/* Create Modal */}
      <Modal visible={showCreateModal} animationType="slide" transparent>
        <View style={s.modalOverlay}>
          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={s.modalContent}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Create Discussion</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#2C1810" />
              </TouchableOpacity>
            </View>

            <Text style={s.modalLabel}>Topic</Text>
            <TextInput style={s.modalInput} placeholder="What do you want to discuss?" placeholderTextColor="#555"
              value={newTitle} onChangeText={setNewTitle} />

            <Text style={[s.modalLabel, { marginTop: 16 }]}>Domain</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }}>
              {Object.keys(DOMAIN_COLORS).map(domain => (
                <TouchableOpacity key={domain}
                  style={[s.domainChip, newDomain === domain && { backgroundColor: DOMAIN_COLORS[domain] + '25', borderColor: DOMAIN_COLORS[domain] }]}
                  onPress={() => setNewDomain(domain)}>
                  <Text style={[s.domainChipText, newDomain === domain && { color: DOMAIN_COLORS[domain] }]}>{domain}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <Text style={s.modalLabel}>Opening Message</Text>
            <TextInput style={s.modalTextarea} placeholder="Share your thoughts..."
              placeholderTextColor="#555" multiline textAlignVertical="top"
              value={newBody} onChangeText={setNewBody} />

            <View style={s.modalActions}>
              <TouchableOpacity style={s.modalBtnCancel} onPress={() => setShowCreateModal(false)}>
                <Text style={{ color: '#2C1810', fontWeight: '600' }}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.modalBtnCreate} onPress={handleCreate}>
                <Text style={{ color: '#2C1810', fontWeight: '700' }}>Create Room</Text>
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Hero
  hero: { paddingHorizontal: 20, paddingTop: 54, paddingBottom: 20 },
  heroTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#2C1810', lineHeight: 36, letterSpacing: -0.5 },

  // Featured cards — sketch style with yellow top bar
  featuredCard: { width: width * 0.6, padding: 20, justifyContent: 'space-between', minHeight: 180, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, borderTopWidth: 5, borderTopColor: '#F9D84A', ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  featuredCardLabel: { fontSize: 11, color: '#8A7860', fontWeight: '700', letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 8 },
  featuredCardTitle: { fontSize: 22, fontWeight: '700', color: '#2C1810', lineHeight: 28, marginBottom: 8 },
  featuredCardDesc: { fontSize: 12, color: '#8A7860', lineHeight: 18, marginBottom: 14 },
  featuredCardBtn: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', backgroundColor: '#F9D84A', paddingHorizontal: 14, paddingVertical: 8, gap: 4, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 },
  featuredCardBtnText: { fontSize: 13, fontWeight: '700', color: '#2C1810' },

  // Search — sketch style
  searchWrap: { paddingHorizontal: 16, paddingVertical: 12 },
  searchBar: { flexDirection: 'row', alignItems: 'center', height: 44, paddingHorizontal: 16, gap: 8, backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 3 } }) },
  searchInput: { flex: 1, fontSize: 14, color: '#2C1810' },

  // Section titles
  sectionTitle: { fontSize: 11, fontWeight: '700', color: '#8A7860', letterSpacing: 1.2, paddingHorizontal: 20, marginTop: 16, marginBottom: 12 },

  // Meeting-style card — sketch bordered items
  meetingCard: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 10, paddingHorizontal: 14, paddingVertical: 14, gap: 14, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, backgroundColor: '#FFFCF2', ...Platform.select({ ios: { shadowColor: '#B8AE90', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 2 } }) },
  meetingIcon: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },
  meetingTitle: { fontSize: 15, fontWeight: '600', color: '#2C1810', marginBottom: 4 },
  meetingMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  meetingMetaText: { fontSize: 12, color: '#8A7860' },
  meetingMetaDot: { color: '#8A7860', fontSize: 12 },
  meetingTime: { fontSize: 11, color: '#8A7860' },
  liveDot: { marginTop: 6, alignItems: 'center' },
  liveDotInner: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#F9D84A' },

  // FAB — sketch style asymmetric
  fab: { position: 'absolute', bottom: 24, right: 20, width: 56, height: 56, backgroundColor: '#FFD60A', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 14, borderBottomLeftRadius: 14, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 6 } }) },

  // ─── DETAIL VIEW ──────────────────
  detailHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 54, paddingBottom: 12, gap: 12 },
  headerBtn: { padding: 6 },

  detailDomainBadge: { alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 5, borderRadius: 10, marginBottom: 12 },
  detailDomainText: { fontSize: 12, fontWeight: '700' },

  detailTitle: { fontSize: 24, fontWeight: '900', color: '#2C1810', lineHeight: 32, paddingHorizontal: 20, marginBottom: 12, letterSpacing: -0.5 },

  detailMeta: { flexDirection: 'row', gap: 16, paddingHorizontal: 20, marginBottom: 20 },
  detailMetaItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  detailMetaText: { fontSize: 12, color: '#8A7860' },

  // Keywords
  keywordsSection: { paddingHorizontal: 20, marginBottom: 20 },
  sectionLabel: { fontSize: 10, fontWeight: '700', color: '#8A7860', letterSpacing: 1, marginBottom: 10 },
  keywordsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  keywordChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 14, borderWidth: 1, backgroundColor: '#F8F6F0' },
  keywordText: { fontSize: 12, fontWeight: '600' },

  // Speakers
  speakersSection: { paddingHorizontal: 20, marginBottom: 20 },
  speakersRow: { flexDirection: 'row', gap: 16 },
  speakerItem: { alignItems: 'center', gap: 6 },
  speakerAvatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  speakerAvatarText: { fontSize: 16, fontWeight: '700' },
  speakerName: { fontSize: 11, color: '#8A7860', maxWidth: 70, textAlign: 'center' },

  // Divider
  divider: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, marginBottom: 16, gap: 10 },
  dividerLine: { flex: 1, height: 0.5, backgroundColor: '#C8BFA8' },
  dividerText: { fontSize: 12, fontWeight: '600', color: '#8A7860' },

  // Messages
  msgCard: { backgroundColor: '#F8F6F0', borderRadius: 16, padding: 14, marginBottom: 10, borderWidth: 1.5, borderColor: '#E6D5B8' },
  timestampPill: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8, marginBottom: 10 },
  timestampText: { fontSize: 11, fontWeight: '700' },
  msgHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  msgAvatar: { width: 30, height: 30, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  msgAvatarText: { fontSize: 13, fontWeight: '700' },
  msgUsername: { fontSize: 13, fontWeight: '600', color: '#2C1810' },
  youBadge: { backgroundColor: '#F9D84A30', paddingHorizontal: 6, paddingVertical: 1, borderRadius: 4 },
  youBadgeText: { fontSize: 9, fontWeight: '700', color: '#8A7860' },
  msgText: { fontSize: 14, lineHeight: 22, color: '#5A4A30', marginBottom: 10 },
  msgActions: { flexDirection: 'row', gap: 16, paddingTop: 8, borderTopWidth: 0.5, borderTopColor: '#C8BFA8' },
  msgAction: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  msgActionText: { fontSize: 11, color: '#8A7860', fontWeight: '500' },

  // Nested replies
  replyRow: { flexDirection: 'row', marginLeft: 16, marginTop: 8 },
  replyLine: { width: 2, borderRadius: 1, marginRight: 10 },
  replyContent: { flex: 1, backgroundColor: '#FFFCF2', borderRadius: 12, padding: 10 },
  replyHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  replyAvatar: { width: 22, height: 22, borderRadius: 11, justifyContent: 'center', alignItems: 'center' },
  replyAvatarText: { fontSize: 10, fontWeight: '700' },
  replyUsername: { fontSize: 11, fontWeight: '600', color: '#5A4A30' },
  replyTime: { fontSize: 10, color: '#8A7860' },
  replyText: { fontSize: 13, lineHeight: 19, color: '#8A7860' },

  // Reply bar
  replyBar: { borderTopWidth: 0.5, borderTopColor: '#F8F6F0', backgroundColor: '#FFFCF2', paddingBottom: 30 },
  replyingBanner: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#FFFCF2' },
  replyingText: { fontSize: 12, color: '#D35400', fontWeight: '500' },
  replyInputRow: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 12, paddingVertical: 10, gap: 10 },
  replyInput: { flex: 1, minHeight: 42, maxHeight: 100, borderWidth: 2, borderColor: '#2C1810', backgroundColor: '#FFFCF2', paddingHorizontal: 16, paddingTop: 10, paddingBottom: 10, fontSize: 14, color: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },
  sendBtn: { width: 42, height: 42, justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#FFFCF2', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 40 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, paddingBottom: 12, borderBottomWidth: 0.5, borderBottomColor: '#C8BFA8' },
  modalTitle: { fontSize: 20, fontWeight: '700', color: '#2C1810' },
  modalLabel: { fontSize: 13, fontWeight: '600', marginBottom: 8, color: '#8A7860' },
  modalInput: { height: 48, borderWidth: 1.5, paddingHorizontal: 14, fontSize: 15, borderColor: '#2C1810', color: '#2C1810', backgroundColor: '#FFFCF2', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },
  modalTextarea: { height: 120, borderWidth: 1.5, paddingHorizontal: 14, paddingTop: 14, fontSize: 15, borderColor: '#2C1810', color: '#2C1810', backgroundColor: '#FFFCF2', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },
  domainChip: { paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1.5, marginRight: 8, borderColor: '#2C1810', backgroundColor: '#FFFCF2', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 },
  domainChipText: { fontSize: 12, fontWeight: '500', textTransform: 'capitalize', color: '#8A7860' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 24 },
  modalBtnCancel: { flex: 1, height: 48, justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },
  modalBtnCreate: { flex: 1, height: 48, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F9D84A', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3 },

  // ─── Detail Hero (chat-style) ──────────
  heroSection: { paddingBottom: 16, minHeight: 260, justifyContent: 'flex-end' },
  heroBgImg: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%', opacity: 0.25 },
  heroDarkOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(10,10,10,0.6)' },
  heroHeader: { position: 'absolute', top: 54, left: 16, right: 16, flexDirection: 'row', alignItems: 'center', zIndex: 5 },
  heroBackBtn: { padding: 4 },
  heroTagRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 20, marginBottom: 10 },
  heroTag: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  heroTagText: { fontSize: 11, fontWeight: '700', color: '#2C1810' },
  heroStatPill: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(255,255,255,0.12)', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10 },
  heroStatText: { fontSize: 11, color: '#5A4A30', fontWeight: '600' },
  creatorPill: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(255,255,255,0.12)', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 14 },
  creatorAvatar: { width: 22, height: 22, borderRadius: 11, justifyContent: 'center', alignItems: 'center' },
  creatorName: { fontSize: 11, color: '#EEE', fontWeight: '600' },
  heroTitle: { fontSize: 24, fontWeight: '800', color: '#2C1810', lineHeight: 32, paddingHorizontal: 20, fontStyle: 'italic' },

  // Keywords chips
  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingHorizontal: 20, paddingVertical: 14 },
  kwChip: { paddingHorizontal: 12, paddingVertical: 5, borderWidth: 2, borderColor: '#2C1810', backgroundColor: '#FFFCF2', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 },
  kwChipText: { fontSize: 12, fontWeight: '600' },

  // Chat bubbles
  chatBubble: { maxWidth: '85%', borderRadius: 16, padding: 12 },
  chatBubbleMe: { alignSelf: 'flex-end', backgroundColor: '#F9D84A', borderBottomRightRadius: 4 },
  chatBubbleOther: { alignSelf: 'flex-start', backgroundColor: '#F8F6F0', borderBottomLeftRadius: 4 },
  chatBubbleReply: { backgroundColor: '#FFFCF2', borderRadius: 12 },
  chatBubbleText: { fontSize: 14, lineHeight: 21, color: '#2C1810' },
  chatMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4, paddingHorizontal: 4 },
  chatMetaAvatar: { width: 18, height: 18, borderRadius: 9, justifyContent: 'center', alignItems: 'center' },
  chatMetaUser: { fontSize: 11, fontWeight: '600', color: '#8A7860' },
  chatMetaTime: { fontSize: 10, color: '#8A7860' },
  chatRepliesBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, marginLeft: 10, marginTop: 4 },
  chatRepliesBtnText: { fontSize: 11, fontWeight: '600' },
  chatReplyTap: { marginTop: 2, padding: 4 },
});
