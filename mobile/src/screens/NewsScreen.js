import React, { useState, useEffect, useContext } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  StatusBar, Image, Dimensions, Share, Alert, RefreshControl,
  ScrollView, TextInput, KeyboardAvoidingView, Platform,
  ActivityIndicator, Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { contentAPI } from '../api';
import { AuthContext, ThemeContext } from '../../App';
import { Tape, Stamp, DoodleDivider, PaperCorner, SketchSectionHeader, StickyNote } from '../components/SketchComponents';

const { width } = Dimensions.get('window');
const HALF = (width - 48) / 2;

const CATEGORIES = [
  { id: 'all', label: 'ALL' },
  { id: 'technology', label: 'TECH' },
  { id: 'ai', label: 'AI' },
  { id: 'physics', label: 'PHYSICS' },
  { id: 'space', label: 'SPACE' },
  { id: 'biology', label: 'BIO' },
  { id: 'nature', label: 'NATURE' },
  { id: 'history', label: 'HISTORY' },
];

const DOMAIN_COLORS = {
  physics: '#D35400', nature: '#2ECC71', ai: '#1A9A7A',
  history: '#8E44AD', technology: '#3A5A9C', space: '#3A5A9C',
  biology: '#27AE60', mathematics: '#F39C12',
};

const ACCENT = '#F9D84A';

const fmtDate = (str) => {
  if (!str) {
    const d = new Date();
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    return `${months[d.getMonth()]} ${String(d.getDate()).padStart(2, '0')}, ${d.getFullYear()}`;
  }
  return str;
};

const fmtCount = (n) => n >= 1000 ? (n / 1000).toFixed(1) + 'K' : (n || 0).toString();

// Generate a consistent placeholder image for news items without thumbnails
const getNewsImage = (item) => {
  if (item.thumbnail_url && !item.thumbnail_url.startsWith('blob:')) return item.thumbnail_url;
  if (item.media_url && !item.media_url.startsWith('blob:')) return item.media_url;
  // Use picsum with a seed based on item id for consistent images
  const seed = item.id ? item.id.charCodeAt(0) + item.id.length : Math.floor(Math.random() * 1000);
  return `https://picsum.photos/seed/${seed}/600/400`;
};

export default function NewsScreen() {
  const { user } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [likes, setLikes] = useState({});
  const [saves, setSaves] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedNews, setSelectedNews] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState([]);

  useEffect(() => { fetchNews(); }, [selectedCategory]);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const params = { content_type: 'news', limit: 20 };
      if (selectedCategory !== 'all') params.domain = selectedCategory;
      const res = await contentAPI.list(params);
      setNews(res.data);
    } catch (e) { console.log('Fetch news failed', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  const toggleLike = async (id) => {
    const wasLiked = likes[id] || false;
    setLikes(p => ({ ...p, [id]: !wasLiked }));
    setNews(prev => prev.map(n => n.id === id ? { ...n, likes_count: (n.likes_count || 0) + (wasLiked ? -1 : 1) } : n));
    if (selectedNews?.id === id) setSelectedNews(prev => prev ? { ...prev, likes_count: (prev.likes_count || 0) + (wasLiked ? -1 : 1) } : prev);
    try { await contentAPI.interact(id, { interaction_type: 'like' }); }
    catch { setLikes(p => ({ ...p, [id]: wasLiked })); setNews(prev => prev.map(n => n.id === id ? { ...n, likes_count: (n.likes_count || 0) + (wasLiked ? 1 : -1) } : n)); }
  };

  const toggleSave = async (id) => {
    const wasSaved = saves[id] || false;
    setSaves(p => ({ ...p, [id]: !wasSaved }));
    try { await contentAPI.interact(id, { interaction_type: 'save' }); }
    catch { setSaves(p => ({ ...p, [id]: wasSaved })); }
  };

  const handleShare = async (t) => { try { await Share.share({ message: t }); } catch {} };

  const openDetail = async (item) => {
    setSelectedNews(item);
    try { const r = await contentAPI.listComments(item.id); setComments(r.data || []); } catch { setComments([]); }
    // Track view
    try {
      await contentAPI.interact(item.id, { interaction_type: 'view' });
      setNews(prev => prev.map(n => n.id === item.id ? { ...n, views_count: (n.views_count || 0) + 1 } : n));
      setSelectedNews(prev => prev ? { ...prev, views_count: (prev.views_count || 0) + 1 } : prev);
    } catch {}
  };

  const addComment = async () => {
    if (!commentText.trim()) return;
    const txt = commentText.trim();
    setCommentText('');
    try {
      await contentAPI.addComment(selectedNews.id, { body: txt });
      const res = await contentAPI.listComments(selectedNews.id);
      setComments(res.data || []);
      setNews(prev => prev.map(n => n.id === selectedNews.id ? { ...n, comments_count: (n.comments_count || 0) + 1 } : n));
      setSelectedNews(prev => prev ? { ...prev, comments_count: (prev.comments_count || 0) + 1 } : prev);
    } catch { Alert.alert('Error', 'Failed to post comment.'); }
  };

  // ─── DETAIL VIEW ─────────────────────────────────
  if (selectedNews) {
    const item = selectedNews;
    const dc = DOMAIN_COLORS[item.domain] || ACCENT;
    const liked = likes[item.id];
    const saved = saves[item.id];

    return (
      <View style={s.container}>
        {/* Notebook ruled lines */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.10)', zIndex: 0 }} pointerEvents="none" />
        <StatusBar barStyle="dark-content" backgroundColor="#FBF8F0" />

        {/* Header */}
        <View style={s.detailHeader}>
          <TouchableOpacity onPress={() => setSelectedNews(null)} style={s.detailHeaderBtn}>
            <Ionicons name="arrow-back" size={22} color="#2C1810" />
          </TouchableOpacity>
          <View style={{ flex: 1 }} />
          <TouchableOpacity onPress={() => handleShare(item.title)} style={s.detailHeaderBtn}>
            <Ionicons name="share-outline" size={20} color="#2C1810" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => toggleSave(item.id)} style={s.detailHeaderBtn}>
            <Ionicons name={saved ? 'bookmark' : 'bookmark-outline'} size={20} color={saved ? ACCENT : '#2C1810'} />
          </TouchableOpacity>
        </View>

        <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
          {/* Domain + Date */}
          <View style={s.detailTagRow}>
            <View style={s.detailTag}><Text style={s.detailTagText}>{(item.domain || 'NEWS').toUpperCase()}</Text></View>
            <Text style={s.detailDate}>{fmtDate()}</Text>
          </View>

          {/* Headline */}
          <Text style={s.detailHeadline}>{item.title}</Text>

          {/* Author */}
          <View style={s.detailAuthorRow}>
            <Text style={s.detailAuthorLabel}>Written by </Text>
            <Text style={s.detailAuthorName}>{item.author_username || 'ScrollUForward'}</Text>
          </View>

          {/* Hero image */}
          <Image source={{ uri: getNewsImage(item) }} style={s.detailHeroImg} />

          {/* Body */}
          <Text style={s.detailBody}>{item.body}</Text>

          {/* Source link */}
          {item.source_url && (
            <TouchableOpacity style={s.sourceLink} onPress={() => Linking.openURL(item.source_url)}>
              <Ionicons name="open-outline" size={16} color={ACCENT} />
              <Text style={s.sourceLinkText}>Read original source</Text>
              <Ionicons name="arrow-forward" size={14} color={ACCENT} />
            </TouchableOpacity>
          )}

          {/* Actions */}
          <View style={s.detailActions}>
            <TouchableOpacity style={s.detailActionBtn} onPress={() => toggleLike(item.id)}>
              <Ionicons name={liked ? 'heart' : 'heart-outline'} size={20} color={liked ? '#ED4956' : '#8A7860'} />
              <Text style={[s.detailActionText, liked && { color: '#ED4956' }]}>{fmtCount(item.likes_count || 0)}</Text>
            </TouchableOpacity>
            <View style={s.detailActionBtn}>
              <Ionicons name="eye-outline" size={18} color="#8A7860" />
              <Text style={s.detailActionText}>{fmtCount(item.views_count || 0)}</Text>
            </View>
            <View style={s.detailActionBtn}>
              <Ionicons name="chatbubble-outline" size={18} color="#8A7860" />
              <Text style={s.detailActionText}>{fmtCount(item.comments_count || 0)}</Text>
            </View>
            <TouchableOpacity style={s.detailActionBtn} onPress={() => handleShare(item.title)}>
              <Ionicons name="paper-plane-outline" size={18} color="#8A7860" />
              <Text style={s.detailActionText}>Share</Text>
            </TouchableOpacity>
          </View>

          {/* Comments */}
          <View style={s.detailDivider} />
          <Text style={s.commentsTitle}>Comments ({comments.length})</Text>
          <View style={s.commentInputRow}>
            <TextInput style={s.commentInput} placeholder="Write a comment..." placeholderTextColor="#8A7860"
              value={commentText} onChangeText={setCommentText} />
            <TouchableOpacity style={[s.commentSend, { backgroundColor: commentText.trim() ? ACCENT : '#E0D9D0' }]} onPress={addComment}>
              <Ionicons name="arrow-up" size={18} color={commentText.trim() ? '#2C1810' : '#8A7860'} />
            </TouchableOpacity>
          </View>
          {comments.map(c => (
            <View key={c.id} style={s.commentCard}>
              <View style={s.commentAvatar}><Text style={s.commentAvatarText}>{c.username?.[0]?.toUpperCase()}</Text></View>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                  <Text style={s.commentUser}>{c.username}</Text>
                  <Text style={s.commentTime}>{c.time || 'recently'}</Text>
                </View>
                <Text style={s.commentBody}>{c.body}</Text>
              </View>
            </View>
          ))}
          <View style={{ height: 80 }} />
        </ScrollView>
      </View>
    );
  }

  // ─── LIST VIEW — Magazine Layout ─────────────────
  const featured = news[0];
  const stories = news.slice(1, 3);
  const rest = news.slice(3);

  return (
    <View style={s.container}>
        {/* Notebook margin */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)', zIndex: 0 }} pointerEvents="none" />
      <StatusBar barStyle="dark-content" backgroundColor="#FBF8F0" />

      <ScrollView showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchNews(); }} tintColor={ACCENT} />}>

        {/* Masthead — notebook style */}
        <View style={s.masthead}>
          <View>
            <View style={{ flexDirection: 'row', gap: 4, marginBottom: 4 }}>
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            </View>
            <Text style={s.mastheadTitle}>SCROLL<Text style={{ color: '#3A5A9C' }}>U</Text> NEWS</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
              <View style={{ height: 2.5, backgroundColor: '#F9D84A', width: 40, borderRadius: 2 }} />
              <View style={{ height: 1, backgroundColor: '#C8BFA8', width: 60, marginLeft: 4 }} />
            </View>
          </View>
          <TouchableOpacity style={s.createNewsBtn}>
            <Ionicons name="add" size={18} color="#2C1810" />
            <Text style={s.createNewsBtnText}>Create</Text>
          </TouchableOpacity>
        </View>

        {/* Category tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.catRow}>
          {CATEGORIES.map(c => {
            const active = selectedCategory === c.id;
            return (
              <TouchableOpacity key={c.id} style={[s.catChip, active && s.catChipActive]} onPress={() => setSelectedCategory(c.id)}>
                <Text style={[s.catChipText, active && s.catChipTextActive]}>{c.label}{c.id === 'all' ? ` (${news.length})` : ''}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {loading && <ActivityIndicator color={ACCENT} size="large" style={{ marginTop: 60 }} />}

        {!loading && news.length === 0 && (
          <View style={{ height: 300, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '-3deg' }], marginBottom: 16 }}>
              <Ionicons name="newspaper-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>No news yet</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>The newsroom is quiet! Fresh stories will land here soon — stay tuned.</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        )}

        {/* STORIES header */}
        {!loading && news.length > 0 && (
          <>
            <View style={s.storiesHeader}>
              <Text style={s.storiesTitle}>STO{'\n'}RIES</Text>
              {/* Featured hero */}
              {featured && (
                <TouchableOpacity style={s.heroCard} onPress={() => openDetail(featured)}>
                  <Tape color="yellow" style={{ left: 20 }} width={60} />
                  <Image source={{ uri: getNewsImage(featured) }} style={s.heroImg} />
                  <PaperCorner />
                </TouchableOpacity>
              )}
            </View>

            {/* Featured title below */}
            {featured && (
              <TouchableOpacity style={s.featuredInfo} onPress={() => openDetail(featured)}>
                <View style={s.tagDateRow}>
                  <Stamp domain={featured.domain} label={(featured.domain || 'NEWS').toUpperCase()} />
                  <Text style={s.dateText}>{fmtDate()}</Text>
                </View>
                <Text style={s.featuredTitle} numberOfLines={3}>{featured.title}</Text>
                <Text style={s.featuredAuthor}>Written by <Text style={{ fontStyle: 'italic' }}>{featured.author_username || 'ScrollUForward'}</Text></Text>
              </TouchableOpacity>
            )}

            <DoodleDivider style={{ marginHorizontal: 20, marginVertical: 4 }} />

            {/* VIEW ALL row */}
            <View style={s.viewAllRow}>
              <View style={{ flex: 1 }}>
                {stories[0] && (
                  <TouchableOpacity onPress={() => openDetail(stories[0])}>
                    <Image source={{ uri: getNewsImage(stories[0]) }} style={s.storyImg} />
                    <Text style={s.storyTitle} numberOfLines={2}>{stories[0].title}</Text>
                  </TouchableOpacity>
                )}
              </View>
              <View style={s.viewAllBox}>
                <Text style={s.viewAllLabel}>VIEW ALL</Text>
                <Ionicons name="arrow-forward" size={18} color="#2C1810" />
              </View>
            </View>

            {/* Second story row */}
            {stories[1] && (
              <TouchableOpacity style={s.wideStory} onPress={() => openDetail(stories[1])}>
                <Image source={{ uri: getNewsImage(stories[1]) }} style={s.wideStoryImg} />
                <View style={s.wideStoryInfo}>
                  <View style={s.tagDateRow}>
                    <View style={s.tag}><Text style={s.tagText}>{(stories[1].domain || 'NEWS').toUpperCase()}</Text></View>
                    <Text style={s.dateText}>{fmtDate()}</Text>
                  </View>
                  <Text style={s.wideStoryTitle} numberOfLines={3}>{stories[1].title}</Text>
                  <Text style={s.featuredAuthor}>Written by <Text style={{ fontStyle: 'italic' }}>{stories[1].author_username || 'ScrollUForward'}</Text></Text>
                </View>
              </TouchableOpacity>
            )}

            <SketchSectionHeader title="More Stories" style={{ marginTop: 8 }} />

            {/* Remaining articles — editorial list */}
            {rest.map((item, i) => (
              <TouchableOpacity key={item.id} style={s.editorialCard} onPress={() => openDetail(item)}>
                <Tape color={['blue','purple','green','red','yellow'][i % 5]} style={{ right: 15, left: 'auto' }} width={45} />
                <Image source={{ uri: getNewsImage(item) }} style={s.editorialImg} />
                <View style={s.tagDateRow}>
                  <Stamp domain={item.domain} label={(item.domain || 'NEWS').toUpperCase()} />
                  <Text style={s.dateText}>{fmtDate()}</Text>
                </View>
                <Text style={s.editorialTitle} numberOfLines={3}>{item.title}</Text>
                <Text style={s.editorialBody} numberOfLines={2}>{item.body}</Text>
                <View style={s.editorialFooter}>
                  <Text style={s.featuredAuthor}>Written by <Text style={{ fontStyle: 'italic' }}>{item.author_username || 'ScrollUForward'}</Text></Text>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                      <Ionicons name="eye-outline" size={14} color="#666" />
                      <Text style={{ fontSize: 11, color: '#8A7860' }}>{fmtCount(item.views_count || 0)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                      <Ionicons name="heart-outline" size={14} color="#666" />
                      <Text style={{ fontSize: 11, color: '#8A7860' }}>{fmtCount(item.likes_count || 0)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                      <Ionicons name="chatbubble-outline" size={13} color="#666" />
                      <Text style={{ fontSize: 11, color: '#8A7860' }}>{fmtCount(item.comments_count || 0)}</Text>
                    </View>
                    <TouchableOpacity onPress={() => toggleSave(item.id)}>
                      <Ionicons name={saves[item.id] ? 'bookmark' : 'bookmark-outline'} size={18} color={saves[item.id] ? ACCENT : '#999'} />
                    </TouchableOpacity>
                  </View>
                </View>
                {i < rest.length - 1 && <View style={s.editorialDivider} />}
              </TouchableOpacity>
            ))}

            {/* Footer */}
            <View style={s.footer}>
              <Text style={s.footerBrand}>SCROLL<Text style={{ color: ACCENT }}>U</Text>FORWARD</Text>
              <Text style={s.footerDesc}>Curated science & knowledge news from 200+ verified sources. No opinion, no clickbait.</Text>
              <View style={s.footerLinks}>
                {['TECH', 'AI', 'PHYSICS', 'NATURE', 'HISTORY', 'SPACE'].map(l => (
                  <Text key={l} style={s.footerLink}>{l}</Text>
                ))}
              </View>
            </View>
          </>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Masthead
  masthead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 54, paddingBottom: 12 },
  mastheadTitle: { fontSize: 22, fontWeight: '900', color: '#2C1810', letterSpacing: 3 },
  createNewsBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFD60A', paddingHorizontal: 14, paddingVertical: 8, gap: 4, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 },
  createNewsBtnText: { fontSize: 13, fontWeight: '700', color: '#2C1810' },

  // Categories — sketch chips
  catRow: { paddingHorizontal: 16, paddingVertical: 12, gap: 8 },
  catChip: { paddingHorizontal: 16, paddingVertical: 8, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2, ...Platform.select({ ios: { shadowColor: '#B8AE90', shadowOffset: { width: 1.5, height: 2 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 2 } }) },
  catChipActive: { backgroundColor: '#FFD60A', borderColor: '#2C1810' },
  catChipText: { fontSize: 11, fontWeight: '700', color: '#8A7860', letterSpacing: 0.8 },
  catChipTextActive: { color: '#2C1810' },

  // Stories hero — sketch card
  storiesHeader: { flexDirection: 'row', paddingHorizontal: 20, marginTop: 16, gap: 16, alignItems: 'flex-end' },
  storiesTitle: { fontSize: 64, fontWeight: '900', color: '#2C1810', lineHeight: 68, letterSpacing: -2 },
  heroCard: { flex: 1, height: 200, overflow: 'hidden', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  heroImg: { width: '100%', height: '100%' },

  // Featured
  featuredInfo: { paddingHorizontal: 20, marginTop: 16, marginBottom: 20 },
  tagDateRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  tag: { paddingHorizontal: 9, paddingVertical: 3, borderWidth: 2, borderColor: '#F9D84A', borderRadius: 3, transform: [{ rotate: '-1.5deg' }] },
  tagText: { fontSize: 10, fontWeight: '800', color: '#5A4A30', letterSpacing: 1.2, textTransform: 'uppercase' },
  dateText: { fontSize: 11, color: '#8A7860', fontWeight: '500' },
  featuredTitle: { fontSize: 22, fontWeight: '800', color: '#2C1810', lineHeight: 28, marginBottom: 8 },
  featuredAuthor: { fontSize: 12, color: '#8A7860' },

  // View all + story grid
  viewAllRow: { flexDirection: 'row', paddingHorizontal: 20, gap: 12, marginBottom: 20 },
  storyImg: { width: '100%', height: 140, marginBottom: 8, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  storyTitle: { fontSize: 14, fontWeight: '700', color: '#2C1810', lineHeight: 20 },
  viewAllBox: { width: 100, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F9D84A', gap: 6, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  viewAllLabel: { fontSize: 12, fontWeight: '800', color: '#2C1810', letterSpacing: 1 },

  // Wide story
  wideStory: { flexDirection: 'row', paddingHorizontal: 20, gap: 14, marginBottom: 24 },
  wideStoryImg: { width: 140, height: 160, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  wideStoryInfo: { flex: 1, justifyContent: 'center' },
  wideStoryTitle: { fontSize: 16, fontWeight: '700', color: '#2C1810', lineHeight: 22, marginBottom: 8 },

  // Editorial list — sketch cards
  editorialCard: { marginHorizontal: 16, marginBottom: 14, padding: 14, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, backgroundColor: '#FFFCF2', ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  editorialImg: { width: '100%', height: 180, marginBottom: 12, borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 2, borderBottomRightRadius: 8 },
  editorialTitle: { fontSize: 22, fontWeight: '900', color: '#2C1810', lineHeight: 26, marginBottom: 6, textTransform: 'uppercase' },
  editorialBody: { fontSize: 13, lineHeight: 20, color: '#8A7860', marginBottom: 10 },
  editorialFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  editorialDivider: { height: 0, marginTop: 0 },

  // Footer
  footer: { paddingHorizontal: 20, paddingTop: 30, paddingBottom: 20, borderTopWidth: 1, borderTopColor: '#C8BFA8', marginTop: 10 },
  footerBrand: { fontSize: 28, fontWeight: '900', color: '#2C1810', letterSpacing: 2, marginBottom: 8 },
  footerDesc: { fontSize: 12, lineHeight: 18, color: '#8A7860', marginBottom: 16 },
  footerLinks: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
  footerLink: { fontSize: 11, fontWeight: '700', color: '#2C1810', letterSpacing: 0.8 },

  // ─── DETAIL VIEW ──────────────────
  detailHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 54, paddingBottom: 10, gap: 8 },
  detailHeaderBtn: { padding: 8, color: '#2C1810', borderWidth: 1.5, borderColor: '#2C1810', borderRadius: 8, backgroundColor: '#FFFCF2' },
  detailTagRow: { paddingHorizontal: 20, marginBottom: 12 },
  detailTag: { paddingHorizontal: 9, paddingVertical: 3, borderWidth: 2, borderColor: '#F9D84A', borderRadius: 3, alignSelf: 'flex-start', marginBottom: 8, transform: [{ rotate: '-1.5deg' }] },
  detailTagText: { fontSize: 10, fontWeight: '800', color: '#5A4A30', letterSpacing: 1.2, textTransform: 'uppercase' },
  detailDate: { fontSize: 11, color: '#8A7860', fontWeight: '500' },
  detailHeadline: { fontSize: 30, fontWeight: '900', color: '#2C1810', lineHeight: 36, paddingHorizontal: 20, marginBottom: 10, letterSpacing: -0.5 },
  detailAuthorRow: { flexDirection: 'row', paddingHorizontal: 20, marginBottom: 20 },
  detailAuthorLabel: { fontSize: 13, color: '#8A7860' },
  detailAuthorName: { fontSize: 13, color: '#2C1810', fontWeight: '600', fontStyle: 'italic' },
  detailHeroImg: { width: width - 40, height: 220, marginHorizontal: 20, marginBottom: 20, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  detailBody: { fontSize: 17, lineHeight: 30, color: '#5A4A30', paddingHorizontal: 20, marginBottom: 20 },

  sourceLink: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: ACCENT + '12', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 12, marginHorizontal: 20, marginBottom: 20, borderWidth: 1, borderColor: ACCENT + '30' },
  sourceLinkText: { flex: 1, fontSize: 14, fontWeight: '600', color: ACCENT },

  detailActions: { flexDirection: 'row', gap: 20, paddingHorizontal: 20, marginBottom: 20 },
  detailActionBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2 },
  detailActionText: { fontSize: 13, color: '#8A7860', fontWeight: '500' },

  detailDivider: { height: 1, backgroundColor: '#C8BFA8', marginHorizontal: 20, marginBottom: 20 },

  commentsTitle: { fontSize: 18, fontWeight: '700', color: '#2C1810', paddingHorizontal: 20, marginBottom: 14 },
  commentInputRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 20, marginBottom: 16 },
  commentInput: { flex: 1, height: 42, borderRadius: 21, paddingHorizontal: 16, fontSize: 14, backgroundColor: '#F8F6F0', color: '#2C1810', borderWidth: 2, borderColor: '#C8BFA8' },
  commentSend: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  commentCard: { flexDirection: 'row', paddingHorizontal: 20, paddingVertical: 10, gap: 10, borderBottomWidth: 0.5, borderBottomColor: '#C8BFA8' },
  commentAvatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: ACCENT + '20', justifyContent: 'center', alignItems: 'center' },
  commentAvatarText: { fontSize: 13, fontWeight: '700', color: ACCENT },
  commentUser: { fontSize: 13, fontWeight: '600', color: '#2C1810' },
  commentTime: { fontSize: 11, color: '#8A7860' },
  commentBody: { fontSize: 14, lineHeight: 20, color: '#8A7860', marginTop: 2 },
});
