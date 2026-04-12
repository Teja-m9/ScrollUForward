import React, { useState, useEffect, useRef, useContext } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  StatusBar, TextInput, Dimensions, ActivityIndicator, Image, Platform, Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ThemeContext } from '../../App';
import { AuthContext } from '../../App';
import { contentAPI, usersAPI } from '../api';
import { Tape, Stamp, SketchCard, DoodleDivider, PencilLine, PageHeader, StickerBadge } from '../components/SketchComponents';

const { width } = Dimensions.get('window');
const ACCENT = '#F9D84A';

const CATEGORIES = [
  { id: 'all', label: 'All', icon: 'grid' },
  { id: 'technology', label: 'Tech', icon: 'code-slash' },
  { id: 'ai', label: 'AI', icon: 'hardware-chip' },
  { id: 'physics', label: 'Physics', icon: 'planet' },
  { id: 'nature', label: 'Nature', icon: 'leaf' },
  { id: 'history', label: 'History', icon: 'library' },
  { id: 'space', label: 'Space', icon: 'rocket' },
  { id: 'biology', label: 'Biology', icon: 'flask' },
  { id: 'mathematics', label: 'Math', icon: 'calculator' },
];

const DOMAIN_COLORS = {
  physics: '#D35400', nature: '#27AE60', ai: '#1A9A7A',
  history: '#8E44AD', technology: '#3A5A9C', space: '#3A5A9C',
  biology: '#27AE60', mathematics: '#F39C12', philosophy: '#8E44AD',
  engineering: '#E67E22', chemistry: '#16A085', ancient_civilizations: '#D35400',
};

const getImage = (item, i) => {
  if (item?.thumbnail_url && !item.thumbnail_url.startsWith('blob:')) return item.thumbnail_url;
  if (item?.media_url && !item.media_url.startsWith('blob:')) return item.media_url;
  return `https://picsum.photos/seed/explore${i}/400/300`;
};

export default function ExploreScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchResults, setSearchResults] = useState([]);
  const [peopleResults, setPeopleResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(true);
  const searchRef = useRef(null);

  // Trending topics ticker
  const TRENDING = [
    { label: 'Quantum Computing', icon: 'hardware-chip', hot: true },
    { label: 'Mars Colonization', icon: 'rocket', hot: false },
    { label: 'GPT-5 Rumors', icon: 'sparkles', hot: true },
    { label: 'CRISPR Advances', icon: 'flask', hot: false },
    { label: 'Dark Matter Discovery', icon: 'planet', hot: true },
    { label: 'Neural Interfaces', icon: 'pulse', hot: false },
    { label: 'Fusion Energy', icon: 'flash', hot: true },
  ];
  const tickerScroll = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const tickerWidth = TRENDING.length * 160;
    Animated.loop(
      Animated.timing(tickerScroll, { toValue: -tickerWidth, duration: tickerWidth * 30, useNativeDriver: true })
    ).start();
  }, []);

  useEffect(() => { fetchContent(); }, [selectedCategory]);

  useEffect(() => {
    if (searchQuery.trim().length > 1) {
      const t = setTimeout(() => universalSearch(), 400);
      return () => clearTimeout(t);
    } else if (!searchQuery.trim()) {
      setSearchResults([]);
      setPeopleResults([]);
    }
  }, [searchQuery]);

  const fetchContent = async () => {
    setLoading(true);
    try {
      const params = { limit: 20 };
      if (selectedCategory !== 'all') params.domain = selectedCategory;
      const res = await contentAPI.list(params);
      setContent(res.data || []);
    } catch { setContent([]); }
    finally { setLoading(false); }
  };

  const universalSearch = async () => {
    setSearching(true);
    const query = searchQuery.trim().toLowerCase();
    try {
      // Try API search first, fall back to fetching all content and filtering locally
      const [contentRes, peopleRes] = await Promise.allSettled([
        contentAPI.search({ q: searchQuery, limit: 30 }).catch(async () => {
          // Fallback: fetch all content and filter client-side
          const all = await contentAPI.list({ limit: 100 });
          const filtered = (all.data || []).filter(item =>
            (item.title || '').toLowerCase().includes(query) ||
            (item.body || '').toLowerCase().includes(query) ||
            (item.domain || '').toLowerCase().includes(query) ||
            (item.author_username || '').toLowerCase().includes(query) ||
            (item.tags || []).some(t => t.toLowerCase().includes(query))
          );
          return { data: filtered };
        }),
        usersAPI.leaderboard(50),
      ]);

      // Content results
      if (contentRes.status === 'fulfilled') {
        setSearchResults(contentRes.value.data || []);
      } else {
        setSearchResults([]);
      }

      // People results — filter leaderboard by username/display_name
      if (peopleRes.status === 'fulfilled') {
        const allUsers = peopleRes.value.data || [];
        const filtered = allUsers.filter(u =>
          (u.username || '').toLowerCase().includes(query) ||
          (u.display_name || '').toLowerCase().includes(query)
        );
        setPeopleResults(filtered);
      } else {
        setPeopleResults([]);
      }
    } catch {
      setSearchResults([]);
      setPeopleResults([]);
    } finally {
      setSearching(false);
    }
  };

  const navigateToContent = (item) => {
    if (!item || !navigation) return;
    const type = item.content_type;
    if (type === 'reel') {
      navigation.navigate('Home'); // Reels tab
    } else if (type === 'article') {
      navigation.navigate('Articles');
    } else if (type === 'news') {
      navigation.navigate('News');
    } else {
      navigation.navigate('Home');
    }
  };

  const isSearchActive = searchQuery.trim().length > 1;
  const displayItems = isSearchActive ? searchResults : content;
  const featured = displayItems[0];
  const gridItems = displayItems.slice(1);

  const renderPeopleResults = () => {
    if (!isSearchActive || peopleResults.length === 0) return null;
    return (
      <View style={s.sectionWrap}>
        <Text style={s.sectionTitle}>People</Text>
        {peopleResults.map((person, i) => (
          <TouchableOpacity
            key={person.user_id || i}
            style={s.personRow}
            activeOpacity={0.7}
            onPress={() => navigation && navigation.navigate('UserProfile', { userId: person.user_id })}
          >
            <View style={s.personAvatar}>
              {person.avatar_url ? (
                <Image source={{ uri: person.avatar_url }} style={s.personAvatarImg} />
              ) : (
                <Ionicons name="person" size={20} color="#8A7860" />
              )}
            </View>
            <View style={s.personInfo}>
              <Text style={s.personName} numberOfLines={1}>
                {person.display_name || person.username || 'User'}
              </Text>
              <Text style={s.personUsername} numberOfLines={1}>
                @{person.username || 'unknown'}
              </Text>
            </View>
            <View style={s.personBadge}>
              <Text style={s.personBadgeText}>{person.knowledge_rank || 'Novice'}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderContentResults = () => {
    if (!featured && !isSearchActive) return null;
    return (
      <>
        {isSearchActive && displayItems.length > 0 && (
          <Text style={[s.sectionTitle, { paddingHorizontal: 16, marginTop: 8 }]}>Content</Text>
        )}

        {featured && (
          <>
            {/* Featured card — sketch style */}
            <TouchableOpacity style={s.featuredCard} activeOpacity={0.9} onPress={() => navigateToContent(featured)}>
              <Tape color="blue" style={{ left: 30 }} />
              <Image source={{ uri: getImage(featured, 0) }} style={s.featuredImg} />
              <View style={s.featuredOverlay}>
                <Stamp domain={featured.domain} style={{ marginBottom: 8 }} />
                <Text style={s.featuredTitle} numberOfLines={3}>{featured.title}</Text>
                <View style={s.featuredMeta}>
                  <Ionicons name={featured.content_type === 'reel' ? 'play-circle' : 'document-text'} size={14} color="#E0D8C8" />
                  <Text style={s.featuredMetaText}>{featured.content_type}</Text>
                  <Text style={s.featuredMetaDot}>·</Text>
                  <Text style={s.featuredMetaText}>@{featured.author_username || 'author'}</Text>
                </View>
              </View>
            </TouchableOpacity>

            {/* Content grid — 2 columns */}
            <View style={s.grid}>
              {gridItems.map((item, i) => {
                const dc = DOMAIN_COLORS[item.domain] || ACCENT;
                return (
                  <TouchableOpacity key={item.id || i} style={s.gridCard} activeOpacity={0.85} onPress={() => navigateToContent(item)}>
                    <Tape color={i % 3 === 0 ? 'blue' : i % 3 === 1 ? 'yellow' : 'purple'} style={{ left: 15, width: 40 }} />
                    <Image source={{ uri: getImage(item, i + 1) }} style={s.gridImg} />
                    <View style={s.gridCardBody}>
                      <Stamp domain={item.domain} style={{ marginBottom: 6 }} />
                      <Text style={s.gridTitle} numberOfLines={2}>{item.title}</Text>
                      <View style={s.gridMeta}>
                        <Text style={s.gridMetaText}>@{item.author_username || 'author'}</Text>
                        {item.content_type === 'reel' && <Ionicons name="play-circle" size={12} color="#8A7860" />}
                      </View>
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          </>
        )}
      </>
    );
  };

  return (
    <View style={s.container}>
      {/* Notebook margin line */}
      <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)', zIndex: 0 }} pointerEvents="none" />
      <StatusBar barStyle="dark-content" backgroundColor="#FBF8F0" />

      {/* Header — notebook style with decorative dots */}
      <View style={s.header}>
        <View style={s.headerLeft}>
          <TouchableOpacity
            style={s.avatarSmall}
            activeOpacity={0.7}
            onPress={() => navigation && navigation.navigate('Profile')}
          >
            <Ionicons name="person" size={18} color="#8A7860" />
          </TouchableOpacity>
          <View>
            <Text style={s.welcomeText}>{user?.username || 'Scholar'}</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Text style={s.welcomeTitle}>Explore</Text>
              <View style={{ flexDirection: 'row', gap: 4, marginTop: 2 }}>
                <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
                <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
                <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
              </View>
            </View>
          </View>
        </View>
      </View>

      {/* Universal Search */}
      <View style={s.searchWrap}>
        <View style={[s.searchBar, isSearchFocused && s.searchBarFocused]}>
          <Ionicons name="search" size={18} color="#8A7860" />
          <TextInput
            ref={searchRef}
            style={s.searchInput}
            placeholder="Search content, people, topics..."
            placeholderTextColor="#8A7860"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => { setSearchQuery(''); setPeopleResults([]); }}>
              <Ionicons name="close-circle" size={18} color="#8A7860" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Trending ticker */}
      <View style={s.tickerWrap}>
        <View style={s.tickerLabel}>
          <Ionicons name="trending-up" size={13} color="#2C1810" />
          <Text style={s.tickerLabelText}>TRENDING</Text>
        </View>
        <View style={s.tickerTrack}>
          <Animated.View style={{ flexDirection: 'row', transform: [{ translateX: tickerScroll }] }}>
            {[...TRENDING, ...TRENDING].map((t, i) => (
              <TouchableOpacity key={i} style={[s.tickerItem, t.hot && s.tickerItemHot]} activeOpacity={0.7}
                onPress={() => { setSearchQuery(t.label); }}>
                <Ionicons name={t.icon} size={12} color={t.hot ? '#D35400' : '#5A4A30'} />
                <Text style={[s.tickerItemText, t.hot && { color: '#D35400' }]} numberOfLines={1}>{t.label}</Text>
                {t.hot && <View style={s.tickerHotDot} />}
              </TouchableOpacity>
            ))}
          </Animated.View>
        </View>
      </View>

      <PencilLine style={{ marginHorizontal: 16, marginVertical: 2 }} />

      {/* Category chips — wrapping layout */}
      <View style={s.catWrap}>
        {CATEGORIES.map(c => {
          const active = selectedCategory === c.id;
          return (
            <TouchableOpacity key={c.id} style={[s.catChip, active && s.catChipActive]} onPress={() => setSelectedCategory(c.id)}>
              <Text style={[s.catChipText, active && s.catChipTextActive]}>{c.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        {(loading || searching) && <ActivityIndicator color={ACCENT} size="large" style={{ marginTop: 40 }} />}

        {!loading && !searching && isSearchActive && displayItems.length === 0 && peopleResults.length === 0 && (
          <View style={{ height: 280, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '-2deg' }], marginBottom: 16 }}>
              <Ionicons name="search-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>No results found</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>We searched every corner but came up empty. Try different keywords!</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        )}

        {!loading && !searching && !isSearchActive && displayItems.length === 0 && (
          <View style={{ height: 280, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '3deg' }], marginBottom: 16 }}>
              <Ionicons name="telescope-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>Nothing to explore</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>The universe of content awaits! Check back soon for fresh discoveries.</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        )}

        {!loading && !searching && (
          <>
            {/* People section appears first in search */}
            {renderPeopleResults()}

            {/* Content section */}
            {renderContentResults()}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Trending ticker
  tickerWrap: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, overflow: 'hidden', height: 32 },
  tickerLabel: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    backgroundColor: '#FFD60A', paddingHorizontal: 8, paddingVertical: 4,
    borderWidth: 1.5, borderColor: '#2C1810', borderRadius: 3,
    transform: [{ rotate: '-2deg' }], zIndex: 2, marginRight: 8,
  },
  tickerLabelText: { fontSize: 9, fontWeight: '800', color: '#2C1810', letterSpacing: 1 },
  tickerTrack: { flex: 1, overflow: 'hidden' },
  tickerItem: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 4, marginRight: 8,
    borderWidth: 1, borderColor: '#C8BFA8', borderRadius: 3,
    backgroundColor: '#FFFCF2',
  },
  tickerItemHot: { borderColor: '#D35400', backgroundColor: '#FFF5EE' },
  tickerItemText: { fontSize: 11, fontWeight: '600', color: '#5A4A30' },
  tickerHotDot: { width: 5, height: 5, borderRadius: 1, backgroundColor: '#D35400', transform: [{ rotate: '45deg' }] },

  // Header
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 54, paddingBottom: 8 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarSmall: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F8F6F0', borderWidth: 1.5, borderColor: '#2C1810', justifyContent: 'center', alignItems: 'center' },
  welcomeText: { fontSize: 12, color: '#8A7860' },
  welcomeTitle: { fontSize: 24, fontWeight: '900', color: '#2C1810', letterSpacing: -0.5 },

  // Search — sketch style asymmetric border
  searchWrap: { paddingHorizontal: 16, paddingVertical: 10 },
  searchBar: { flexDirection: 'row', alignItems: 'center', height: 48, paddingHorizontal: 16, gap: 10, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 3 } }) },
  searchBarFocused: { borderColor: '#F9D84A' },
  searchInput: { flex: 1, fontSize: 15, color: '#2C1810' },

  // Categories — sketch chips with asymmetric border
  catWrap: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, paddingBottom: 12, gap: 8 },
  catChip: { paddingHorizontal: 16, paddingVertical: 8, borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#2C1810', ...Platform.select({ ios: { shadowColor: '#B8AE90', shadowOffset: { width: 1.5, height: 2 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 2 } }) },
  catChipActive: { backgroundColor: '#FFD60A', borderColor: '#2C1810', borderWidth: 2, transform: [{ rotate: '-1deg' }] },
  catChipText: { fontSize: 13, fontWeight: '600', color: '#8A7860' },
  catChipTextActive: { color: '#2C1810' },

  // Section headers
  sectionWrap: { paddingHorizontal: 16, marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: ACCENT, marginBottom: 10, marginTop: 4 },

  // People results
  personRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#C8BFA8' },
  personAvatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#F8F6F0', borderWidth: 1.5, borderColor: '#2C1810', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' },
  personAvatarImg: { width: 44, height: 44, borderRadius: 22 },
  personInfo: { flex: 1, marginLeft: 12 },
  personName: { fontSize: 15, fontWeight: '600', color: '#2C1810' },
  personUsername: { fontSize: 13, color: '#666', marginTop: 2 },
  personBadge: { paddingHorizontal: 10, paddingVertical: 4, borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2, borderWidth: 1, borderColor: ACCENT, backgroundColor: ACCENT + '12' },
  personBadgeText: { fontSize: 11, fontWeight: '600', color: '#5A4A30' },

  // Featured — sketch card
  featuredCard: { marginHorizontal: 16, overflow: 'hidden', height: 240, marginBottom: 16, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  featuredImg: { width: '100%', height: '100%' },
  featuredOverlay: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16, backgroundColor: 'rgba(0,0,0,0.55)' },
  featuredTitle: { fontSize: 20, fontWeight: '800', color: '#FFF', lineHeight: 26, marginBottom: 6, letterSpacing: -0.3 },
  featuredMeta: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  featuredMetaText: { fontSize: 12, color: '#CCC' },
  featuredMetaDot: { color: '#888' },

  // Grid — sketch cards with asymmetric border + ink shadow
  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 10, justifyContent: 'space-between' },
  gridCard: { width: (width - 30) / 2, backgroundColor: '#FFFCF2', overflow: 'hidden', marginBottom: 12, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 14, borderBottomLeftRadius: 14, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  gridImg: { width: '100%', height: 130 },
  gridCardBody: { padding: 12, borderTopWidth: 1, borderTopColor: 'rgba(90,150,210,0.10)' },
  gridTitle: { fontSize: 13, fontWeight: '600', color: '#2C1810', lineHeight: 18, marginBottom: 6 },
  gridMeta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  gridMetaText: { fontSize: 11, color: '#8A7860' },
});
