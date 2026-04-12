import React, { useState, useRef, useCallback, useContext, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, Dimensions, TouchableOpacity,
  StatusBar, Modal, TextInput, KeyboardAvoidingView, Platform,
  Alert, ScrollView, Image, ActivityIndicator, Animated, Linking, PanResponder, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { contentAPI } from '../api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext } from '../../App';
import { ThemeContext } from '../../App';
import * as ImagePicker from 'expo-image-picker';
import { WebView } from 'react-native-webview';
import { Tape, Stamp, DoodleDivider, PaperCorner, PencilLine, StickerBadge, MarkerUnderline } from '../components/SketchComponents';
let Video = null;
let ResizeMode = {};
try {
  const av = require('expo-av');
  Video = av.Video;
  ResizeMode = av.ResizeMode || {};
} catch (e) {
  // expo-av not available — story videos will show as images
}

const { width, height } = Dimensions.get('window');
const STORIES_HEIGHT = 80;

const DOMAIN_COLORS = {
  physics: '#F97316', nature: '#10B981', ai: '#14B8A6',
  history: '#8B5CF6', technology: '#3B82F6', space: '#6366F1',
  biology: '#10B981', mathematics: '#F97316',
};
const DOMAIN_ICONS = {
  physics: 'planet', nature: 'leaf', ai: 'hardware-chip',
  history: 'library', technology: 'code-slash', space: 'rocket',
  biology: 'flask', mathematics: 'calculator',
};

const OWN_STORY_PLACEHOLDER = { id: 'your_story', username: 'Your story', isOwn: true, hasStory: false, color: '#FFD60A' };


export default function ReelsScreen({ navigation }) {
  const { user, openChat } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);

  const [reels, setReels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const [likes, setLikes] = useState({});
  const [saves, setSaves] = useState({});
  const [pausedReels, setPausedReels] = useState({});
  const [mutedReels, setMutedReels] = useState({});
  const [fullscreen, setFullscreen] = useState(false);
  const [videoProgress, setVideoProgress] = useState({});
  const [fsPaused, setFsPaused] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const exitFullscreen = () => {
    // Stop fullscreen video immediately
    const fsRef = webViewRefs.current['fs_active'];
    if (fsRef) try { fsRef.postMessage('stop'); } catch {}
    setFsPaused(false);
    setFullscreen(false);
    // Restart current main reel from beginning after modal closes
    setTimeout(() => {
      const mainRef = webViewRefs.current[reels[activeIndex]?.id];
      if (mainRef) {
        try {
          mainRef.postMessage('stop');
          setTimeout(() => mainRef.postMessage('play'), 200);
        } catch {}
      }
    }, 300);
  };
  const webViewRefs = useRef({});
  const pauseAnim = useRef(new Animated.Value(0)).current;
  const [showStory, setShowStory] = useState(null);
  const [storyIndex, setStoryIndex] = useState(0);
  const [stories, setStories] = useState([OWN_STORY_PLACEHOLDER]);
  const storyTimerRef = useRef(null);
  const [commentModalReel, setCommentModalReel] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

  // Double-tap like animation
  const [heartAnimId, setHeartAnimId] = useState(null);
  const heartScale = useRef(new Animated.Value(0)).current;
  const lastTapRef = useRef({});
  const handleDoubleTap = (item, index) => {
    const hasVideo = item.media_url && !item.media_url.startsWith('blob:') && (item.media_url.includes('amazonaws') || item.media_url.includes('s3') || item.media_url.match(/\.(mp4|mov|webm|avi)($|\?)/i));
    const now = Date.now();
    const lastTap = lastTapRef.current[item.id] || 0;
    if (now - lastTap < 300) {
      // Double tap detected — like + animate
      if (!likes[item.id]) toggleLike(item.id);
      setHeartAnimId(item.id);
      heartScale.setValue(0);
      Animated.sequence([
        Animated.spring(heartScale, { toValue: 1, friction: 3, tension: 100, useNativeDriver: true }),
        Animated.delay(400),
        Animated.timing(heartScale, { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start(() => setHeartAnimId(null));
    } else {
      lastTapRef.current[item.id] = now;
      // Single tap — only open fullscreen for VIDEO reels
      if (hasVideo) {
        setTimeout(() => {
          if (Date.now() - lastTapRef.current[item.id] >= 280) {
            setActiveIndex(index);
            setFsPaused(false);
            setFullscreen(true);
          }
        }, 300);
      }
      // For image/quote posts — do nothing on single tap (actions are inline)
    }
  };

  // Create Reel state
  const [showCreateReel, setShowCreateReel] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createBody, setCreateBody] = useState('');
  const [createDomain, setCreateDomain] = useState('technology');
  const [createMediaUri, setCreateMediaUri] = useState(null);
  const [publishingReel, setPublishingReel] = useState(false);

  useEffect(() => { fetchReels(); fetchStories(); }, []);

  const fetchReels = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      // Fetch all content types — reels, images, quotes, articles
      const res = await contentAPI.list({ limit: 30 });
      const shuffled = (res.data || []).sort(() => Math.random() - 0.5);
      setReels(shuffled);
    } catch (e) { console.log('Failed to fetch reels', e); }
    finally { if (!silent) setLoading(false); }
  };

  const fetchStories = async () => {
    try {
      const res = await contentAPI.list({ content_type: 'story', limit: 20 });
      if (res.data && res.data.length > 0) {
        const now = Date.now();
        const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
        const apiStories = res.data
          .filter(s => {
            if (!s.created_at) return false;
            return (now - new Date(s.created_at).getTime()) < TWENTY_FOUR_HOURS;
          })
          .map((s, i) => ({
            id: s.id || `api_${i}`,
            username: s.author_username || 'unknown',
            hasStory: true,
            color: DOMAIN_COLORS[s.domain] || '#F9D84A',
            viewed: false,
            content: s.story_content || null,
          }));
        setStories([OWN_STORY_PLACEHOLDER, ...apiStories]);
      }
    } catch (e) {
      console.log('Stories API unavailable');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchReels(true), fetchStories()]);
    setRefreshing(false);
  };

  // Story auto-progress timer
  const STORY_DURATION = 5000; // 5 seconds per story slide
  const progressAnim = useRef(new Animated.Value(0)).current;

  const startStoryTimer = useCallback((index) => {
    if (storyTimerRef.current) clearTimeout(storyTimerRef.current);
    progressAnim.setValue(0);
    Animated.timing(progressAnim, {
      toValue: 1,
      duration: STORY_DURATION,
      useNativeDriver: false,
    }).start();
    storyTimerRef.current = setTimeout(() => {
      const storyContent = getStoryContent(showStory);
      if (index < storyContent.length - 1) {
        setStoryIndex(index + 1);
      } else {
        setShowStory(null);
      }
    }, STORY_DURATION);
  }, [showStory, progressAnim]);

  useEffect(() => {
    if (showStory) {
      startStoryTimer(storyIndex);
    } else {
      if (storyTimerRef.current) clearTimeout(storyTimerRef.current);
      progressAnim.setValue(0);
    }
    return () => { if (storyTimerRef.current) clearTimeout(storyTimerRef.current); };
  }, [showStory, storyIndex]);

  // Swipe-down to close story
  const storyPan = useRef(new Animated.ValueXY()).current;
  const storyOpacity = useRef(new Animated.Value(1)).current;
  const storyPanResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (_, gestureState) => gestureState.dy > 10 && Math.abs(gestureState.dy) > Math.abs(gestureState.dx),
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy > 0) {
          storyPan.setValue({ x: 0, y: gestureState.dy });
          storyOpacity.setValue(1 - gestureState.dy / 400);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dy > 120) {
          Animated.parallel([
            Animated.timing(storyPan, { toValue: { x: 0, y: height }, duration: 200, useNativeDriver: true }),
            Animated.timing(storyOpacity, { toValue: 0, duration: 200, useNativeDriver: true }),
          ]).start(() => {
            setShowStory(null);
            storyPan.setValue({ x: 0, y: 0 });
            storyOpacity.setValue(1);
          });
        } else {
          Animated.parallel([
            Animated.spring(storyPan, { toValue: { x: 0, y: 0 }, useNativeDriver: true }),
            Animated.timing(storyOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
          ]).start();
        }
      },
    })
  ).current;

  // Get story content for a given story user
  const getStoryContent = (story) => {
    if (!story) return [];
    if (story.content && Array.isArray(story.content) && story.content.length > 0) return story.content;
    // Fallback: show a single placeholder slide
    return [{ text: 'No story content available.', bg: story.color || '#333', domain: null, mediaType: null, mediaUri: null }];
  };

  const handleCamera = () => {
    Alert.alert('Create', 'What would you like to create?', [
      { text: 'Story', onPress: handleCreateStory },
      { text: 'Reel / Video', onPress: () => setShowCreateReel(true) },
      { text: 'Image Post', onPress: handleCreateImagePost },
      { text: 'Quote / Text', onPress: () => setShowCreateReel(true) },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const handleCreateImagePost = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: true, quality: 0.9 });
    if (!result.canceled && result.assets?.length > 0) {
      setCreateMediaUri(result.assets[0].uri);
      setShowCreateReel(true);
    }
  };

  const handleCreateStory = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images', 'videos'], allowsEditing: true, quality: 1 });
    if (!result.canceled && result.assets?.length > 0) {
      const asset = result.assets[0];
      const isVideo = asset.type === 'video' || (asset.uri && asset.uri.match(/\.(mp4|mov|avi|mkv)$/i));
      const storySlide = {
        mediaUri: asset.uri,
        mediaType: isVideo ? 'video' : 'image',
        text: '',
        bg: '#000',
      };
      // Save locally and update own story
      try {
        const existing = await AsyncStorage.getItem('my_stories');
        const myStories = existing ? JSON.parse(existing) : [];
        myStories.push({ ...storySlide, createdAt: Date.now() });
        // Keep only last 24h stories
        const cutoff = Date.now() - 24 * 60 * 60 * 1000;
        const filtered = myStories.filter(s => s.createdAt > cutoff);
        await AsyncStorage.setItem('my_stories', JSON.stringify(filtered));
      } catch {}
      setStories(prev => prev.map(s => s.id === 'your_story'
        ? { ...s, hasStory: true, content: [...(s.content || []), storySlide] }
        : s
      ));
      Alert.alert('Story Posted!', 'Your story has been shared.');
    }
  };

  // Load own stories from AsyncStorage on mount
  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem('my_stories');
        if (saved) {
          const myStories = JSON.parse(saved);
          const cutoff = Date.now() - 24 * 60 * 60 * 1000;
          const valid = myStories.filter(s => s.createdAt > cutoff);
          if (valid.length > 0) {
            setStories(prev => prev.map(s => s.id === 'your_story'
              ? { ...s, hasStory: true, content: valid }
              : s
            ));
          }
        }
      } catch {}
    })();
  }, []);

  const pickReelMedia = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['videos', 'images'], allowsEditing: true, quality: 0.8 });
    if (!result.canceled && result.assets?.length > 0) {
      setCreateMediaUri(result.assets[0].uri);
    }
  };

  const resetCreateReel = () => {
    setCreateTitle(''); setCreateBody(''); setCreateDomain('technology');
    setCreateMediaUri(null); setPublishingReel(false);
  };

  const handlePublishReel = async () => {
    if (!createTitle.trim()) { Alert.alert('Missing title', 'Please enter a title for your reel.'); return; }
    if (!createBody.trim() || createBody.trim().length < 50) { Alert.alert('Missing content', 'Please write at least 50 characters of content.'); return; }
    setPublishingReel(true);
    try {
      const reelData = {
        content_type: 'reel',
        title: createTitle.trim(),
        body: createBody.trim(),
        domain: createDomain,
        thumbnail_url: createMediaUri || '',
        media_url: createMediaUri || '',
        citations: [],
        tags: [createDomain],
      };
      await contentAPI.create(reelData);
      setShowCreateReel(false);
      resetCreateReel();
      Alert.alert('Published!', 'Your reel has been published.');
      fetchReels();
    } catch (e) {
      console.log('Failed to publish reel', e?.response?.data || e);
      const detail = e?.response?.data?.detail || 'Failed to publish reel. Please try again.';
      Alert.alert('Error', typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setPublishingReel(false);
    }
  };

  const CREATE_DOMAINS = [
    { id: 'technology', label: 'Tech' }, { id: 'ai', label: 'AI' },
    { id: 'physics', label: 'Physics' }, { id: 'nature', label: 'Nature' },
    { id: 'history', label: 'History' }, { id: 'space', label: 'Space' },
    { id: 'biology', label: 'Biology' }, { id: 'mathematics', label: 'Math' },
  ];

  const toggleLike = async (id) => {
    const wasLiked = likes[id] || false;
    setLikes(prev => ({ ...prev, [id]: !wasLiked }));
    // Optimistically update the count on the reel itself
    setReels(prev => prev.map(r => r.id === id ? { ...r, likes_count: (r.likes_count || 0) + (wasLiked ? -1 : 1) } : r));
    try { await contentAPI.interact(id, { interaction_type: 'like' }); }
    catch (e) {
      // Revert on failure
      setLikes(prev => ({ ...prev, [id]: wasLiked }));
      setReels(prev => prev.map(r => r.id === id ? { ...r, likes_count: (r.likes_count || 0) + (wasLiked ? 1 : -1) } : r));
    }
  };
  const toggleSave = async (id) => {
    const wasSaved = saves[id] || false;
    setSaves(prev => ({ ...prev, [id]: !wasSaved }));
    // Persist saved IDs to AsyncStorage for profile saved section
    try {
      const savedIdsJson = await AsyncStorage.getItem('saved_content_ids');
      const savedIds = savedIdsJson ? JSON.parse(savedIdsJson) : [];
      if (wasSaved) {
        await AsyncStorage.setItem('saved_content_ids', JSON.stringify(savedIds.filter(i => i !== id)));
      } else {
        await AsyncStorage.setItem('saved_content_ids', JSON.stringify([...savedIds, id]));
      }
    } catch {}
    try { await contentAPI.interact(id, { interaction_type: 'save' }); }
    catch (e) {
      setSaves(prev => ({ ...prev, [id]: wasSaved }));
    }
  };
  const handleShare = (item) => {
    Alert.alert('Share', `Share "${item.title}"?`, [
      { text: 'Copy Link', onPress: () => Alert.alert('Copied!') },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };
  const openComments = async (reel) => {
    setCommentModalReel(reel);
    setComments([]);
    setCommentsLoading(true);
    try {
      const res = await contentAPI.listComments(reel.id);
      const data = Array.isArray(res.data) ? res.data : (res.data?.documents || res.data?.comments || []);
      setComments(data);
    } catch (e) { console.log('Failed to fetch comments', e); setComments([]); }
    finally { setCommentsLoading(false); }
  };
  const addComment = async () => {
    if (!commentText.trim()) return;
    const txt = commentText.trim();
    setCommentText('');

    // Optimistically add comment immediately — always visible
    const tempComment = {
      id: 'local_' + Date.now(),
      content_id: commentModalReel.id,
      user_id: user?.user_id || '',
      username: user?.username || 'You',
      avatar_url: '',
      body: txt,
      likes_count: 0,
      created_at: new Date().toISOString(),
    };
    setComments(prev => [...prev, tempComment]);
    setReels(prev => prev.map(r => r.id === commentModalReel.id ? { ...r, comments_count: (r.comments_count || 0) + 1 } : r));

    // Persist to API in background — don't overwrite local state on failure
    try {
      await contentAPI.addComment(commentModalReel.id, { body: txt });
    } catch (e) {
      console.log('Comment post failed (kept locally):', e);
    }
    // Don't re-fetch — keep optimistic comments visible
  };
  const openStory = (story) => {
    if (story.isOwn && !story.hasStory) { handleCamera(); return; }
    storyPan.setValue({ x: 0, y: 0 });
    storyOpacity.setValue(1);
    setStoryIndex(0);
    setShowStory(story);
    setStories(prev => prev.map(s => s.id === story.id ? { ...s, viewed: true } : s));
  };
  const formatCount = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num ? num.toString() : '0';
  };

  // Control WebView video play/stop when active index changes + track views
  const viewedReels = useRef({});
  useEffect(() => {
    Object.entries(webViewRefs.current).forEach(([id, ref]) => {
      try {
        const reelIndex = reels.findIndex(r => r.id === id);
        if (reelIndex === activeIndex) {
          ref.postMessage('play');
        } else {
          ref.postMessage('stop');
        }
      } catch {}
    });
    // Track view for the active reel
    if (reels[activeIndex] && !viewedReels.current[reels[activeIndex].id]) {
      const reelId = reels[activeIndex].id;
      viewedReels.current[reelId] = true;
      setReels(prev => prev.map(r => r.id === reelId ? { ...r, views_count: (r.views_count || 0) + 1 } : r));
      contentAPI.interact(reelId, { interaction_type: 'view' }).catch(() => {});
    }
  }, [activeIndex, reels]);

  const togglePause = (id) => {
    const wasPaused = pausedReels[id] || false;
    setPausedReels(prev => ({ ...prev, [id]: !wasPaused }));
    const ref = webViewRefs.current[id];
    if (ref) {
      try { ref.postMessage(wasPaused ? 'play' : 'pause'); } catch {}
    }
  };

  const toggleMute = (id) => {
    const wasMuted = mutedReels[id] || false;
    setMutedReels(prev => ({ ...prev, [id]: !wasMuted }));
    const ref = webViewRefs.current[id];
    if (ref) {
      try { ref.postMessage(wasMuted ? 'unmute' : 'mute'); } catch {}
    }
  };

  const tapeColors = ['yellow', 'blue', 'pink', 'green', 'orange', 'purple'];

  const renderReel = ({ item, index }) => {
    const domainColor = DOMAIN_COLORS[item.domain] || '#3A5A9C';
    const domainIcon = DOMAIN_ICONS[item.domain] || 'bulb';
    const hasVideo = item.media_url && !item.media_url.startsWith('blob:');
    const hasImage = (item.thumbnail_url && !item.thumbnail_url.startsWith('blob:')) || (item.media_url && !item.media_url.startsWith('blob:') && !hasVideo);
    const isQuote = !hasVideo && !hasImage && item.body && item.body.length > 0;
    const contentType = item.content_type || 'reel';
    const tapeColor = tapeColors[index % tapeColors.length];
    const cardRotation = index % 3 === 0 ? -0.5 : index % 3 === 1 ? 0.3 : 0;

    return (
      <TouchableOpacity
        activeOpacity={0.9}
        style={[styles.reelCard, cardRotation !== 0 && { transform: [{ rotate: `${cardRotation}deg` }] }]}
        onPress={() => handleDoubleTap(item, index)}
      >
        <Tape color={tapeColor} style={{ left: 20 + (index % 4) * 15 }} width={50 + (index % 3) * 10} />

        {/* Double-tap heart animation */}
        {heartAnimId === item.id && (
          <Animated.View style={{
            position: 'absolute', zIndex: 99, alignSelf: 'center', top: '30%',
            opacity: heartScale, transform: [{ scale: heartScale.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1.2] }) }],
          }}>
            <Ionicons name="heart" size={80} color="#ED4956" />
          </Animated.View>
        )}

        {/* ═══ QUOTE / TEXT POST ═══ */}
        {isQuote ? (
          <View style={[styles.reelCardMediaWrap, { backgroundColor: domainColor + '12', justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 24 }]}>
            {/* Ruled lines background */}
            {Array.from({ length: 8 }, (_, i) => (
              <View key={`ql-${i}`} style={{ position: 'absolute', left: 0, right: 0, top: 28 + i * 28, height: 1, backgroundColor: 'rgba(90,150,210,0.10)' }} />
            ))}
            <View style={{ position: 'absolute', left: 20, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.12)' }} />
            <Ionicons name="chatbubble-ellipses" size={28} color={domainColor + '40'} style={{ marginBottom: 10 }} />
            <Text style={{ fontSize: 17, fontWeight: '700', color: '#2C1810', lineHeight: 26, textAlign: 'center', fontStyle: 'italic', paddingHorizontal: 10 }} numberOfLines={6}>
              "{item.body?.substring(0, 180)}{item.body?.length > 180 ? '...' : ''}"
            </Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12 }}>
              <View style={{ height: 2, width: 20, backgroundColor: domainColor, borderRadius: 1, opacity: 0.4 }} />
              <Text style={{ fontSize: 12, color: '#8A7558', fontWeight: '600' }}>@{item.author_username || 'unknown'}</Text>
              <View style={{ height: 2, width: 20, backgroundColor: domainColor, borderRadius: 1, opacity: 0.4 }} />
            </View>
            {/* Stats overlay */}
            <View style={{ position: 'absolute', bottom: 10, right: 10, flexDirection: 'row', gap: 12 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons name="heart-outline" size={14} color="#8A7558" />
                <Text style={{ fontSize: 11, color: '#8A7558', fontWeight: '600' }}>{formatCount(item.likes_count || 0)}</Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                <Ionicons name="chatbubble-outline" size={14} color="#8A7558" />
                <Text style={{ fontSize: 11, color: '#8A7558', fontWeight: '600' }}>{formatCount(item.comments_count || 0)}</Text>
              </View>
            </View>
          </View>
        ) : (
          /* ═══ IMAGE / VIDEO POST ═══ */
          <View style={styles.reelCardMediaWrap}>
            {item.thumbnail_url && !item.thumbnail_url.startsWith('blob:') ? (
              <Image source={{ uri: item.thumbnail_url }} style={styles.reelCardMedia} resizeMode="cover" />
            ) : item.media_url && !item.media_url.startsWith('blob:') ? (
              <Image source={{ uri: item.media_url }} style={styles.reelCardMedia} resizeMode="cover" />
            ) : (
              <View style={[styles.reelCardMedia, { backgroundColor: domainColor + '22', justifyContent: 'center', alignItems: 'center' }]}>
                <Ionicons name={domainIcon} size={90} color={domainColor + '55'} />
              </View>
            )}
            <View style={styles.reelCardOverlay} />
            {hasVideo ? (
              <View style={styles.playRing}>
                <Ionicons name="play" size={18} color="#FFFFFF" style={{ marginLeft: 2 }} />
              </View>
            ) : (
              <View style={[styles.playRing, { backgroundColor: 'rgba(255,255,255,0.15)', borderColor: 'rgba(255,255,255,0.6)' }]}>
                <Ionicons name="image" size={18} color="#FFFFFF" />
              </View>
            )}
            <View style={styles.mediaSidebar}>
              <View style={styles.mediaStat}>
                <Ionicons name="heart-outline" size={18} color="#FFFFFF" />
                <Text style={styles.mediaStatText}>{formatCount(item.likes_count || 0)}</Text>
              </View>
              <View style={styles.mediaStat}>
                <Ionicons name="chatbubble-outline" size={18} color="#FFFFFF" />
                <Text style={styles.mediaStatText}>{formatCount(item.comments_count || 0)}</Text>
              </View>
              <View style={styles.mediaStat}>
                <Ionicons name="eye-outline" size={18} color="#FFFFFF" />
                <Text style={styles.mediaStatText}>{formatCount(item.views_count || 0)}</Text>
              </View>
              {hasVideo && (
                <View style={styles.mediaAudioTag}>
                  <Text style={styles.mediaAudioText}>Video</Text>
                </View>
              )}
              {!hasVideo && hasImage && (
                <View style={[styles.mediaAudioTag, { backgroundColor: 'rgba(255,255,255,0.2)' }]}>
                  <Text style={styles.mediaAudioText}>Photo</Text>
                </View>
              )}
            </View>
          </View>
        )}

        <View style={styles.reelCardBody}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <Stamp domain={item.domain} color={domainColor} />
            {contentType !== 'reel' && (
              <View style={{ backgroundColor: domainColor + '15', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 2, borderWidth: 1, borderColor: domainColor + '30' }}>
                <Text style={{ fontSize: 8, fontWeight: '800', color: domainColor, letterSpacing: 1, textTransform: 'uppercase' }}>{contentType}</Text>
              </View>
            )}
          </View>
          <Text style={styles.reelCardTitle} numberOfLines={2}>{item.title || 'Untitled post'}</Text>
          {isQuote && item.body && (
            <Text style={{ fontSize: 13, color: '#8A7558', lineHeight: 19, marginBottom: 8 }} numberOfLines={2}>{item.body.substring(0, 100)}</Text>
          )}
          <View style={styles.authorRow}>
            <View style={[styles.smallAvatar, { backgroundColor: domainColor + '20', borderWidth: 1.5, borderColor: '#2C1810' }]}>
              <Text style={{ color: domainColor, fontSize: 11, fontWeight: '700' }}>{item.author_username?.[0]?.toUpperCase() || '?'}</Text>
            </View>
            <Text style={styles.authorNameCard}>@{item.author_username || 'unknown'}</Text>
          </View>

          {/* ═══ INLINE ACTION BAR ═══ */}
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: 'rgba(90,150,210,0.10)', gap: 4 }}>
            <TouchableOpacity
              style={{ flexDirection: 'row', alignItems: 'center', gap: 5, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8, backgroundColor: likes[item.id] ? '#FEE2E2' : 'transparent' }}
              onPress={() => toggleLike(item.id)}
              activeOpacity={0.7}
            >
              <Ionicons name={likes[item.id] ? 'heart' : 'heart-outline'} size={18} color={likes[item.id] ? '#DC2626' : '#8A7558'} />
              <Text style={{ fontSize: 12, fontWeight: '700', color: likes[item.id] ? '#DC2626' : '#8A7558' }}>{formatCount((item.likes_count || 0) + (likes[item.id] ? 1 : 0))}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={{ flexDirection: 'row', alignItems: 'center', gap: 5, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8 }}
              onPress={() => openComments(item)}
              activeOpacity={0.7}
            >
              <Ionicons name="chatbubble-outline" size={16} color="#8A7558" />
              <Text style={{ fontSize: 12, fontWeight: '700', color: '#8A7558' }}>{formatCount(item.comments_count || 0)}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={{ flexDirection: 'row', alignItems: 'center', gap: 5, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8, backgroundColor: saves[item.id] ? '#EFF6FF' : 'transparent' }}
              onPress={() => toggleSave(item.id)}
              activeOpacity={0.7}
            >
              <Ionicons name={saves[item.id] ? 'bookmark' : 'bookmark-outline'} size={16} color={saves[item.id] ? '#2563EB' : '#8A7558'} />
            </TouchableOpacity>

            <View style={{ flex: 1 }} />

            <TouchableOpacity
              style={{ paddingVertical: 6, paddingHorizontal: 8 }}
              onPress={() => { try { require('react-native').Share.share({ message: `${item.title} — ScrollUForward` }); } catch {} }}
              activeOpacity={0.7}
            >
              <Ionicons name="share-outline" size={16} color="#8A7558" />
            </TouchableOpacity>
          </View>

          <PaperCorner />
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: '#FDF6E3' }]}>
      <StatusBar barStyle="dark-content" backgroundColor="#FDF6E3" translucent={false} />
      {/* Notebook margin line */}
      <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.10)', zIndex: 0 }} pointerEvents="none" />

      {/* Fixed Header — Camera, Notifications, Chat */}
      <View style={styles.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <View style={{ flexDirection: 'row', gap: 6 }}>
            <View style={{ width: 10, height: 10, borderRadius: 5, borderWidth: 2, borderColor: '#C4AA78', backgroundColor: '#E6D5B8' }}>
              <View style={{ width: 4, height: 4, borderRadius: 2, backgroundColor: '#FDF6E3', position: 'absolute', top: 1, left: 1 }} />
            </View>
            <View style={{ width: 10, height: 10, borderRadius: 5, borderWidth: 2, borderColor: '#C4AA78', backgroundColor: '#E6D5B8' }}>
              <View style={{ width: 4, height: 4, borderRadius: 2, backgroundColor: '#FDF6E3', position: 'absolute', top: 1, left: 1 }} />
            </View>
            <View style={{ width: 10, height: 10, borderRadius: 5, borderWidth: 2, borderColor: '#C4AA78', backgroundColor: '#E6D5B8' }}>
              <View style={{ width: 4, height: 4, borderRadius: 2, backgroundColor: '#FDF6E3', position: 'absolute', top: 1, left: 1 }} />
            </View>
          </View>
          <View style={{ position: 'relative' }}>
            <View style={{ position: 'absolute', left: -6, right: -6, bottom: -1, height: '50%', backgroundColor: 'rgba(255,214,10,0.45)', borderRadius: 2, transform: [{ rotate: '-1deg' }] }} />
            <Text style={styles.logoText}>Scroll<Text style={{ color: '#3B82F6', fontWeight: '900', fontStyle: 'italic' }}>U</Text>Forward</Text>
          </View>
        </View>
        <View style={styles.headerIcons}>
          <TouchableOpacity style={styles.headerIconBtn} onPress={handleCamera}>
            <Ionicons name="camera-outline" size={18} color="#2C1810" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerIconBtn} onPress={() => navigation.navigate('Notifications')}>
            <Ionicons name="heart-outline" size={18} color="#2C1810" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerIconBtn} onPress={openChat}>
            <Ionicons name="chatbubble-ellipses-outline" size={18} color="#2C1810" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Reels feed with stories as scrollable header */}
      <View style={styles.reelsFeed}>
        <FlatList
          data={reels}
          keyExtractor={(item, idx) => item.id ? `${item.id}_${idx}` : `reel_${idx}`}
          renderItem={renderReel}
          contentContainerStyle={{ paddingTop: 0, paddingBottom: 24 }}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#F9D84A" colors={['#F9D84A']} />}
          ListHeaderComponent={
            <View style={styles.storiesContainer}>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storiesList}>
                {stories.map(story => (
                  <TouchableOpacity key={story.id} style={styles.storyItem} onPress={() => openStory(story)}>
                    <View style={[styles.storyRing, {
                      borderColor: story.isOwn && !story.hasStory ? '#8A7860' : story.viewed ? '#C8BFA8' : (story.color || '#3A5A9C'),
                      borderWidth: story.isOwn && !story.hasStory ? 1.5 : 2.5,
                      borderStyle: story.isOwn && !story.hasStory ? 'dashed' : 'solid',
                    }]}>
                      <View style={[styles.storyAvatar, { backgroundColor: (story.color || '#3A5A9C') + '20' }]}>
                        <Text style={[styles.storyAvatarText, { color: story.color || '#3A5A9C' }]}>{story.username[0].toUpperCase()}</Text>
                      </View>
                      {story.isOwn && !story.hasStory && (
                        <View style={styles.addStoryBadge}>
                          <Ionicons name="add" size={12} color="#0A0A0A" />
                        </View>
                      )}
                    </View>
                    <Text style={styles.storyUsername} numberOfLines={1}>
                      {story.isOwn ? 'Your story' : story.username}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          }
          ListEmptyComponent={!loading && (
            <View style={{ height: 300, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
              <View style={{ width: 90, height: 90, borderWidth: 2.5, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 22, borderBottomLeftRadius: 22, borderBottomRightRadius: 2, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '-4deg' }], marginBottom: 18, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 8 } }) }}>
                <Ionicons name="videocam-outline" size={40} color="#C4AA78" />
              </View>
              <Text style={{ color: '#2C1810', fontWeight: '900', fontSize: 18, marginBottom: 6, letterSpacing: -0.5 }}>No reels yet</Text>
              <Text style={{ color: '#7A6848', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>The stage is empty! Be the first to share a reel and start the show.</Text>
              <MarkerUnderline color="#FFD60A" width={60} style={{ marginTop: 14 }} />
            </View>
          )}
          ListFooterComponent={loading ? (
            <View style={{ paddingVertical: 20 }}>
              <ActivityIndicator color="#3A5A9C" />
            </View>
          ) : null}
        />
      </View>

      {/* Fullscreen Reel Modal — with likes, comments, scroll */}
      <Modal visible={fullscreen} animationType="fade" statusBarTranslucent onRequestClose={exitFullscreen}>
        <View style={{ flex: 1, backgroundColor: '#000' }}>
          <StatusBar hidden />
          <FlatList
            data={reels}
            keyExtractor={(item) => 'fs_' + item.id}
            pagingEnabled
            showsVerticalScrollIndicator={false}
            snapToInterval={height}
            decelerationRate="fast"
            initialScrollIndex={activeIndex}
            getItemLayout={(data, index) => ({ length: height, offset: height * index, index })}
            onMomentumScrollEnd={(e) => {
              const newIdx = Math.round(e.nativeEvent.contentOffset.y / height);
              if (newIdx !== activeIndex) {
                setFsPaused(false);
                setVideoProgress(prev => { const p = {...prev}; delete p['fs_' + reels[activeIndex]?.id]; return p; });
              }
              setActiveIndex(newIdx);
            }}
            renderItem={({ item: fsItem, index: fsIdx }) => {
              const fsHasVideo = fsItem.media_url && !fsItem.media_url.startsWith('blob:') && (fsItem.media_url.includes('amazonaws') || fsItem.media_url.includes('s3') || fsItem.media_url.match(/\.(mp4|mov|webm|avi)($|\?)/i));
              const fsIsActive = fsIdx === activeIndex;
              const fsLiked = likes[fsItem.id] || false;
              const fsSaved = saves[fsItem.id] || false;
              const fsDC = DOMAIN_COLORS[fsItem.domain] || '#FF6B35';
              return (
                <View style={{ width, height, backgroundColor: '#000' }}>
                  {fsHasVideo && fsIsActive ? (
                    <WebView
                      ref={ref => { if (ref) webViewRefs.current['fs_active'] = ref; }}
                      source={{ html: `
                        <html><head><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
                        <style>*{margin:0;padding:0;box-sizing:border-box}body{background:#000;overflow:hidden;width:100vw;height:100vh}
                        video{width:100vw;height:100vh;object-fit:contain;background:#000}</style></head>
                        <body>
                        <video id="v" playsinline webkit-playsinline loop autoplay
                          src="${fsItem.media_url}" poster="${fsItem.thumbnail_url || ''}"></video>
                        <script>
                          var v=document.getElementById('v');
                          var isMuted=false;
                          function handle(e){
                            var d=e.data;
                            if(d==='pause'){v.pause();}
                            if(d==='play'){v.play();}
                            if(d==='stop'){v.pause();v.currentTime=0;}
                            if(d==='mute'){v.muted=true;isMuted=true;}
                            if(d==='unmute'){v.muted=false;isMuted=false;}
                            if(d==='toggleMute'){v.muted=!v.muted;isMuted=v.muted;window.ReactNativeWebView&&window.ReactNativeWebView.postMessage(JSON.stringify({muted:v.muted}));}
                            if(d&&d.startsWith&&d.startsWith('seek:'))v.currentTime=parseFloat(d.split(':')[1]);
                          }
                          window.addEventListener('message',handle);
                          document.addEventListener('message',handle);
                          v.addEventListener('timeupdate',function(){
                            window.ReactNativeWebView&&window.ReactNativeWebView.postMessage(JSON.stringify({t:v.currentTime,d:v.duration,muted:v.muted}));
                          });
                          v.addEventListener('loadeddata',function(){
                            window.ReactNativeWebView&&window.ReactNativeWebView.postMessage(JSON.stringify({ready:true,d:v.duration}));
                          });
                          // Start playing with sound
                          v.muted=false;
                          v.volume=1;
                          v.play().catch(function(){
                            // If autoplay with sound fails, try muted then unmute
                            v.muted=true;
                            v.play().then(function(){
                              setTimeout(function(){v.muted=false;},300);
                            }).catch(function(){});
                          });
                        </script></body></html>
                      ` }}
                      style={StyleSheet.absoluteFillObject}
                      allowsInlineMediaPlayback={true}
                      mediaPlaybackRequiresUserAction={false}
                      javaScriptEnabled={true}
                      scrollEnabled={false}
                      allowsFullscreenVideo={true}
                      onMessage={(e) => {
                        try {
                          const msg = JSON.parse(e.nativeEvent.data);
                          if (msg.t !== undefined && msg.d) {
                            setVideoProgress(prev => ({ ...prev, ['fs_' + fsItem.id]: { current: msg.t, duration: msg.d } }));
                          }
                          if (msg.muted !== undefined) {
                            setMutedReels(prev => ({ ...prev, [fsItem.id]: msg.muted }));
                          }
                        } catch {}
                      }}
                    />
                  ) : (fsItem.thumbnail_url && !fsItem.thumbnail_url.startsWith('blob:')) ? (
                    <Image source={{ uri: fsItem.thumbnail_url }} style={StyleSheet.absoluteFillObject} resizeMode="contain" />
                  ) : (
                    <View style={[StyleSheet.absoluteFillObject, { justifyContent: 'center', alignItems: 'center' }]}>
                      <Ionicons name={DOMAIN_ICONS[fsItem.domain] || 'bulb'} size={120} color={fsDC + '30'} />
                    </View>
                  )}

                  {/* Bottom gradient */}
                  <View style={[styles.bottomGradientWrap, { pointerEvents: 'none' }]}>
                    <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0)' }} />
                    <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.2)' }} />
                    <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' }} />
                    <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.7)' }} />
                  </View>

                  {/* Right-side action bar */}
                  <View style={[styles.actionBar, { bottom: 80 }]}>
                    <TouchableOpacity style={styles.actionItem} onPress={() => toggleLike(fsItem.id)}>
                      <Ionicons name={fsLiked ? 'heart' : 'heart-outline'} size={30} color={fsLiked ? '#ED4956' : '#FFF'} />
                      <Text style={styles.actionText}>{formatCount(fsItem.likes_count || 0)}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.actionItem} onPress={() => { openComments(fsItem); }}>
                      <Ionicons name="chatbubble-outline" size={28} color="#FFF" />
                      <Text style={styles.actionText}>{formatCount(fsItem.comments_count)}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.actionItem} onPress={() => handleShare(fsItem)}>
                      <Ionicons name="paper-plane-outline" size={28} color="#FFF" />
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.actionItem} onPress={() => toggleSave(fsItem.id)}>
                      <Ionicons name={fsSaved ? 'bookmark' : 'bookmark-outline'} size={28} color={fsSaved ? '#F9D84A' : '#FFF'} />
                    </TouchableOpacity>
                  </View>

                  {/* Bottom-left: title + author */}
                  <View style={[styles.bottomOverlay, { bottom: 80 }]}>
                    <View style={[styles.domainBadge, { backgroundColor: fsDC + '25', borderColor: fsDC + '50' }]}>
                      <Ionicons name={DOMAIN_ICONS[fsItem.domain] || 'bulb'} size={13} color={fsDC} />
                      <Text style={[styles.domainText, { color: fsDC }]}>{(fsItem.domain || '').toUpperCase()}</Text>
                    </View>
                    <Text style={[styles.reelTitle, { fontSize: 18 }]} numberOfLines={2}>{fsItem.title}</Text>
                    <Text style={styles.authorName}>@{fsItem.author_username}</Text>
                  </View>

                  {/* Draggable progress bar */}
                  {videoProgress['fs_' + fsItem.id] && (() => {
                    const prog = videoProgress['fs_' + fsItem.id];
                    const pct = prog.duration > 0 ? (prog.current / prog.duration) * 100 : 0;
                    const fmtTime = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
                    const seekTo = (locationX) => {
                      const trackWidth = width - 110;
                      const ratio = Math.max(0, Math.min(1, locationX / trackWidth));
                      const r = webViewRefs.current['fs_active'];
                      if (r && prog.duration) r.postMessage('seek:' + (ratio * prog.duration).toFixed(1));
                    };
                    return (
                      <View style={[styles.fsSlider, { bottom: 24 }]}>
                        <Text style={styles.fsTime}>{fmtTime(prog.current)}</Text>
                        <View
                          style={styles.fsSliderTrack}
                          onStartShouldSetResponder={() => true}
                          onMoveShouldSetResponder={() => true}
                          onResponderGrant={(e) => seekTo(e.nativeEvent.locationX)}
                          onResponderMove={(e) => seekTo(e.nativeEvent.locationX)}
                          onResponderTerminationRequest={() => false}
                        >
                          <View style={styles.fsSliderBg}>
                            <View style={[styles.fsSliderFill, { width: `${pct}%` }]} />
                          </View>
                          <View style={[styles.fsSliderDot, { left: `${pct}%` }]} />
                        </View>
                        <Text style={styles.fsTime}>{fmtTime(prog.duration)}</Text>
                      </View>
                    );
                  })()}
                </View>
              );
            }}
          />
          {/* Back button — floating */}
          {/* Back button */}
          <TouchableOpacity style={styles.fsBackBtn} onPress={exitFullscreen}>
            <Ionicons name="close" size={26} color="#FFF" />
          </TouchableOpacity>
          {/* Pause/Play toggle */}
          <TouchableOpacity style={styles.fsPauseBtn} onPress={() => {
            const ref = webViewRefs.current['fs_active'];
            if (ref) {
              if (fsPaused) { ref.postMessage('play'); setFsPaused(false); }
              else { ref.postMessage('pause'); setFsPaused(true); }
            }
          }}>
            <Ionicons name={fsPaused ? 'play' : 'pause'} size={24} color="#FFF" />
          </TouchableOpacity>
          {/* Mute/Unmute toggle */}
          <TouchableOpacity style={[styles.fsPauseBtn, { right: 60, top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 14 : 50 }]} onPress={() => {
            const ref = webViewRefs.current['fs_active'];
            if (ref) {
              ref.postMessage('toggleMute');
            }
          }}>
            <Ionicons name={mutedReels[reels[activeIndex]?.id] ? 'volume-mute' : 'volume-high'} size={22} color="#FFF" />
          </TouchableOpacity>
        </View>
      </Modal>

      {/* Story Viewer Modal */}
      <Modal visible={!!showStory} animationType="fade" transparent statusBarTranslucent>
        <Animated.View
          style={[styles.storyModal, { opacity: storyOpacity, transform: storyPan.getTranslateTransform() }]}
          {...storyPanResponder.panHandlers}
        >
          {(() => {
            const content = getStoryContent(showStory);
            const current = content[storyIndex % content.length] || content[0];
            if (!current) return null;
            return (
              <View style={[styles.storyContent, { backgroundColor: '#000' }]}>
                {/* Background media — Image or Video */}
                {current.mediaUri && current.mediaType === 'image' && (
                  <Image source={{ uri: current.mediaUri }} style={styles.storyMedia} resizeMode="cover" />
                )}
                {current.mediaUri && current.mediaType === 'video' && Video ? (
                  <Video
                    source={{ uri: current.mediaUri }}
                    style={styles.storyMedia}
                    resizeMode={ResizeMode.COVER}
                    shouldPlay={true}
                    isLooping={false}
                    isMuted={false}
                  />
                ) : current.mediaUri && current.mediaType === 'video' ? (
                  <Image source={{ uri: current.mediaUri }} style={styles.storyMedia} resizeMode="cover" />
                ) : null}
                {/* Fallback solid bg when no media */}
                {!current.mediaUri && (
                  <View style={[styles.storyMedia, { backgroundColor: current.bg || '#222' }]} />
                )}

                {/* Gradient overlay for readability */}
                <View style={styles.storyGradientTop} />
                <View style={styles.storyGradientBottom} />

                {/* Progress bars */}
                <View style={styles.storyProgress}>
                  {content.map((_, i) => (
                    <View key={i} style={[styles.progressBar, { backgroundColor: 'rgba(255,255,255,0.3)' }]}>
                      {i < storyIndex && (
                        <View style={[styles.progressFill, { width: '100%' }]} />
                      )}
                      {i === storyIndex && (
                        <Animated.View style={[styles.progressFill, {
                          width: progressAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }),
                        }]} />
                      )}
                    </View>
                  ))}
                </View>

                {/* Header */}
                <View style={styles.storyHeader}>
                  <View style={styles.storyHeaderLeft}>
                    <View style={[styles.storyHeaderAvatar, { backgroundColor: 'rgba(255,255,255,0.3)' }]}>
                      <Text style={{ color: '#FFF', fontWeight: '700' }}>{showStory?.username?.[0]?.toUpperCase()}</Text>
                    </View>
                    <Text style={styles.storyHeaderName}>{showStory?.username}</Text>
                    <Text style={styles.storyHeaderTime}>2h</Text>
                  </View>
                  <TouchableOpacity onPress={() => setShowStory(null)}>
                    <Ionicons name="close" size={28} color="#FFF" />
                  </TouchableOpacity>
                </View>

                {/* Domain badge */}
                {current.domain && (
                  <View style={styles.storyDomainBadge}>
                    <Ionicons name={DOMAIN_ICONS[current.domain] || 'bulb'} size={14} color="#FFF" />
                    <Text style={styles.storyDomainText}>{current.domain.toUpperCase()}</Text>
                  </View>
                )}

                {/* Text content (only if there's text and no media, or text overlay) */}
                {current.text && !current.mediaUri ? (
                  <View style={styles.storyCenter}>
                    <Text style={styles.storyText}>{current.text}</Text>
                  </View>
                ) : null}

                {/* Tap areas */}
                <View style={styles.storyTapAreas}>
                  <TouchableOpacity style={styles.tapLeft} onPress={() => {
                    if (storyIndex > 0) setStoryIndex(storyIndex - 1);
                  }} />
                  <TouchableOpacity style={styles.tapRight} onPress={() => {
                    if (storyIndex < content.length - 1) setStoryIndex(storyIndex + 1);
                    else setShowStory(null);
                  }} />
                </View>

                {/* Bottom — reply bar */}
                <View style={styles.storyBottom}>
                  <TextInput style={styles.storyReplyInput} placeholder="Send message..." placeholderTextColor="rgba(255,255,255,0.7)" />
                  <TouchableOpacity style={styles.storyActionBtn}><Ionicons name="heart-outline" size={26} color="#FFF" /></TouchableOpacity>
                  <TouchableOpacity style={styles.storyActionBtn}><Ionicons name="paper-plane-outline" size={24} color="#FFF" /></TouchableOpacity>
                </View>
              </View>
            );
          })()}
        </Animated.View>
      </Modal>

      {/* Comment Modal — Instagram-style bottom sheet */}
      <Modal visible={!!commentModalReel} animationType="slide" transparent onRequestClose={() => setCommentModalReel(null)}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' }}>
          <TouchableOpacity style={{ flex: 1 }} activeOpacity={1} onPress={() => setCommentModalReel(null)} />
          <KeyboardAvoidingView behavior="padding" keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}>
            <View style={{ backgroundColor: theme.background || '#FFFFFF', borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: height * 0.7 }}>
              {/* Handle bar */}
              <View style={{ alignItems: 'center', paddingTop: 10, paddingBottom: 6 }}>
                <View style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: '#333' }} />
              </View>

              {/* Header */}
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 10, borderBottomWidth: 0.5, borderBottomColor: theme.border || '#222' }}>
                <Text style={{ fontSize: 16, fontWeight: '700', color: theme.textPrimary || '#FFF' }}>
                  Comments {comments.length > 0 ? `(${comments.length})` : ''}
                </Text>
                <TouchableOpacity onPress={() => setCommentModalReel(null)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                  <Ionicons name="close" size={24} color={theme.textPrimary || '#FFF'} />
                </TouchableOpacity>
              </View>

              {/* Comments list */}
              <ScrollView style={{ maxHeight: height * 0.45, paddingHorizontal: 16 }} showsVerticalScrollIndicator={false}>
                {commentsLoading ? (
                  <View style={{ padding: 30, alignItems: 'center' }}>
                    <ActivityIndicator color={theme.primary || '#F9D84A'} />
                    <Text style={{ color: '#555', marginTop: 8 }}>Loading comments...</Text>
                  </View>
                ) : comments.length === 0 ? (
                  <View style={{ alignItems: 'center', paddingVertical: 40 }}>
                    <Ionicons name="chatbubble-outline" size={40} color="#333" />
                    <Text style={{ color: '#555', marginTop: 10, fontSize: 14 }}>No comments yet</Text>
                    <Text style={{ color: '#8A7860', fontSize: 12, marginTop: 4 }}>Be the first to comment!</Text>
                  </View>
                ) : (
                  comments.map((c, idx) => (
                    <View key={c.id || idx} style={{ flexDirection: 'row', paddingVertical: 10, borderBottomWidth: idx < comments.length - 1 ? 0.5 : 0, borderBottomColor: '#1A1A1A', gap: 10 }}>
                      <View style={{ width: 36, height: 36, borderRadius: 18, backgroundColor: (theme.primary || '#F9D84A') + '15', justifyContent: 'center', alignItems: 'center' }}>
                        <Text style={{ color: theme.primary || '#F9D84A', fontSize: 14, fontWeight: '700' }}>{(c.username || '?')[0].toUpperCase()}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                          <Text style={{ color: theme.textPrimary || '#FFF', fontSize: 13, fontWeight: '600' }}>{c.username || 'User'}</Text>
                          <Text style={{ color: '#555', fontSize: 11 }}>{c.created_at ? new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</Text>
                        </View>
                        <Text style={{ color: theme.textSecondary || '#CCC', fontSize: 14, lineHeight: 20, marginTop: 2 }}>{c.body}</Text>
                      </View>
                    </View>
                  ))
                )}
                <View style={{ height: 10 }} />
              </ScrollView>

              {/* Input bar — always visible above keyboard */}
              <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 10, borderTopWidth: 0.5, borderTopColor: theme.border || '#222', gap: 8 }}>
                <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: (theme.primary || '#F9D84A') + '15', justifyContent: 'center', alignItems: 'center' }}>
                  <Text style={{ color: theme.primary || '#F9D84A', fontSize: 12, fontWeight: '700' }}>{(user?.username || 'Y')[0].toUpperCase()}</Text>
                </View>
                <TextInput
                  style={{ flex: 1, minHeight: 40, maxHeight: 100, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, backgroundColor: theme.surface || '#141414', color: theme.textPrimary || '#FFF', borderWidth: 1, borderColor: theme.border || '#222' }}
                  placeholder="Add a comment..."
                  placeholderTextColor="#8A7860"
                  value={commentText}
                  onChangeText={setCommentText}
                  returnKeyType="send"
                  onSubmitEditing={addComment}
                  multiline
                />
                <TouchableOpacity onPress={addComment} style={{ padding: 6 }}>
                  <Ionicons name="send" size={22} color={commentText.trim() ? (theme.primary || '#F9D84A') : '#444'} />
                </TouchableOpacity>
              </View>
            </View>
          </KeyboardAvoidingView>
        </View>
      </Modal>

      {/* Create Reel Modal — sketch style */}
      <Modal visible={showCreateReel} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => { setShowCreateReel(false); resetCreateReel(); }}>
        <KeyboardAvoidingView style={{ flex: 1, backgroundColor: '#FBF8F0' }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: Platform.OS === 'ios' ? 56 : 16, paddingBottom: 12, paddingHorizontal: 20, borderBottomWidth: 1.5, borderBottomColor: '#2C1810' }}>
            <TouchableOpacity onPress={() => { setShowCreateReel(false); resetCreateReel(); }}>
              <Ionicons name="close" size={26} color="#8A7860" />
            </TouchableOpacity>
            <Text style={{ fontSize: 18, fontWeight: '700', color: '#2C1810' }}>New Reel</Text>
            <TouchableOpacity
              style={{ backgroundColor: (!createTitle.trim() || !createBody.trim() || publishingReel) ? '#C8BFA8' : '#F9D84A', paddingHorizontal: 20, paddingVertical: 9, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 }}
              onPress={handlePublishReel}
              disabled={!createTitle.trim() || !createBody.trim() || publishingReel}
            >
              {publishingReel ? <ActivityIndicator color="#2C1810" size="small" /> : (
                <Text style={{ fontSize: 14, fontWeight: '700', color: (!createTitle.trim() || !createBody.trim()) ? '#8A7860' : '#2C1810' }}>Publish</Text>
              )}
            </TouchableOpacity>
          </View>
          <ScrollView style={{ flex: 1, paddingHorizontal: 20 }} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
            <TouchableOpacity style={{ marginTop: 20, height: 200, borderWidth: 1.5, borderColor: '#2C1810', borderStyle: 'dashed', backgroundColor: '#F8F6F0', justifyContent: 'center', alignItems: 'center', overflow: 'hidden', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 3, borderBottomRightRadius: 10 }} onPress={pickReelMedia}>
              {createMediaUri ? (
                <Image source={{ uri: createMediaUri }} style={{ width: '100%', height: '100%' }} />
              ) : (
                <View style={{ alignItems: 'center', gap: 8 }}>
                  <Ionicons name="videocam-outline" size={36} color="#8A7860" />
                  <Text style={{ fontSize: 14, color: '#8A7860' }}>Add video or thumbnail</Text>
                </View>
              )}
            </TouchableOpacity>
            <TextInput style={{ fontSize: 22, fontWeight: '700', color: '#2C1810', marginTop: 20 }} placeholder="Reel title" placeholderTextColor="#8A7860" value={createTitle} onChangeText={setCreateTitle} />
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 16 }} contentContainerStyle={{ gap: 8 }}>
              {CREATE_DOMAINS.map(d => (
                <TouchableOpacity key={d.id} style={{ paddingHorizontal: 14, paddingVertical: 8, borderWidth: 1.5, borderColor: createDomain === d.id ? (DOMAIN_COLORS[d.id] || '#2C1810') : '#2C1810', backgroundColor: createDomain === d.id ? (DOMAIN_COLORS[d.id] || '#F9D84A') + '25' : '#FFFFFF', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 }} onPress={() => setCreateDomain(d.id)}>
                  <Text style={{ fontSize: 13, fontWeight: '500', color: createDomain === d.id ? (DOMAIN_COLORS[d.id] || '#2C1810') : '#8A7860' }}>{d.label}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TextInput style={{ fontSize: 16, lineHeight: 24, color: '#5A4A30', marginTop: 16, minHeight: 150 }} placeholder="Reel script / description (min 50 chars)..." placeholderTextColor="#8A7860" value={createBody} onChangeText={setCreateBody} multiline textAlignVertical="top" />
            <View style={{ height: 120 }} />
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Fixed header at top
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 18, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 50, paddingBottom: 12,
    backgroundColor: '#FDF6E3',
    borderBottomWidth: 2, borderBottomColor: '#2C1810',
  },
  logoText: { color: '#2C1810', fontSize: 24, fontWeight: '900', letterSpacing: -1 },
  headerIcons: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerIconBtn: {
    width: 36, height: 36,
    borderWidth: 2, borderColor: '#2C1810',
    borderTopLeftRadius: 2, borderTopRightRadius: 10,
    borderBottomLeftRadius: 10, borderBottomRightRadius: 2,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#FFFCF2',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  notifDot: { position: 'absolute', top: -3, right: -3, width: 10, height: 10, borderRadius: 5, backgroundColor: '#EF4444', borderWidth: 2, borderColor: '#2C1810' },

  // Stories row
  storiesContainer: { height: STORIES_HEIGHT + 4, justifyContent: 'center', marginTop: 6, marginBottom: 12, backgroundColor: '#FDF6E3', borderBottomWidth: 1, borderBottomColor: 'rgba(90,150,210,0.12)' },
  storiesList: { paddingHorizontal: 18, gap: 16 },
  storyItem: { alignItems: 'center', width: 70 },
  storyRing: { width: 58, height: 58, borderRadius: 29, justifyContent: 'center', alignItems: 'center', padding: 2, backgroundColor: '#FFFCF2' },
  storyAvatar: { width: '100%', height: '100%', borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
  storyAvatarText: { fontSize: 20, fontWeight: '800' },
  addStoryBadge: { position: 'absolute', bottom: -2, right: -2, width: 18, height: 18, borderRadius: 9, justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#2C1810', backgroundColor: '#FFD60A' },
  storyUsername: { color: '#7A6848', fontSize: 10, fontWeight: '600', marginTop: 4, textAlign: 'center' },

  // Reels feed
  reelsFeed: { flex: 1, backgroundColor: '#FDF6E3', paddingHorizontal: 14, paddingLeft: 18 },
  reelCard: {
    backgroundColor: '#FFFCF2',
    borderWidth: 2.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 3,
    overflow: 'hidden',
    marginBottom: 22,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },
  reelCardMediaWrap: { height: 230, backgroundColor: '#10131A' },
  reelCardMedia: { width: '100%', height: '100%' },
  reelCardOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.2)' },
  playRing: {
    position: 'absolute',
    alignSelf: 'center',
    top: '40%',
    width: 54,
    height: 54,
    borderRadius: 27,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  mediaSidebar: { position: 'absolute', right: 10, bottom: 10, alignItems: 'center', gap: 10 },
  mediaStat: { alignItems: 'center', gap: 1 },
  mediaStatText: { color: 'rgba(255,255,255,0.9)', fontSize: 11, fontWeight: '600' },
  mediaAudioTag: { marginTop: 2, backgroundColor: 'rgba(0,0,0,0.35)', borderRadius: 10, paddingHorizontal: 7, paddingVertical: 2 },
  mediaAudioText: { color: 'rgba(255,255,255,0.9)', fontSize: 10, fontWeight: '600' },
  reelCardBody: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 14, borderTopWidth: 1.5, borderTopColor: 'rgba(90,150,210,0.12)' },
  reelCardTitle: { color: '#2C1810', fontSize: 17, fontWeight: '800', lineHeight: 24, marginBottom: 9, letterSpacing: -0.3 },

  // Fullscreen reel
  reelContainer: { width, overflow: 'hidden' },
  reelBackground: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center' },
  bgIcon: { position: 'absolute', top: '20%', opacity: 0.6 },
  bottomGradientWrap: { position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%', zIndex: 1 },
  bottomOverlay: { position: 'absolute', bottom: 16, left: 14, right: 86, zIndex: 2 },
  domainBadge: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', paddingHorizontal: 9, paddingVertical: 3, borderWidth: 2, borderRadius: 3, gap: 4, marginBottom: 8, backgroundColor: 'rgba(255,255,255,0.85)', transform: [{ rotate: '-1.5deg' }] },
  domainText: { fontSize: 10, fontWeight: '700', letterSpacing: 1.2, textTransform: 'uppercase' },
  reelTitle: { color: '#FFF', fontSize: 16, fontWeight: '700', lineHeight: 22, marginBottom: 10, textShadowColor: 'rgba(0,0,0,0.8)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 4 },
  actionBar: { position: 'absolute', right: 12, bottom: 20, alignItems: 'center', gap: 20, zIndex: 3 },
  actionItem: { alignItems: 'center', gap: 3 },
  actionText: { color: '#FFF', fontSize: 11, fontWeight: '500', textShadowColor: 'rgba(0,0,0,0.6)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 3 },
  authorRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  authorName: { color: '#FFF', fontSize: 13, fontWeight: '600', textShadowColor: 'rgba(0,0,0,0.8)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 4 },
  authorNameCard: { color: '#5A4A30', fontSize: 13, fontWeight: '600' },
  smallAvatar: { width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  pauseOverlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center', zIndex: 5 },
  pauseIconBg: { width: 70, height: 70, borderRadius: 35, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  musicDisc: { position: 'absolute', right: -56, bottom: 2 },
  musicDiscInner: { width: 32, height: 32, borderRadius: 16, borderWidth: 2, backgroundColor: '#222', justifyContent: 'center', alignItems: 'center' },

  // Story viewer
  storyModal: { flex: 1, backgroundColor: '#000' },
  storyContent: { flex: 1 },
  storyMedia: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%' },
  storyGradientTop: { position: 'absolute', top: 0, left: 0, right: 0, height: 140, backgroundColor: 'transparent', zIndex: 5,
    // Gradient effect via shadow overlay
    borderBottomWidth: 0, opacity: 1,
    ...Platform.select({ ios: { }, android: { } }),
  },
  storyGradientBottom: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 160, zIndex: 5, backgroundColor: 'rgba(0,0,0,0.45)' },
  storyProgress: { flexDirection: 'row', position: 'absolute', top: 50, left: 10, right: 10, gap: 4, zIndex: 20 },
  progressBar: { flex: 1, height: 2.5, borderRadius: 2, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#FFF', borderRadius: 2 },
  storyDomainBadge: { position: 'absolute', top: 100, alignSelf: 'center', flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, gap: 6, zIndex: 20 },
  storyDomainText: { color: '#FFF', fontSize: 11, fontWeight: '700', letterSpacing: 1 },
  storyHeader: { position: 'absolute', top: 60, left: 16, right: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', zIndex: 20 },
  storyHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  storyHeaderAvatar: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  storyHeaderName: { color: '#FFF', fontSize: 14, fontWeight: '600', textShadowColor: 'rgba(0,0,0,0.6)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 3 },
  storyHeaderTime: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
  storyCenter: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 30, zIndex: 10 },
  storyText: { color: '#FFF', fontSize: 24, fontWeight: '700', textAlign: 'center', lineHeight: 34, textShadowColor: 'rgba(0,0,0,0.7)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 4 },
  storyTapAreas: { position: 'absolute', top: 0, bottom: 80, left: 0, right: 0, flexDirection: 'row', zIndex: 15 },
  tapLeft: { flex: 1 }, tapRight: { flex: 1 },
  storyBottom: { position: 'absolute', bottom: 30, left: 16, right: 16, flexDirection: 'row', alignItems: 'center', gap: 12, zIndex: 25 },
  storyReplyInput: { flex: 1, height: 44, borderRadius: 22, borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.5)', paddingHorizontal: 16, color: '#FFF', fontSize: 14, backgroundColor: 'rgba(0,0,0,0.3)' },
  storyActionBtn: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },

  // Modals
  modalOverlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' },
  sheetHandle: { alignItems: 'center', paddingVertical: 12 },
  handleBar: { width: 40, height: 4, borderRadius: 2 },
  commentSheet: { borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: height * 0.65, paddingBottom: 20 },
  commentHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 0.5 },
  commentTitle: { fontSize: 16, fontWeight: '700' },
  commentsList: { paddingHorizontal: 16, flex: 1 },
  commentItem: { flexDirection: 'row', paddingVertical: 12, borderBottomWidth: 0.5, gap: 10 },
  commentAvatar: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  commentAvatarText: { fontSize: 14, fontWeight: '700' },
  commentContent: { flex: 1 },
  commentUser: { fontSize: 13, fontWeight: '600', marginBottom: 2 },
  commentBody: { fontSize: 14, lineHeight: 19 },
  commentInput: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 12, borderTopWidth: 0.5, gap: 10 },
  commentTextInput: { flex: 1, height: 42, borderRadius: 21, paddingHorizontal: 16, fontSize: 14, borderWidth: 1 },

  // Fullscreen button
  fullscreenBtn: { position: 'absolute', top: 12, right: 12, zIndex: 5, width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },

  // Video progress bar at bottom of reel — full width, tappable
  progressBarWrap: { position: 'absolute', bottom: 0, left: 0, width: width, height: 22, zIndex: 6, justifyContent: 'center' },
  progressBarTrack: { height: 3, backgroundColor: '#F9D84A', position: 'absolute', bottom: 10, left: 0 },
  progressDot: { position: 'absolute', bottom: 4, width: 14, height: 14, borderRadius: 7, backgroundColor: '#F9D84A', borderWidth: 2.5, borderColor: '#FFF', marginLeft: -7, elevation: 3 },

  // Fullscreen modal styles
  fsBackBtn: { position: 'absolute', top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 14 : 50, left: 16, zIndex: 10, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  fsPauseBtn: { position: 'absolute', top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 14 : 50, right: 16, zIndex: 10, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  fsTitle: { position: 'absolute', top: 54, left: 70, right: 16, zIndex: 10 },
  fsSlider: { position: 'absolute', bottom: 40, left: 20, right: 20, flexDirection: 'row', alignItems: 'center', gap: 10, zIndex: 10 },
  fsSliderTrack: { flex: 1, height: 30, justifyContent: 'center', overflow: 'visible' },
  fsSliderBg: { height: 5, backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 3, overflow: 'visible' },
  fsSliderFill: { height: 5, backgroundColor: '#F9D84A', borderRadius: 3 },
  fsSliderDot: { position: 'absolute', top: -5, width: 16, height: 16, borderRadius: 8, backgroundColor: '#F9D84A', borderWidth: 2.5, borderColor: '#FFF', marginLeft: -8, elevation: 4 },
  fsTime: { color: '#FFF', fontSize: 12, fontWeight: '600', minWidth: 35 },
});
