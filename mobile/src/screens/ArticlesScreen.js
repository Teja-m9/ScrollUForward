import React, { useState, useEffect, useContext, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  StatusBar, ScrollView, RefreshControl, TextInput,
  KeyboardAvoidingView, Platform, Alert, Dimensions,
  Image, ActivityIndicator, Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ThemeContext } from '../../App';
import { contentAPI } from '../api';
import { AuthContext } from '../../App';
import { Tape, Stamp, DoodleDivider, PaperCorner, SketchSectionHeader } from '../components/SketchComponents';
import { SkeletonCard, EmptyState, FadeInView } from '../components/AnimatedComponents';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';

const { width, height } = Dimensions.get('window');

const SERIF_FONT = Platform.OS === 'ios' ? 'Georgia' : 'serif';

const CATEGORIES = [
  { id: 'all', label: 'All', icon: 'grid-outline' },
  { id: 'technology', label: 'Tech', icon: 'code-slash' },
  { id: 'ai', label: 'AI', icon: 'hardware-chip' },
  { id: 'history', label: 'History', icon: 'library' },
  { id: 'nature', label: 'Nature', icon: 'leaf' },
  { id: 'physics', label: 'Physics', icon: 'planet' },
  { id: 'space', label: 'Space', icon: 'rocket' },
  { id: 'biology', label: 'Biology', icon: 'flask' },
  { id: 'mathematics', label: 'Math', icon: 'calculator' },
];

const DOMAIN_COLORS = {
  physics: '#D35400', nature: '#27AE60', ai: '#1A9A7A',
  history: '#8E44AD', technology: '#3A5A9C', space: '#3A5A9C',
  biology: '#27AE60', mathematics: '#F39C12',
};

const DOMAIN_GRADIENTS = {
  physics: ['#D35400', '#E67E22'],
  nature: ['#2ECC71', '#27AE60'],
  ai: ['#1A9A7A', '#16A085'],
  history: ['#D4A843', '#B8860B'],
  technology: ['#3A5A9C', '#2E4A7C'],
  space: ['#3A5A9C', '#2E4A7C'],
  biology: ['#27AE60', '#229954'],
  mathematics: ['#F39C12', '#E67E22'],
};

// Rich markdown renderer with images, tables, blockquotes, lists, bold, italic
const renderInlineFormatting = (text, baseStyle) => {
  if (!text) return null;
  // Split by bold **text** and italic *text* patterns
  const parts = [];
  let remaining = text;
  let keyIdx = 0;
  while (remaining.length > 0) {
    // Bold: **text**
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Italic: *text* (but not **)
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/);

    let firstMatch = null;
    let matchType = null;
    if (boldMatch && (!italicMatch || boldMatch.index <= italicMatch.index)) {
      firstMatch = boldMatch; matchType = 'bold';
    } else if (italicMatch) {
      firstMatch = italicMatch; matchType = 'italic';
    }

    if (!firstMatch) {
      parts.push(<Text key={keyIdx++} style={baseStyle}>{remaining}</Text>);
      break;
    }

    if (firstMatch.index > 0) {
      parts.push(<Text key={keyIdx++} style={baseStyle}>{remaining.substring(0, firstMatch.index)}</Text>);
    }
    if (matchType === 'bold') {
      parts.push(<Text key={keyIdx++} style={[baseStyle, { fontWeight: '700', color: '#2C1810' }]}>{firstMatch[1]}</Text>);
    } else {
      parts.push(<Text key={keyIdx++} style={[baseStyle, { fontStyle: 'italic', color: '#8A7860' }]}>{firstMatch[1]}</Text>);
    }
    remaining = remaining.substring(firstMatch.index + firstMatch[0].length);
  }
  return parts;
};

const renderBodyText = (text, theme) => {
  if (!text) return null;
  const blocks = text.split(/\n/);
  const elements = [];
  let i = 0;

  while (i < blocks.length) {
    const line = blocks[i].trim();
    if (!line) { i++; continue; }

    // --- Horizontal divider
    if (/^-{3,}$/.test(line)) {
      elements.push(<View key={`hr-${i}`} style={styles.mdDivider} />);
      i++; continue;
    }

    // ![alt](url) — Image
    const imgMatch = line.match(/^!\[([^\]]*)\]\(([^)]+)\)/);
    if (imgMatch) {
      const altText = imgMatch[1];
      const imgUrl = imgMatch[2];
      elements.push(
        <View key={`img-${i}`} style={styles.mdImageWrap}>
          <Image source={{ uri: imgUrl }} style={styles.mdImage} resizeMode="cover" />
        </View>
      );
      // Check if next line is a caption (*text*)
      if (i + 1 < blocks.length) {
        const nextLine = blocks[i + 1].trim();
        const captionMatch = nextLine.match(/^\*([^*]+)\*$/);
        if (captionMatch) {
          elements.push(
            <Text key={`cap-${i}`} style={styles.mdCaption}>{captionMatch[1]}</Text>
          );
          i += 2; continue;
        }
      }
      i++; continue;
    }

    // ## Header
    if (line.startsWith('### ')) {
      const headerText = line.replace(/^###\s*/, '').replace(/[🏁🔴📊⚙️🇺🇸🔮💡]/g, '').trim();
      elements.push(
        <Text key={`h3-${i}`} style={[styles.mdH3, { fontFamily: SERIF_FONT }]}>
          {headerText}
        </Text>
      );
      i++; continue;
    }
    if (line.startsWith('## ')) {
      const headerText = line.replace(/^##\s*/, '').replace(/[🏁🔴📊⚙️🇺🇸🔮💡]/g, '').trim();
      elements.push(
        <Text key={`h2-${i}`} style={[styles.bodyHeader, { color: theme.textPrimary, fontFamily: SERIF_FONT }]}>
          {headerText}
        </Text>
      );
      i++; continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <Text key={`h1-${i}`} style={[styles.bodyHeaderLarge, { color: theme.textPrimary, fontFamily: SERIF_FONT }]}>
          {line.replace(/^#\s*/, '')}
        </Text>
      );
      i++; continue;
    }

    // > Blockquote
    if (line.startsWith('> ')) {
      const quoteLines = [line.replace(/^>\s*/, '')];
      while (i + 1 < blocks.length && blocks[i + 1].trim().startsWith('> ')) {
        i++;
        quoteLines.push(blocks[i].trim().replace(/^>\s*/, ''));
      }
      const quoteText = quoteLines.join(' ');
      elements.push(
        <View key={`bq-${i}`} style={styles.mdBlockquote}>
          <Text style={styles.mdBlockquoteText}>
            {renderInlineFormatting(quoteText, styles.mdBlockquoteText)}
          </Text>
        </View>
      );
      i++; continue;
    }

    // | Table |
    if (line.startsWith('|') && line.includes('|')) {
      const tableRows = [];
      let j = i;
      while (j < blocks.length && blocks[j].trim().startsWith('|')) {
        const row = blocks[j].trim();
        // Skip separator rows like |---|---|
        if (!/^\|[\s\-|:]+\|$/.test(row)) {
          const cells = row.split('|').filter(c => c.trim() !== '');
          tableRows.push(cells.map(c => c.trim()));
        }
        j++;
      }
      if (tableRows.length > 0) {
        const isHeader = true;
        elements.push(
          <View key={`tbl-${i}`} style={styles.mdTable}>
            {tableRows.map((row, rIdx) => (
              <View key={`tr-${rIdx}`} style={[styles.mdTableRow, rIdx === 0 && styles.mdTableHeaderRow, rIdx % 2 === 0 && rIdx > 0 && styles.mdTableRowAlt]}>
                {row.map((cell, cIdx) => (
                  <View key={`td-${cIdx}`} style={[styles.mdTableCell, cIdx === 0 && styles.mdTableCellFirst]}>
                    <Text style={[styles.mdTableCellText, rIdx === 0 && styles.mdTableHeaderText]}>
                      {cell.replace(/\*\*/g, '')}
                    </Text>
                  </View>
                ))}
              </View>
            ))}
          </View>
        );
      }
      i = j; continue;
    }

    // Numbered list: 1. text
    const listMatch = line.match(/^(\d+)\.\s+(.+)/);
    if (listMatch) {
      const listItems = [{ num: listMatch[1], text: listMatch[2] }];
      while (i + 1 < blocks.length) {
        const nextMatch = blocks[i + 1].trim().match(/^(\d+)\.\s+(.+)/);
        if (!nextMatch) break;
        listItems.push({ num: nextMatch[1], text: nextMatch[2] });
        i++;
      }
      elements.push(
        <View key={`ol-${i}`} style={styles.mdList}>
          {listItems.map((item, idx) => (
            <View key={`li-${idx}`} style={styles.mdListItem}>
              <Text style={styles.mdListNum}>{item.num}.</Text>
              <Text style={styles.mdListText}>
                {renderInlineFormatting(item.text, styles.mdListText)}
              </Text>
            </View>
          ))}
        </View>
      );
      i++; continue;
    }

    // Bullet list: - text
    if (line.startsWith('- ') || line.startsWith('• ')) {
      const listItems = [line.replace(/^[-•]\s*/, '')];
      while (i + 1 < blocks.length && (blocks[i + 1].trim().startsWith('- ') || blocks[i + 1].trim().startsWith('• '))) {
        i++;
        listItems.push(blocks[i].trim().replace(/^[-•]\s*/, ''));
      }
      elements.push(
        <View key={`ul-${i}`} style={styles.mdList}>
          {listItems.map((item, idx) => (
            <View key={`li-${idx}`} style={styles.mdListItem}>
              <View style={styles.mdBullet} />
              <Text style={styles.mdListText}>
                {renderInlineFormatting(item, styles.mdListText)}
              </Text>
            </View>
          ))}
        </View>
      );
      i++; continue;
    }

    // Result line: 🥇🥈🥉 — keep as styled result
    if (/^[🥇🥈🥉]/.test(line) || /^\d+\.\s*[🥇🥈🥉]/.test(line)) {
      elements.push(
        <Text key={`result-${i}`} style={styles.mdResultLine}>{line}</Text>
      );
      i++; continue;
    }

    // Regular paragraph — collect consecutive non-special lines
    const paraLines = [line];
    while (i + 1 < blocks.length) {
      const nextLine = blocks[i + 1].trim();
      if (!nextLine || nextLine.startsWith('#') || nextLine.startsWith('>') || nextLine.startsWith('|') || nextLine.startsWith('!') || nextLine.startsWith('---') || /^\d+\.\s/.test(nextLine) || nextLine.startsWith('- ')) break;
      paraLines.push(nextLine);
      i++;
    }
    const paraText = paraLines.join(' ');
    elements.push(
      <Text key={`p-${i}`} style={[styles.bodyParagraph, { color: theme.textSecondary }]}>
        {renderInlineFormatting(paraText, { fontSize: 17, lineHeight: 28, color: '#5A4A30' })}
      </Text>
    );
    i++;
  }

  return elements;
};

const estimateReadTime = (body) => {
  if (!body) return '1 min read';
  const words = body.split(/\s+/).length;
  const minutes = Math.max(1, Math.ceil(words / 200));
  return `${minutes} min read`;
};

const formatDate = () => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const d = new Date();
  return `${months[d.getMonth()]} ${d.getDate()}`;
};

export default function ArticlesScreen({ navigation }) {
  const { user } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);

  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  const [likes, setLikes] = useState({});
  const [saves, setSaves] = useState({});

  const [selectedArticle, setSelectedArticle] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

  // Reading progress
  const [readProgress, setReadProgress] = useState(0);
  const handleDetailScroll = (e) => {
    const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
    const scrollable = contentSize.height - layoutMeasurement.height;
    if (scrollable > 0) {
      setReadProgress(Math.min(1, contentOffset.y / scrollable));
    }
  };

  // ─── Create Article Modal State ────────────────────
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createBody, setCreateBody] = useState('');
  const [createDomain, setCreateDomain] = useState('technology');
  const [createCoverImage, setCreateCoverImage] = useState(null);
  const [publishing, setPublishing] = useState(false);

  useEffect(() => { fetchArticles(); }, [selectedCategory]);

  useEffect(() => {
    if (searchQuery.trim().length > 1) {
      const timer = setTimeout(() => searchArticles(), 400);
      return () => clearTimeout(timer);
    } else if (!searchQuery.trim()) { fetchArticles(); }
  }, [searchQuery]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = { content_type: 'article', limit: 20 };
      if (selectedCategory !== 'all') params.domain = selectedCategory;
      const res = await contentAPI.list(params);
      setArticles(res.data);
    } catch (e) { console.log('Failed to fetch articles', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  const searchArticles = async () => {
    const query = searchQuery.trim().toLowerCase();
    try {
      const res = await contentAPI.search({ q: searchQuery, limit: 30 });
      setArticles((res.data || []).filter(c => c.content_type === 'article'));
    } catch (e) {
      // Fallback: fetch all articles and filter client-side
      try {
        const all = await contentAPI.list({ content_type: 'article', limit: 100 });
        const filtered = (all.data || []).filter(item =>
          (item.title || '').toLowerCase().includes(query) ||
          (item.body || '').toLowerCase().includes(query) ||
          (item.domain || '').toLowerCase().includes(query) ||
          (item.author_username || '').toLowerCase().includes(query) ||
          (item.tags || []).some(t => t.toLowerCase().includes(query))
        );
        setArticles(filtered);
      } catch { setArticles([]); }
    }
  };

  const onRefresh = () => { setRefreshing(true); fetchArticles(); };

  const toggleLike = async (id) => {
    const wasLiked = likes[id] || false;
    setLikes(prev => ({ ...prev, [id]: !wasLiked }));
    setArticles(prev => prev.map(a => a.id === id ? { ...a, likes_count: (a.likes_count || 0) + (wasLiked ? -1 : 1) } : a));
    if (selectedArticle?.id === id) setSelectedArticle(prev => prev ? { ...prev, likes_count: (prev.likes_count || 0) + (wasLiked ? -1 : 1) } : prev);
    try { await contentAPI.interact(id, { interaction_type: 'like' }); }
    catch { setLikes(prev => ({ ...prev, [id]: wasLiked })); setArticles(prev => prev.map(a => a.id === id ? { ...a, likes_count: (a.likes_count || 0) + (wasLiked ? 1 : -1) } : a)); }
  };

  const toggleSave = async (id) => {
    const wasSaved = saves[id] || false;
    setSaves(prev => ({ ...prev, [id]: !wasSaved }));
    try { await contentAPI.interact(id, { interaction_type: 'save' }); }
    catch { setSaves(prev => ({ ...prev, [id]: wasSaved })); }
  };

  const handleShare = (item) => {
    Alert.alert('Share', `Share "${item.title}"?`, [
      { text: 'Copy Link', onPress: () => Alert.alert('Copied!') },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const openArticle = async (article) => {
    setSelectedArticle(article);
    setCommentsLoading(true);
    try { const res = await contentAPI.listComments(article.id); setComments(res.data); }
    catch (e) { console.log('Failed to fetch article comments'); }
    finally { setCommentsLoading(false); }
    try {
      await contentAPI.interact(article.id, { interaction_type: 'view' });
      setArticles(prev => prev.map(a => a.id === article.id ? { ...a, views_count: (a.views_count || 0) + 1 } : a));
      setSelectedArticle(prev => prev ? { ...prev, views_count: (prev.views_count || 0) + 1 } : prev);
    } catch(e) {}
  };

  const addComment = async () => {
    if (!commentText.trim()) return;
    const txt = commentText.trim();
    setCommentText('');
    try {
      await contentAPI.addComment(selectedArticle.id, { body: txt });
      const res = await contentAPI.listComments(selectedArticle.id);
      setComments(res.data || []);
      setArticles(prev => prev.map(a => a.id === selectedArticle.id ? { ...a, comments_count: (a.comments_count || 0) + 1 } : a));
    } catch (e) { Alert.alert('Error', 'Failed to post comment.'); }
  };

  const formatCount = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num ? num.toString() : '0';
  };

  // ─── Create Article Helpers ─────────────────────────
  const pickCoverImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please grant photo library access to upload a cover image.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [16, 9],
      quality: 0.8,
    });
    if (!result.canceled && result.assets && result.assets.length > 0) {
      setCreateCoverImage(result.assets[0].uri);
    }
  };

  const resetCreateForm = () => {
    setCreateTitle('');
    setCreateBody('');
    setCreateDomain('technology');
    setCreateCoverImage(null);
    setPublishing(false);
  };

  const handlePublish = async () => {
    if (!createTitle.trim()) {
      Alert.alert('Missing title', 'Please enter a title for your article.');
      return;
    }
    if (!createBody.trim()) {
      Alert.alert('Missing content', 'Please write some content for your article.');
      return;
    }
    setPublishing(true);
    try {
      const articleData = {
        content_type: 'article',
        title: createTitle.trim(),
        body: createBody.trim(),
        domain: createDomain,
      };
      if (createCoverImage) {
        articleData.thumbnail_url = createCoverImage;
      }
      await contentAPI.create(articleData);
      setShowCreateModal(false);
      resetCreateForm();
      Alert.alert('Published!', 'Your article has been published successfully.');
      fetchArticles();
    } catch (e) {
      console.log('Failed to publish article', e);
      Alert.alert('Error', 'Failed to publish article. Please try again.');
    } finally {
      setPublishing(false);
    }
  };

  // Domain chips for article creation (exclude 'all')
  const CREATE_DOMAINS = CATEGORIES.filter(c => c.id !== 'all');

  // ─── Article Detail View (Medium-style reading experience) ────────
  if (selectedArticle) {
    const article = selectedArticle;
    const domainColor = DOMAIN_COLORS[article.domain] || '#FFD60A';
    const gradientColors = DOMAIN_GRADIENTS[article.domain] || ['#333', '#555'];
    const isLiked = likes[article.id] || false;
    const isSaved = saves[article.id] || false;
    const readTime = estimateReadTime(article.body);

    // Extract citations from body (lines starting with [number] or "Sources:" section)
    const bodyText = article.body || '';
    let mainBody = bodyText;
    let citations = [];
    const sourcesIdx = bodyText.search(/\n(Sources|References|Citations):/i);
    if (sourcesIdx !== -1) {
      mainBody = bodyText.substring(0, sourcesIdx).trim();
      const citationBlock = bodyText.substring(sourcesIdx).trim();
      citations = citationBlock.split('\n').filter(l => l.trim());
    }

    return (
      <View style={[styles.container, { backgroundColor: '#FDF6E3' }]}>
        <StatusBar barStyle="dark-content" />

        {/* Notebook ruled lines */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.10)', zIndex: 0 }} pointerEvents="none" />

        {/* Reading progress bar */}
        <View style={styles.readProgressWrap}>
          <View style={[styles.readProgressBar, { width: `${readProgress * 100}%` }]} />
          {readProgress > 0.05 && (
            <Text style={styles.readProgressText}>{Math.round(readProgress * 100)}%</Text>
          )}
        </View>

        {/* Floating back bar */}
        <View style={styles.detailFloatingHeader}>
          <TouchableOpacity onPress={() => setSelectedArticle(null)} style={styles.detailBackCircle}>
            <Ionicons name="arrow-back" size={22} color="#FFF" />
          </TouchableOpacity>
          <View style={styles.detailFloatingRight}>
            <TouchableOpacity onPress={() => handleShare(article)} style={styles.detailBackCircle}>
              <Ionicons name="share-outline" size={20} color="#FFF" />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => toggleSave(article.id)} style={styles.detailBackCircle}>
              <Ionicons name={isSaved ? 'bookmark' : 'bookmark-outline'} size={20} color={isSaved ? '#FFD60A' : '#FFF'} />
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView showsVerticalScrollIndicator={false} onScroll={handleDetailScroll} scrollEventThrottle={16}>
          {/* Full-width cover image */}
          <View style={styles.detailCoverWrap}>
            <Image source={{ uri: (article.thumbnail_url && !article.thumbnail_url.startsWith('blob:')) ? article.thumbnail_url : (article.media_url && !article.media_url.startsWith('blob:')) ? article.media_url : `https://picsum.photos/seed/artd${article.id?.slice(-4) || '0'}/800/400` }} style={styles.detailCoverImage} />
            <LinearGradient colors={['transparent', '#FDF6E3']} style={styles.detailCoverGradient} />
          </View>

          <View style={styles.detailContentWrap}>
            {/* Domain badge */}
            <View style={[styles.detailDomainPill, { backgroundColor: domainColor + '20' }]}>
              <View style={[styles.detailDomainDot, { backgroundColor: domainColor }]} />
              <Text style={[styles.detailDomainLabel, { color: domainColor }]}>{article.domain?.toUpperCase()}</Text>
            </View>

            {/* Title */}
            <Text style={[styles.detailTitle, { fontFamily: SERIF_FONT }]}>{article.title}</Text>

            {/* Author info bar */}
            <View style={styles.detailAuthorBar}>
              <TouchableOpacity style={styles.detailAuthorRow} onPress={() => navigation && navigation.navigate('Profile', { userId: article.author_id })}>
                <View style={[styles.detailAuthorAvatar, { backgroundColor: domainColor + '25' }]}>
                  <Text style={[styles.detailAuthorAvatarText, { color: domainColor }]}>{article.author_username?.[0]?.toUpperCase() || '?'}</Text>
                </View>
                <View>
                  <View style={styles.detailAuthorNameRow}>
                    <Text style={styles.detailAuthorName}>{article.author_username}</Text>
                    <Ionicons name="checkmark-circle" size={14} color="#FFD60A" />
                  </View>
                  <Text style={styles.detailAuthorMeta}>{formatDate()} · {readTime} · {formatCount(article.views_count)} views</Text>
                </View>
              </TouchableOpacity>
            </View>

            {/* Divider */}
            <View style={styles.detailDivider} />

            {/* Body text (markdown-ish) */}
            <View style={styles.detailBodyWrap}>
              {renderBodyText(mainBody, { textPrimary: '#2C1810', textSecondary: '#5A4A30' })}
            </View>

            {/* Citations */}
            {citations.length > 0 && (
              <View style={styles.citationsWrap}>
                <View style={styles.citationsDivider} />
                <Text style={styles.citationsTitle}>Sources & References</Text>
                {citations.map((cite, idx) => (
                  <Text key={idx} style={styles.citationItem}>{cite}</Text>
                ))}
              </View>
            )}

            {/* IQ card */}
            <View style={styles.detailIqCard}>
              <Ionicons name="star" size={16} color="#FFD60A" />
              <Text style={styles.detailIqText}>+10 IQ Points earned for reading this article</Text>
            </View>

            {/* Action bar */}
            <View style={styles.detailActionsBar}>
              <TouchableOpacity style={styles.detailActionItem} onPress={() => toggleLike(article.id)}>
                <Ionicons name={isLiked ? 'heart' : 'heart-outline'} size={24} color={isLiked ? '#ED4956' : '#888'} />
                <Text style={[styles.detailActionLabel, isLiked && { color: '#ED4956' }]}>{formatCount(article.likes_count || 0)}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.detailActionItem}>
                <Ionicons name="chatbubble-outline" size={22} color="#888" />
                <Text style={styles.detailActionLabel}>{comments.length}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.detailActionItem} onPress={() => handleShare(article)}>
                <Ionicons name="paper-plane-outline" size={22} color="#888" />
                <Text style={styles.detailActionLabel}>Share</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.detailActionItem} onPress={() => toggleSave(article.id)}>
                <Ionicons name={isSaved ? 'bookmark' : 'bookmark-outline'} size={22} color={isSaved ? '#D35400' : '#888'} />
                <Text style={[styles.detailActionLabel, isSaved && { color: '#D35400' }]}>Save</Text>
              </TouchableOpacity>
            </View>

            {/* Comments section */}
            <View style={styles.detailDivider} />
            <Text style={styles.commentsHeading}>Responses ({comments.length})</Text>
            <View style={styles.commentInputRow}>
              <TextInput
                style={styles.commentInput}
                placeholder="Write a response..."
                placeholderTextColor="#666"
                value={commentText}
                onChangeText={setCommentText}
              />
              <TouchableOpacity onPress={addComment} style={[styles.commentSendBtn, { backgroundColor: commentText.trim() ? '#FFD60A' : '#222' }]}>
                <Ionicons name="arrow-up" size={18} color={commentText.trim() ? '#FFFFFF' : '#666'} />
              </TouchableOpacity>
            </View>

            {commentsLoading && <ActivityIndicator color="#FFD60A" style={{ marginVertical: 16 }} />}
            {comments.map(comment => (
              <View key={comment.id} style={styles.commentCard}>
                <View style={styles.commentAvatarWrap}>
                  <Text style={styles.commentAvatarLetter}>{comment.username?.[0]?.toUpperCase() || '?'}</Text>
                </View>
                <View style={styles.commentBody}>
                  <View style={styles.commentTopRow}>
                    <Text style={styles.commentAuthor}>{comment.username}</Text>
                    <Text style={styles.commentTime}>{comment.time || 'recently'}</Text>
                  </View>
                  <Text style={styles.commentText}>{comment.body}</Text>
                </View>
              </View>
            ))}
          </View>
          <View style={{ height: 100 }} />
        </ScrollView>
      </View>
    );
  }

  // ─── Article List View (Medium-style cards) ────────────────
  const renderArticle = ({ item, index }) => {
    const domainColor = DOMAIN_COLORS[item.domain] || '#FFD60A';
    const gradientColors = DOMAIN_GRADIENTS[item.domain] || ['#333', '#555'];
    const isLiked = likes[item.id] || false;
    const isSaved = saves[item.id] || false;
    const readTime = estimateReadTime(item.body);

    const tapeColors = ['blue', 'yellow', 'purple', 'green', 'red'];
    return (
      <TouchableOpacity
        style={[styles.card, { transform: [{ rotate: `${index % 2 === 0 ? -0.3 : 0.3}deg` }] }]}
        onPress={() => openArticle(item)}
        activeOpacity={0.85}
      >
        <Tape color={tapeColors[index % tapeColors.length]} style={{ left: 15 + (index % 3) * 20 }} width={48 + (index % 3) * 8} />
        {/* Cover image */}
        <View style={styles.cardImageWrap}>
          <Image source={{ uri: (item.thumbnail_url && !item.thumbnail_url.startsWith('blob:')) ? item.thumbnail_url : (item.media_url && !item.media_url.startsWith('blob:')) ? item.media_url : `https://picsum.photos/seed/art${item.id?.slice(-4) || index}/600/300` }} style={styles.cardImage} />
          {/* Domain stamp badge */}
          <Stamp domain={item.domain} color={domainColor} style={{ position: 'absolute', bottom: 8, left: 8 }} />
        </View>

        {/* Card body */}
        <View style={styles.cardContent}>
          {/* Title */}
          <Text style={[styles.cardTitle, { fontFamily: SERIF_FONT }]} numberOfLines={2}>{item.title}</Text>

          {/* Excerpt */}
          <Text style={styles.cardExcerpt} numberOfLines={2}>{item.body}</Text>

          {/* Author row */}
          <View style={styles.cardAuthorRow}>
            <View style={[styles.cardAuthorAvatar, { backgroundColor: domainColor + '25' }]}>
              <Text style={[styles.cardAuthorAvatarText, { color: domainColor }]}>{item.author_username?.[0]?.toUpperCase() || '?'}</Text>
            </View>
            <View style={styles.cardAuthorInfo}>
              <Text style={styles.cardAuthorName}>{item.author_username}</Text>
              <Text style={styles.cardAuthorMeta}>{formatDate()} · {readTime}</Text>
            </View>
            <TouchableOpacity onPress={() => toggleSave(item.id)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name={isSaved ? 'bookmark' : 'bookmark-outline'} size={20} color={isSaved ? '#FFD60A' : '#666'} />
            </TouchableOpacity>
          </View>

          {/* Bottom stats row */}
          <View style={styles.cardStatsRow}>
            <TouchableOpacity style={styles.cardStatItem} onPress={() => toggleLike(item.id)}>
              <Ionicons name={isLiked ? 'heart' : 'heart-outline'} size={18} color={isLiked ? '#ED4956' : '#666'} />
              <Text style={[styles.cardStatText, isLiked && { color: '#ED4956' }]}>{formatCount(item.likes_count || 0)}</Text>
            </TouchableOpacity>
            <View style={styles.cardStatItem}>
              <Ionicons name="chatbubble-outline" size={16} color="#666" />
              <Text style={styles.cardStatText}>{formatCount(item.comments_count)}</Text>
            </View>
            <View style={styles.cardStatItem}>
              <Ionicons name="eye-outline" size={16} color="#666" />
              <Text style={styles.cardStatText}>{formatCount(item.views_count)}</Text>
            </View>
            <TouchableOpacity style={styles.cardStatItem} onPress={() => handleShare(item)}>
              <Ionicons name="share-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
          <PaperCorner />
        </View>
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <View>
      <View style={styles.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View style={{ flexDirection: 'row', gap: 4 }}>
            <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 6, height: 6, borderRadius: 3, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
          </View>
          <Text style={[styles.headerTitle, { fontFamily: SERIF_FONT }]}>Articles</Text>
        </View>
        <TouchableOpacity onPress={() => setShowSearch(!showSearch)} style={{ padding: 6, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3, backgroundColor: '#FFFCF2' }}>
          <Ionicons name={showSearch ? "close" : "search-outline"} size={18} color="#2C1810" />
        </TouchableOpacity>
      </View>

      {showSearch && (
        <View style={styles.searchWrapper}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={16} color="#666" />
            <TextInput style={styles.searchInput}
              placeholder="Search articles..." placeholderTextColor="#666"
              value={searchQuery} onChangeText={setSearchQuery} autoFocus returnKeyType="search" />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={16} color="#666" />
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoriesContainer} contentContainerStyle={styles.categoriesContent}>
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat.id;
          return (
            <TouchableOpacity key={cat.id}
              style={[styles.categoryChip, isActive && styles.categoryChipActive]}
              onPress={() => setSelectedCategory(cat.id)}>
              <Ionicons name={cat.icon} size={14} color={isActive ? '#FFFFFF' : '#999'} />
              <Text style={[styles.categoryText, isActive && styles.categoryTextActive]}>{cat.label}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: '#FFFCF2' }]}>
      <StatusBar barStyle="dark-content" />
      {/* Notebook margin */}
      <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)', zIndex: 0 }} pointerEvents="none" />
      <FlatList data={articles} keyExtractor={(item) => item.id} renderItem={renderArticle}
        ListHeaderComponent={renderHeader} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFD60A" />}
        ListEmptyComponent={!loading ? (
          <View style={{ height: 300, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40 }}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '2deg' }], marginBottom: 16 }}>
              <Ionicons name="book-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>No articles yet</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20 }}>This shelf is bare! Write the first article and fill these pages with knowledge.</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        ) : (
          <View style={{ paddingHorizontal: 16, marginTop: 20 }}>
            <SkeletonCard style={{ height: 160, marginBottom: 12 }} />
            <SkeletonCard style={{ height: 160, marginBottom: 12 }} />
            <SkeletonCard style={{ height: 160, marginBottom: 12 }} />
          </View>
        )}
      />

      {/* ─── Floating Action Button (Create Article) ─── */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowCreateModal(true)}
        activeOpacity={0.8}
      >
        <Ionicons name="add" size={30} color="#2C1810" />
      </TouchableOpacity>

      {/* ─── Create Article Modal ─── */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => { setShowCreateModal(false); resetCreateForm(); }}
      >
        <KeyboardAvoidingView
          style={styles.createModalContainer}
          behavior="padding"
          keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}
        >
          {/* Modal Header */}
          <View style={styles.createModalHeader}>
            <TouchableOpacity onPress={() => { setShowCreateModal(false); resetCreateForm(); }}>
              <Ionicons name="close" size={26} color="#999" />
            </TouchableOpacity>
            <Text style={[styles.createModalHeaderTitle, { fontFamily: SERIF_FONT }]}>New Article</Text>
            <TouchableOpacity
              style={[
                styles.publishBtn,
                (!createTitle.trim() || !createBody.trim() || publishing) && styles.publishBtnDisabled,
              ]}
              onPress={handlePublish}
              disabled={!createTitle.trim() || !createBody.trim() || publishing}
            >
              {publishing ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={[
                  styles.publishBtnText,
                  (!createTitle.trim() || !createBody.trim()) && styles.publishBtnTextDisabled,
                ]}>Publish</Text>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.createModalBody}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* Cover Image */}
            <TouchableOpacity style={styles.coverImagePicker} onPress={pickCoverImage} activeOpacity={0.7}>
              {createCoverImage ? (
                <View style={styles.coverImagePreviewWrap}>
                  <Image source={{ uri: createCoverImage }} style={styles.coverImagePreview} />
                  <View style={styles.coverImageOverlay}>
                    <Ionicons name="camera" size={22} color="#FFF" />
                    <Text style={styles.coverImageOverlayText}>Change cover</Text>
                  </View>
                </View>
              ) : (
                <View style={styles.coverImagePlaceholder}>
                  <Ionicons name="image-outline" size={36} color="#555" />
                  <Text style={styles.coverImagePlaceholderText}>Add cover image</Text>
                </View>
              )}
            </TouchableOpacity>

            {/* Title Input */}
            <TextInput
              style={[styles.createTitleInput, { fontFamily: SERIF_FONT }]}
              placeholder="Title"
              placeholderTextColor="#555"
              value={createTitle}
              onChangeText={setCreateTitle}
              multiline
              maxLength={200}
              textAlignVertical="top"
            />

            {/* Domain/Category Selector */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.createDomainScroll}
              contentContainerStyle={styles.createDomainContent}
            >
              {CREATE_DOMAINS.map((cat) => {
                const isActive = createDomain === cat.id;
                const domainColor = DOMAIN_COLORS[cat.id] || '#FFD60A';
                return (
                  <TouchableOpacity
                    key={cat.id}
                    style={[
                      styles.createDomainChip,
                      isActive && { backgroundColor: domainColor + '25', borderColor: domainColor },
                    ]}
                    onPress={() => setCreateDomain(cat.id)}
                  >
                    <Ionicons name={cat.icon} size={14} color={isActive ? domainColor : '#777'} />
                    <Text style={[
                      styles.createDomainChipText,
                      isActive && { color: domainColor },
                    ]}>{cat.label}</Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {/* Body Textarea */}
            <TextInput
              style={styles.createBodyInput}
              placeholder="Tell your story..."
              placeholderTextColor="#444"
              value={createBody}
              onChangeText={setCreateBody}
              multiline
              textAlignVertical="top"
              scrollEnabled={false}
            />

            <View style={{ height: 120 }} />
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Header
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 54, paddingBottom: 12 },
  headerTitle: { fontSize: 28, fontWeight: '800', color: '#2C1810', letterSpacing: 0.3 },

  // Search — sketch style
  searchWrapper: { paddingHorizontal: 16, paddingBottom: 10 },
  searchBar: { flexDirection: 'row', alignItems: 'center', height: 42, paddingHorizontal: 14, gap: 8, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 10, borderBottomLeftRadius: 10, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 3 } }) },
  searchInput: { flex: 1, fontSize: 14, color: '#2C1810' },

  // Categories — sketch chips
  categoriesContainer: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#C8BFA8' },
  categoriesContent: { paddingHorizontal: 16, gap: 8 },
  categoryChip: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 14, paddingVertical: 8, borderWidth: 1.5, borderColor: '#2C1810', backgroundColor: '#FFFCF2', borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2, ...Platform.select({ ios: { shadowColor: '#B8AE90', shadowOffset: { width: 1.5, height: 2 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 2 } }) },
  categoryChipActive: { backgroundColor: '#FFD60A', borderColor: '#2C1810', borderWidth: 2 },
  categoryText: { fontSize: 13, fontWeight: '500', color: '#8A7860' },
  categoryTextActive: { color: '#2C1810', fontWeight: '600' },

  // ─── Card (Sketch-style with tape + stamp) ─────────────────────────
  card: { backgroundColor: '#FFFCF2', marginHorizontal: 16, marginTop: 16, overflow: 'hidden', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  cardImageWrap: { width: '100%', height: 200, position: 'relative' },
  cardImage: { width: '100%', height: '100%', justifyContent: 'center', alignItems: 'center' },
  cardDomainOverlay: { position: 'absolute', top: 12, left: 12, paddingHorizontal: 9, paddingVertical: 3, borderWidth: 2, borderRadius: 3, transform: [{ rotate: '-1.5deg' }] },
  cardDomainOverlayText: { fontSize: 10, fontWeight: '800', letterSpacing: 1.2, textTransform: 'uppercase' },
  cardContent: { padding: 16 },
  cardTitle: { fontSize: 20, fontWeight: '800', color: '#2C1810', lineHeight: 28, marginBottom: 8, letterSpacing: 0.2 },
  cardExcerpt: { fontSize: 14, lineHeight: 21, color: '#8A7860', marginBottom: 14 },
  cardAuthorRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 14 },
  cardAuthorAvatar: { width: 34, height: 34, borderRadius: 17, justifyContent: 'center', alignItems: 'center' },
  cardAuthorAvatarText: { fontSize: 14, fontWeight: '700' },
  cardAuthorInfo: { flex: 1, marginLeft: 10 },
  cardAuthorName: { fontSize: 13, fontWeight: '600', color: '#5A4A30' },
  cardAuthorMeta: { fontSize: 11, color: '#8A7860', marginTop: 2 },
  cardStatsRow: { flexDirection: 'row', alignItems: 'center', gap: 18, paddingTop: 12, borderTopWidth: 0.5, borderTopColor: '#C8BFA8' },
  cardStatItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  cardStatText: { fontSize: 12, color: '#8A7860', fontWeight: '500' },

  // ─── Detail View (Medium reading experience) ─────
  // Reading progress bar
  readProgressWrap: {
    position: 'absolute', top: 0, left: 0, right: 0, height: 4, zIndex: 20,
    backgroundColor: '#E8E0D0',
  },
  readProgressBar: {
    height: 4, backgroundColor: '#FFD60A',
    borderTopRightRadius: 2, borderBottomRightRadius: 2,
  },
  readProgressText: {
    position: 'absolute', right: 8, top: 6,
    fontSize: 9, fontWeight: '700', color: '#8A7860',
    backgroundColor: '#FFFCF2', paddingHorizontal: 4, paddingVertical: 1,
    borderWidth: 1, borderColor: '#C8BFA8', borderRadius: 2,
  },

  detailFloatingHeader: { position: 'absolute', top: 48, left: 16, right: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', zIndex: 10 },
  detailFloatingRight: { flexDirection: 'row', gap: 10 },
  detailBackCircle: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.55)', justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  detailCoverWrap: { width: '100%', height: 300, position: 'relative' },
  detailCoverImage: { width: '100%', height: '100%', justifyContent: 'center', alignItems: 'center' },
  detailCoverGradient: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 120 },
  detailContentWrap: { paddingHorizontal: 20, paddingTop: 4 },
  detailDomainPill: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', paddingHorizontal: 9, paddingVertical: 3, marginBottom: 14, gap: 6, borderWidth: 2, borderRadius: 3, transform: [{ rotate: '-1.5deg' }] },
  detailDomainDot: { width: 6, height: 6, borderRadius: 3 },
  detailDomainLabel: { fontSize: 11, fontWeight: '700', letterSpacing: 0.8 },
  detailTitle: { fontSize: 28, fontWeight: '900', color: '#2C1810', lineHeight: 38, marginBottom: 20, letterSpacing: -0.5 },
  detailAuthorBar: { marginBottom: 20 },
  detailAuthorRow: { flexDirection: 'row', alignItems: 'center' },
  detailAuthorAvatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  detailAuthorAvatarText: { fontSize: 18, fontWeight: '700' },
  detailAuthorNameRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginLeft: 12 },
  detailAuthorName: { fontSize: 15, fontWeight: '600', color: '#5A4A30' },
  detailAuthorMeta: { fontSize: 12, color: '#8A7860', marginTop: 2, marginLeft: 12 },
  detailDivider: { height: 1, backgroundColor: '#C8BFA8', marginVertical: 20 },

  // Body text
  detailBodyWrap: { marginBottom: 12 },
  bodyHeaderLarge: { fontSize: 24, fontWeight: '800', color: '#2C1810', lineHeight: 34, marginBottom: 12, marginTop: 24, letterSpacing: 0.3 },
  bodyHeader: { fontSize: 22, fontWeight: '800', color: '#2C1810', lineHeight: 30, marginBottom: 10, marginTop: 24, letterSpacing: 0.3 },
  mdH3: { fontSize: 18, fontWeight: '700', color: '#5A4A30', lineHeight: 26, marginBottom: 8, marginTop: 18 },
  bodyParagraph: { fontSize: 17, lineHeight: 28, color: '#5A4A30', marginBottom: 16, fontFamily: Platform.OS === 'ios' ? 'Georgia' : undefined },

  // Markdown images — sketch bordered
  mdImageWrap: { overflow: 'hidden', marginVertical: 14, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 5 } }) },
  mdImage: { width: '100%', height: 220 },
  mdCaption: { fontSize: 13, color: '#8A7860', fontStyle: 'italic', textAlign: 'center', marginTop: 6, marginBottom: 14, paddingHorizontal: 8 },

  // Markdown divider
  mdDivider: { height: 1, backgroundColor: '#C8BFA8', marginVertical: 24 },

  // Markdown blockquote
  mdBlockquote: { borderLeftWidth: 3, borderLeftColor: '#FFD60A', backgroundColor: '#FFD60A10', paddingLeft: 16, paddingVertical: 14, paddingRight: 14, borderRadius: 4, marginVertical: 14 },
  mdBlockquoteText: { fontSize: 15, lineHeight: 24, color: '#5A4A30', fontStyle: 'italic' },

  // Markdown table — sketch bordered
  mdTable: { overflow: 'hidden', marginVertical: 14, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  mdTableRow: { flexDirection: 'row', borderBottomWidth: 0.5, borderBottomColor: '#C8BFA8' },
  mdTableHeaderRow: { backgroundColor: '#C8BFA8' },
  mdTableRowAlt: { backgroundColor: '#FFFCF2' },
  mdTableCell: { flex: 1, paddingVertical: 10, paddingHorizontal: 12 },
  mdTableCellFirst: { flex: 0.4 },
  mdTableCellText: { fontSize: 13, color: '#5A4A30', lineHeight: 18 },
  mdTableHeaderText: { fontWeight: '700', color: '#2C1810', fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 },

  // Markdown lists
  mdList: { marginVertical: 8, paddingLeft: 4 },
  mdListItem: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 },
  mdListNum: { fontSize: 15, color: '#D35400', fontWeight: '700', width: 24, marginRight: 6 },
  mdListText: { fontSize: 16, lineHeight: 24, color: '#5A4A30', flex: 1 },
  mdBullet: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#FFD60A', marginTop: 9, marginRight: 10 },

  // Result lines (race results)
  mdResultLine: { fontSize: 16, lineHeight: 26, color: '#5A4A30', fontWeight: '500', marginBottom: 4, paddingLeft: 4 },

  // Citations
  citationsWrap: { marginBottom: 20 },
  citationsDivider: { height: 3, width: 40, backgroundColor: '#FFD60A', marginBottom: 16, borderRadius: 2 },
  citationsTitle: { fontSize: 16, fontWeight: '700', color: '#2C1810', marginBottom: 12 },
  citationItem: { fontSize: 13, lineHeight: 20, color: '#8A7860', marginBottom: 6 },

  // IQ Card
  detailIqCard: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 16, backgroundColor: '#FFD60A10', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, marginBottom: 20 },
  detailIqText: { fontSize: 13, fontWeight: '600', color: '#D35400' },

  // Actions bar
  detailActionsBar: { flexDirection: 'row', justifyContent: 'space-around', paddingVertical: 14, backgroundColor: '#FDF6E3', marginBottom: 24, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },
  detailActionItem: { alignItems: 'center', gap: 4 },
  detailActionLabel: { fontSize: 11, color: '#8A7860', fontWeight: '500' },

  // Comments
  commentsHeading: { fontSize: 18, fontWeight: '700', color: '#2C1810', marginBottom: 14 },
  commentInputRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 20 },
  commentInput: { flex: 1, height: 44, borderRadius: 22, paddingHorizontal: 16, fontSize: 14, backgroundColor: '#F8F6F0', color: '#2C1810', borderWidth: 1, borderColor: '#C8BFA8' },
  commentSendBtn: { width: 38, height: 38, borderRadius: 19, justifyContent: 'center', alignItems: 'center' },
  commentCard: { flexDirection: 'row', paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: '#C8BFA8', gap: 10 },
  commentAvatarWrap: { width: 34, height: 34, borderRadius: 17, backgroundColor: '#FFD60A20', justifyContent: 'center', alignItems: 'center' },
  commentAvatarLetter: { fontSize: 14, fontWeight: '700', color: '#D35400' },
  commentBody: { flex: 1 },
  commentTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  commentAuthor: { fontSize: 13, fontWeight: '600', color: '#5A4A30' },
  commentTime: { fontSize: 11, color: '#8A7860' },
  commentText: { fontSize: 14, lineHeight: 20, color: '#8A7860' },

  // Empty
  emptyContainer: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyText: { fontSize: 14, color: '#8A7860' },

  // ─── Floating Action Button — sketch style ─────────────────────────
  fab: {
    position: 'absolute',
    bottom: 30,
    right: 20,
    width: 58,
    height: 58,
    backgroundColor: '#FFD60A',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 20,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 14,
    borderBottomLeftRadius: 14,
    borderBottomRightRadius: 3,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },

  // ─── Create Article Modal ──────────────────────────
  createModalContainer: {
    flex: 1,
    backgroundColor: '#FFFCF2',
  },
  createModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: Platform.OS === 'ios' ? 56 : 16,
    paddingBottom: 12,
    paddingHorizontal: 20,
    borderBottomWidth: 0.5,
    borderBottomColor: '#C8BFA8',
  },
  createModalHeaderTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2C1810',
  },
  publishBtn: {
    backgroundColor: '#FFD60A',
    paddingHorizontal: 20,
    paddingVertical: 9,
    minWidth: 80,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 2,
    borderTopRightRadius: 8,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 2,
  },
  publishBtnDisabled: {
    backgroundColor: '#C8BFA8',
  },
  publishBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#2C1810',
  },
  publishBtnTextDisabled: {
    color: '#8A7860',
  },
  createModalBody: {
    flex: 1,
    paddingHorizontal: 20,
  },

  // Cover image picker
  coverImagePicker: {
    marginTop: 20,
    borderRadius: 14,
    overflow: 'hidden',
  },
  coverImagePlaceholder: {
    height: 180,
    backgroundColor: '#F8F6F0',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#C8BFA8',
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  coverImagePlaceholderText: {
    fontSize: 14,
    color: '#8A7860',
    fontWeight: '500',
  },
  coverImagePreviewWrap: {
    height: 200,
    borderRadius: 14,
    overflow: 'hidden',
    position: 'relative',
  },
  coverImagePreview: {
    width: '100%',
    height: '100%',
  },
  coverImageOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  coverImageOverlayText: {
    fontSize: 13,
    color: '#FFF',
    fontWeight: '500',
  },

  // Title input
  createTitleInput: {
    fontSize: 28,
    fontWeight: '700',
    color: '#2C1810',
    marginTop: 24,
    paddingVertical: 0,
    lineHeight: 38,
  },

  // Domain selector
  createDomainScroll: {
    marginTop: 20,
    marginBottom: 4,
  },
  createDomainContent: {
    gap: 8,
    paddingRight: 20,
  },
  createDomainChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    backgroundColor: '#FFFCF2',
    borderTopLeftRadius: 2,
    borderTopRightRadius: 8,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 2,
  },
  createDomainChipText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8A7860',
  },

  // Body input
  createBodyInput: {
    fontSize: 17,
    lineHeight: 28,
    color: '#5A4A30',
    marginTop: 20,
    paddingVertical: 0,
    minHeight: 300,
  },
});
