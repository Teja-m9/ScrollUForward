import React, { useState, useContext, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, Image, TouchableOpacity,
  StatusBar, Dimensions, ScrollView, Modal, TextInput,
  Alert, Switch, FlatList, Platform, Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { usersAPI, contentAPI, discussionsAPI } from '../api';
import { AuthContext, ThemeContext } from '../../App';

const { width } = Dimensions.get('window');
const POST_SIZE = (width - 6) / 3;
const ACCENT = '#2563EB'; // Rich blue — visible on cream notebook background
const CARD_PHOTO_HEIGHT = 220;

export default function ProfileScreen({ route, navigation }) {
  const { user, onLogout, openDM } = useContext(AuthContext);
  const { theme, isDarkTheme, toggleTheme } = useContext(ThemeContext);

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('posts');
  const [profileImage, setProfileImage] = useState(null);
  const [showEdit, setShowEdit] = useState(false);
  const [editBio, setEditBio] = useState('');
  const [editName, setEditName] = useState('');
  const [editUsername, setEditUsername] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editWebsite, setEditWebsite] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [notifEnabled, setNotifEnabled] = useState(true);
  const [privateAccount, setPrivateAccount] = useState(false);
  const [posts, setPosts] = useState([]);
  const [savedPosts, setSavedPosts] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [showFollowList, setShowFollowList] = useState(null);
  const [followList, setFollowList] = useState([]);
  const [followListLoading, setFollowListLoading] = useState(false);
  const [discussionHistory, setDiscussionHistory] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [showPhotoModal, setShowPhotoModal] = useState(false); // fullscreen photo

  const isOwnProfile = !route?.params?.userId || route.params.userId === user?.user_id;
  const targetUserId = route?.params?.userId || user?.user_id;

  useEffect(() => { loadProfile(); }, [targetUserId]);
  useEffect(() => {
    if (activeTab === 'posts') fetchPosts();
    if (activeTab === 'saved') fetchSaved();
    if (activeTab === 'chats') fetchDiscussionHistory();
  }, [activeTab, targetUserId]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      if (targetUserId) {
        const res = await usersAPI.getProfile(targetUserId);
        setProfile(res.data);
        // Restore saved profile image for own profile
        if (isOwnProfile) {
          const savedImg = await AsyncStorage.getItem('profile_image');
          if (savedImg) setProfileImage(savedImg);
        }
        // Check if current user follows target (for other profiles)
        if (!isOwnProfile && user?.user_id) {
          try {
            const followersRes = await usersAPI.followers(targetUserId, 200);
            const followerIds = (followersRes.data?.follower_ids || []);
            setIsFollowing(followerIds.includes(user.user_id));
          } catch { setIsFollowing(false); }
        }
      } else {
        setProfile({
          username: user?.username || '',
          display_name: user?.display_name || user?.username || '',
          bio: '',
          followers_count: 0,
          following_count: 0,
          posts_count: 0,
          iq_score: 0,
          interest_tags: [],
        });
      }
    } catch {
      setProfile({
        username: user?.username || '',
        display_name: user?.display_name || user?.username || '',
        bio: '',
        followers_count: 0,
        following_count: 0,
        posts_count: 0,
        iq_score: 0,
        interest_tags: [],
      });
    } finally { setLoading(false); }
  };

  const fetchPosts = async () => {
    try {
      const res = await contentAPI.list({ limit: 50 });
      const userPosts = (res.data || []).filter(p => p.author_id === targetUserId);
      setPosts(userPosts);
    } catch { setPosts([]); }
  };

  const fetchSaved = async () => {
    try {
      const res = await contentAPI.saved({ limit: 50 });
      setSavedPosts(res.data || []);
    } catch {
      // Fallback to AsyncStorage if backend fails
      try {
        const savedIdsJson = await AsyncStorage.getItem('saved_content_ids');
        const savedIds = savedIdsJson ? JSON.parse(savedIdsJson) : [];
        if (savedIds.length > 0) {
          const res = await contentAPI.list({ limit: 100 });
          setSavedPosts((res.data || []).filter(p => savedIds.includes(p.id)));
        } else { setSavedPosts([]); }
      } catch { setSavedPosts([]); }
    }
  };

  const fetchDiscussionHistory = async () => {
    if (!targetUserId) return;
    try {
      const res = await discussionsAPI.getUserHistory(targetUserId);
      setDiscussionHistory(res.data?.items || res.data || []);
    } catch { setDiscussionHistory([]); }
  };

  const pickProfileImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') { Alert.alert('Permission needed'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (!result.canceled) {
      const uri = result.assets[0].uri;
      setProfileImage(uri);
      await AsyncStorage.setItem('profile_image', uri);
    }
  };

  const handleSaveProfile = async () => {
    setProfile(p => ({
      ...p,
      bio: editBio,
      display_name: editName,
      username: editUsername || p?.username,
      location: editLocation,
      website: editWebsite,
    }));
    setShowEdit(false);
    try {
      await usersAPI.updateProfile({
        display_name: editName,
        bio: editBio,
        username: editUsername,
        location: editLocation,
        website: editWebsite,
      });
    } catch (e) { console.log('Failed to save profile', e); }
  };

  const openEditModal = () => {
    setEditBio(profile?.bio || '');
    setEditName(profile?.display_name || '');
    setEditUsername(profile?.username || '');
    setEditLocation(profile?.location || '');
    setEditWebsite(profile?.website || '');
    setShowEdit(true);
  };

  const handleFollow = async () => {
    if (followLoading) return;
    setFollowLoading(true);
    const wasFollowing = isFollowing;
    // Optimistic update
    setIsFollowing(!wasFollowing);
    setProfile(p => p ? {
      ...p,
      followers_count: (p.followers_count || 0) + (wasFollowing ? -1 : 1),
    } : p);
    try {
      if (wasFollowing) {
        await usersAPI.unfollow(targetUserId);
      } else {
        await usersAPI.follow(targetUserId);
      }
    } catch {
      // Revert on failure
      setIsFollowing(wasFollowing);
      setProfile(p => p ? {
        ...p,
        followers_count: (p.followers_count || 0) + (wasFollowing ? 1 : -1),
      } : p);
    } finally { setFollowLoading(false); }
  };

  const openFollowList = async (type) => {
    setShowFollowList(type);
    setFollowListLoading(true);
    try {
      const res = type === 'followers'
        ? await usersAPI.followers(targetUserId, 50)
        : await usersAPI.following(targetUserId, 50);
      // IDs come back, need to fetch profiles — use leaderboard as fallback
      const ids = res.data?.follower_ids || res.data?.following_ids || [];
      if (ids.length > 0) {
        // Fetch each profile — batch by using leaderboard data
        const lb = await usersAPI.leaderboard(100);
        const allUsers = lb.data || [];
        setFollowList(allUsers.filter(u => ids.includes(u.user_id)));
      } else {
        setFollowList([]);
      }
    } catch {
      // fallback: leaderboard
      try {
        const res = await usersAPI.leaderboard(50);
        const users = res.data || [];
        const count = type === 'followers' ? (profile?.followers_count || 0) : (profile?.following_count || 0);
        setFollowList(users.slice(0, count));
      } catch { setFollowList([]); }
    } finally { setFollowListLoading(false); }
  };

  const handleShare = () => Alert.alert('Share', `scrolluforward.app/${profile?.username}`);
  const handleLogout = () => {
    Alert.alert('Log Out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log Out', style: 'destructive', onPress: () => { setShowSettings(false); onLogout(); } },
    ]);
  };

  const fmtCount = (n) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
    return (n || 0).toString();
  };

  const getPostImage = (item, i) => {
    if (item.media_url && !item.media_url.startsWith('blob:')) return item.media_url;
    if (item.thumbnail_url && !item.thumbnail_url.startsWith('blob:')) return item.thumbnail_url;
    return `https://picsum.photos/seed/post${i}/300/300`;
  };

  const renderSettingsItem = ({ icon, label, value, onPress, isToggle, toggleValue, onToggle, color, showChevron = true }) => (
    <TouchableOpacity style={s.settingsItem} onPress={onPress} disabled={isToggle} activeOpacity={isToggle ? 1 : 0.6}>
      <View style={[s.settingsIconCircle, { backgroundColor: (color || ACCENT) + '15' }]}>
        <Ionicons name={icon} size={20} color={color || ACCENT} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.settingsLabel, { color: color || '#2C1810' }]}>{label}</Text>
        {value && <Text style={s.settingsValue}>{value}</Text>}
      </View>
      {isToggle ? (
        <Switch value={toggleValue} onValueChange={onToggle}
          trackColor={{ false: '#333', true: ACCENT + '40' }}
          thumbColor={toggleValue ? ACCENT : '#666'} />
      ) : showChevron ? <Ionicons name="chevron-forward" size={18} color="#555" /> : null}
    </TouchableOpacity>
  );

  if (loading) return <View style={s.container} />;

  const hasPhoto = !!profileImage;
  const displayName = profile?.display_name || profile?.username || 'User';
  const username = profile?.username || '';

  return (
    <View style={s.container}>
        {/* Notebook margin */}
        <View style={{ position: 'absolute', left: 14, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.08)', zIndex: 0 }} pointerEvents="none" />
      <StatusBar barStyle="dark-content" backgroundColor="#FBF8F0" />

      {/* Header bar — notebook style */}
      <View style={s.header}>
        {!isOwnProfile ? (
          <TouchableOpacity onPress={() => navigation?.goBack()} style={s.headerBtn}>
            <Ionicons name="arrow-back" size={22} color="#2C1810" />
          </TouchableOpacity>
        ) : (
          <View style={{ flexDirection: 'row', gap: 4, width: 38, justifyContent: 'center' }}>
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
          </View>
        )}
        <Text style={s.headerTitle} numberOfLines={1}>{username ? `@${username}` : 'Profile'}</Text>
        {isOwnProfile ? (
          <View style={{ flexDirection: 'row', gap: 6 }}>
            <TouchableOpacity style={s.headerBtn} onPress={() => setShowSettings(true)}>
              <Ionicons name="settings-outline" size={22} color="#2C1810" />
            </TouchableOpacity>
          </View>
        ) : <View style={{ width: 38 }} />}
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 80 }}>

        {/* ── Profile Card (matches profile.webp design) ── */}
        <View style={s.profileCard}>

          {/* Cover / Avatar area */}
          <View style={s.coverArea}>
            {hasPhoto ? (
              <TouchableOpacity activeOpacity={0.9} onPress={() => setShowPhotoModal(true)}>
                <Image source={{ uri: profileImage }} style={s.coverPhoto} />
                <View style={s.coverOverlay} />
              </TouchableOpacity>
            ) : (
              <View style={s.coverPlaceholder}>
                <Ionicons name="person" size={80} color="#333" />
              </View>
            )}

            {/* Camera button for own profile */}
            {isOwnProfile && (
              <TouchableOpacity style={s.cameraFab} onPress={pickProfileImage}>
                <Ionicons name="camera" size={16} color="#FFFFFF" />
              </TouchableOpacity>
            )}
          </View>

          {/* Name + badge */}
          <View style={s.nameRow}>
            <Text style={s.displayName}>{displayName}</Text>
            <Ionicons name="checkmark-circle" size={20} color={ACCENT} style={{ marginLeft: 6, marginTop: 2 }} />
          </View>

          {/* Bio */}
          {profile?.bio ? (
            <Text style={s.bio}>{profile.bio}</Text>
          ) : isOwnProfile ? (
            <TouchableOpacity onPress={openEditModal}>
              <Text style={s.bioPlaceholder}>+ Add a bio</Text>
            </TouchableOpacity>
          ) : null}

          {/* Location & Website */}
          {(profile?.location || profile?.website) ? (
            <View style={s.extraRow}>
              {profile.location && (
                <View style={s.extraItem}>
                  <Ionicons name="location-outline" size={13} color="#666" />
                  <Text style={s.extraText}>{profile.location}</Text>
                </View>
              )}
              {profile.website && (
                <View style={s.extraItem}>
                  <Ionicons name="link-outline" size={13} color={ACCENT} />
                  <Text style={[s.extraText, { color: ACCENT }]} numberOfLines={1}>{profile.website}</Text>
                </View>
              )}
            </View>
          ) : null}

          {/* Interest tags */}
          {(profile?.interest_tags || []).length > 0 && (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.tagsScroll} contentContainerStyle={s.tagsContent}>
              {profile.interest_tags.map(tag => (
                <View key={tag} style={s.tagChip}>
                  <Text style={s.tagText}>#{tag}</Text>
                </View>
              ))}
            </ScrollView>
          )}

          {/* ── Stats + CTA row (like profile.webp) ── */}
          <View style={s.statsCtaRow}>
            <TouchableOpacity style={s.statItem} onPress={() => openFollowList('followers')}>
              <Text style={s.statNum}>{fmtCount(profile?.followers_count)}</Text>
              <Text style={s.statLabel}>Followers</Text>
            </TouchableOpacity>

            <View style={s.statDivider} />

            <TouchableOpacity style={s.statItem} onPress={() => openFollowList('following')}>
              <Text style={s.statNum}>{fmtCount(profile?.following_count)}</Text>
              <Text style={s.statLabel}>Following</Text>
            </TouchableOpacity>

            <View style={s.statDivider} />

            <View style={s.statItem}>
              <Text style={s.statNum}>{fmtCount(posts.length || profile?.posts_count)}</Text>
              <Text style={s.statLabel}>Posts</Text>
            </View>

            {/* Follow / Edit button inline */}
            {isOwnProfile ? (
              <TouchableOpacity style={s.ctaBtn} onPress={openEditModal}>
                <Ionicons name="pencil" size={14} color="#2C1810" />
                <Text style={s.ctaBtnText}>Edit</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[s.ctaBtn, isFollowing && s.ctaBtnFollowing]}
                onPress={handleFollow}
                disabled={followLoading}
              >
                <Ionicons name={isFollowing ? 'checkmark' : 'person-add'} size={14} color={isFollowing ? '#D35400' : '#2C1810'} />
                <Text style={[s.ctaBtnText, isFollowing && { color: '#D35400' }]}>
                  {isFollowing ? 'Following' : 'Follow'}
                </Text>
              </TouchableOpacity>
            )}
          </View>

          {/* IQ score */}
          <View style={s.iqRow}>
            <Ionicons name="flash" size={13} color={ACCENT} />
            <Text style={s.iqText}>{profile?.iq_score || 0} IQ Points</Text>
            <View style={s.iqDot} />
            <Text style={s.iqText}>{profile?.badge || 'Newcomer'}</Text>
          </View>

          {/* Streak & Daily Goal — notebook style */}
          {isOwnProfile && (
            <View style={s.streakRow}>
              <View style={s.streakCard}>
                <View style={s.streakIconWrap}>
                  <Ionicons name="flame" size={20} color="#D35400" />
                </View>
                <Text style={s.streakNum}>7</Text>
                <Text style={s.streakLabel}>Day Streak</Text>
              </View>
              <View style={s.streakCard}>
                <View style={s.dailyGoalWrap}>
                  <View style={s.dailyGoalBg}>
                    <View style={[s.dailyGoalFill, { width: '60%' }]} />
                  </View>
                  <Text style={s.dailyGoalPct}>60%</Text>
                </View>
                <Text style={s.streakLabel}>Daily Goal</Text>
                <Text style={s.dailyGoalSub}>3 of 5 items</Text>
              </View>
              <View style={s.streakCard}>
                <View style={s.streakIconWrap}>
                  <Ionicons name="trophy" size={20} color="#EA580C" />
                </View>
                <Text style={s.streakNum}>{profile?.knowledge_rank || 'Novice'}</Text>
                <Text style={s.streakLabel}>Rank</Text>
              </View>
            </View>
          )}
        </View>

        {/* Message + Share buttons (for other profiles) */}
        {!isOwnProfile && (
          <View style={s.actionRow}>
            <TouchableOpacity style={s.actionBtn} onPress={() => openDM({ user_id: targetUserId, username: profile?.username, display_name: profile?.display_name })}>
              <Ionicons name="chatbubble-outline" size={18} color="#2C1810" />
              <Text style={s.actionBtnText}>Message</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.actionBtn} onPress={handleShare}>
              <Ionicons name="paper-plane-outline" size={18} color="#2C1810" />
              <Text style={s.actionBtnText}>Share</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ── Tabs ── */}
        <View style={s.tabsRow}>
          <TouchableOpacity style={[s.tab, activeTab === 'posts' && s.tabActive]} onPress={() => setActiveTab('posts')}>
            <Ionicons name="grid-outline" size={20} color={activeTab === 'posts' ? '#2C1810' : '#8A7860'} />
            <Text style={[s.tabLabel, activeTab === 'posts' && s.tabLabelActive]}>Posts</Text>
          </TouchableOpacity>
          {isOwnProfile && (
            <TouchableOpacity style={[s.tab, activeTab === 'saved' && s.tabActive]} onPress={() => setActiveTab('saved')}>
              <Ionicons name="bookmark-outline" size={20} color={activeTab === 'saved' ? '#2C1810' : '#8A7860'} />
              <Text style={[s.tabLabel, activeTab === 'saved' && s.tabLabelActive]}>Saved</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={[s.tab, activeTab === 'chats' && s.tabActive]} onPress={() => setActiveTab('chats')}>
            <Ionicons name="chatbubbles-outline" size={20} color={activeTab === 'chats' ? '#2C1810' : '#8A7860'} />
            <Text style={[s.tabLabel, activeTab === 'chats' && s.tabLabelActive]}>Chats</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.tab, activeTab === 'badges' && s.tabActive]} onPress={() => setActiveTab('badges')}>
            <Ionicons name="medal-outline" size={20} color={activeTab === 'badges' ? ACCENT : '#555'} />
            <Text style={[s.tabLabel, activeTab === 'badges' && s.tabLabelActive]}>Badges</Text>
          </TouchableOpacity>
        </View>

        {/* ── Tab Content ── */}
        {activeTab === 'posts' && (
          <View style={s.grid}>
            {posts.map((item, i) => (
              <TouchableOpacity key={item.id || i} style={s.gridItem}>
                <Image source={{ uri: getPostImage(item, i) }} style={s.gridImg} />
                {item.content_type === 'reel' && (
                  <View style={s.gridReelIcon}><Ionicons name="play" size={14} color="#FFF" /></View>
                )}
              </TouchableOpacity>
            ))}
            {posts.length === 0 && (
              <View style={s.emptyBox}>
                <Ionicons name="grid-outline" size={40} color="#333" />
                <Text style={s.emptyText}>No posts yet</Text>
              </View>
            )}
          </View>
        )}

        {activeTab === 'saved' && isOwnProfile && (
          <View style={s.grid}>
            {savedPosts.map((item, i) => (
              <TouchableOpacity key={item.id || i} style={s.gridItem}>
                <Image source={{ uri: getPostImage(item, i) }} style={s.gridImg} />
              </TouchableOpacity>
            ))}
            {savedPosts.length === 0 && (
              <View style={s.emptyBox}>
                <Ionicons name="bookmark-outline" size={40} color="#333" />
                <Text style={s.emptyText}>No saved content yet</Text>
              </View>
            )}
          </View>
        )}

        {activeTab === 'chats' && (
          <View style={{ paddingHorizontal: 12, paddingTop: 12 }}>
            {discussionHistory.length === 0 ? (
              <View style={s.emptyBox}>
                <Ionicons name="chatbubbles-outline" size={40} color="#333" />
                <Text style={s.emptyText}>No discussion chats yet</Text>
                <Text style={{ color: '#8A7860', fontSize: 12, marginTop: 4, textAlign: 'center', paddingHorizontal: 30 }}>
                  Join an AI discussion room and your chat history will appear here
                </Text>
              </View>
            ) : (
              discussionHistory.map((item, i) => {
                const disc = item.discussion;
                const msgs = item.messages || [];
                const lastMsg = msgs[msgs.length - 1];
                const DCOLORS = { physics: '#D35400', ai: '#1A9A7A', technology: '#3A5A9C', space: '#3A5A9C', biology: '#27AE60', history: '#8E44AD', environment: '#2ECC71', geopolitics: '#E74C3C', mathematics: '#F39C12' };
                const dc = DCOLORS[disc?.domain] || ACCENT;
                return (
                  <TouchableOpacity
                    key={disc?.id || i}
                    onPress={() => setSelectedChat(item)}
                    style={{ backgroundColor: '#FFFFFF', borderRadius: 14, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: dc + '30' }}
                  >
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                      <View style={{ width: 42, height: 42, borderRadius: 21, backgroundColor: dc + '20', justifyContent: 'center', alignItems: 'center' }}>
                        <Ionicons name="chatbubbles" size={20} color={dc} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={{ color: '#2C1810', fontSize: 14, fontWeight: '700' }} numberOfLines={1}>{disc?.title || 'Discussion Room'}</Text>
                        <Text style={{ color: '#8A7860', fontSize: 11, marginTop: 2 }} numberOfLines={1}>
                          {lastMsg ? (lastMsg.username === 'ScrollU AI' ? '🤖 ' : '') + lastMsg.body : 'No messages yet'}
                        </Text>
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <View style={{ backgroundColor: dc + '20', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3 }}>
                          <Text style={{ color: dc, fontSize: 10, fontWeight: '600' }}>{disc?.domain}</Text>
                        </View>
                        <Text style={{ color: '#8A7860', fontSize: 10, marginTop: 4 }}>{msgs.length} msgs</Text>
                      </View>
                    </View>
                  </TouchableOpacity>
                );
              })
            )}
          </View>
        )}

        {activeTab === 'badges' && (
          <View style={s.emptyBox}>
            <Ionicons name="medal-outline" size={40} color="#333" />
            <Text style={s.emptyText}>No badges earned yet</Text>
            <Text style={{ color: '#8A7860', fontSize: 12, marginTop: 4 }}>Keep scrolling to earn badges!</Text>
          </View>
        )}
      </ScrollView>

      {/* ── Fullscreen Photo Modal ── */}
      <Modal visible={showPhotoModal} animationType="fade" onRequestClose={() => setShowPhotoModal(false)}>
        <View style={{ flex: 1, backgroundColor: '#000', justifyContent: 'center', alignItems: 'center' }}>
          <TouchableOpacity
            style={{ position: 'absolute', top: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 54, right: 16, zIndex: 10, padding: 8 }}
            onPress={() => setShowPhotoModal(false)}
          >
            <Ionicons name="close" size={28} color="#FFF" />
          </TouchableOpacity>
          {profileImage && (
            <Image source={{ uri: profileImage }} style={{ width, height: width, resizeMode: 'contain' }} />
          )}
        </View>
      </Modal>

      {/* ── Discussion Chat History Modal ── */}
      <Modal visible={!!selectedChat} animationType="slide" onRequestClose={() => setSelectedChat(null)}>
        <View style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54, paddingBottom: 12, borderBottomWidth: 0.5, borderBottomColor: '#F5F0E4' }}>
            <TouchableOpacity onPress={() => setSelectedChat(null)} style={{ padding: 6, marginRight: 10 }}>
              <Ionicons name="arrow-back" size={24} color="#2C1810" />
            </TouchableOpacity>
            <View style={{ flex: 1 }}>
              <Text style={{ color: '#2C1810', fontSize: 16, fontWeight: '700' }} numberOfLines={1}>{selectedChat?.discussion?.title || 'Discussion'}</Text>
              <Text style={{ color: '#8A7860', fontSize: 12 }}>{selectedChat?.messages?.length || 0} messages · {selectedChat?.discussion?.domain}</Text>
            </View>
          </View>
          <ScrollView style={{ flex: 1, padding: 14 }} showsVerticalScrollIndicator={false}>
            {(selectedChat?.messages || []).length === 0 ? (
              <View style={{ alignItems: 'center', marginTop: 60 }}>
                <Ionicons name="chatbubbles-outline" size={40} color="#333" />
                <Text style={{ color: '#8A7860', marginTop: 8 }}>No messages in this room</Text>
              </View>
            ) : (
              (selectedChat?.messages || []).map((msg, i) => {
                const isAI = msg.username === 'ScrollU AI';
                const isMe = msg.user_id === targetUserId;
                return (
                  <View key={msg.id || i} style={{ marginBottom: 12, alignItems: isMe ? 'flex-end' : 'flex-start' }}>
                    <Text style={{ color: '#8A7860', fontSize: 11, marginBottom: 3, marginHorizontal: 4 }}>
                      {isAI ? '🤖 ScrollU AI' : isMe ? 'You' : msg.username}
                    </Text>
                    <View style={{ maxWidth: width * 0.75, backgroundColor: isAI ? '#F0F0FF' : isMe ? '#F0FFF0' : '#F5F0E4', borderRadius: 16, borderTopLeftRadius: isMe ? 16 : 4, borderTopRightRadius: isMe ? 4 : 16, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: isAI ? '#F9D84A30' : isMe ? ACCENT + '30' : '#D8D0C0' }}>
                      <Text style={{ color: '#2C1810', fontSize: 14, lineHeight: 20 }}>{msg.body}</Text>
                      <Text style={{ color: '#8A7860', fontSize: 10, marginTop: 4, textAlign: isMe ? 'right' : 'left' }}>
                        {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                      </Text>
                    </View>
                  </View>
                );
              })
            )}
            <View style={{ height: 30 }} />
          </ScrollView>
        </View>
      </Modal>

      {/* ── Edit Profile Modal ── */}
      <Modal visible={showEdit} animationType="slide" transparent>
        <View style={s.modalOverlay}>
          <View style={s.modalContent}>
            <View style={s.modalHeader}>
              <TouchableOpacity onPress={() => setShowEdit(false)}>
                <Text style={s.modalCancel}>Cancel</Text>
              </TouchableOpacity>
              <Text style={s.modalTitle}>Edit Profile</Text>
              <TouchableOpacity onPress={handleSaveProfile}>
                <Text style={s.modalDone}>Done</Text>
              </TouchableOpacity>
            </View>
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ padding: 20 }}>
              {/* Photo picker */}
              <TouchableOpacity style={s.editAvatarWrap} onPress={pickProfileImage}>
                <View style={s.editAvatar}>
                  {profileImage
                    ? <Image source={{ uri: profileImage }} style={s.editAvatarImg} />
                    : <Ionicons name="person" size={50} color="#555" />}
                </View>
                <View style={s.editPhotoBtn}>
                  <Ionicons name="camera" size={14} color="#FFFFFF" />
                  <Text style={s.editPhotoText}>Change Photo</Text>
                </View>
              </TouchableOpacity>

              <Text style={s.editLabel}>Display Name</Text>
              <TextInput style={s.editInput} value={editName} onChangeText={setEditName} placeholderTextColor="#555" placeholder="Display name" />

              <Text style={[s.editLabel, { marginTop: 18 }]}>Username</Text>
              <View style={s.editInputRow}>
                <Text style={s.editInputPrefix}>@</Text>
                <TextInput style={[s.editInput, { flex: 1, borderBottomWidth: 0 }]} value={editUsername} onChangeText={setEditUsername} placeholderTextColor="#555" placeholder="username" autoCapitalize="none" />
              </View>
              <View style={s.editInputUnderline} />

              <Text style={[s.editLabel, { marginTop: 18 }]}>Bio</Text>
              <TextInput style={s.editTextarea} value={editBio} onChangeText={setEditBio} placeholderTextColor="#555" placeholder="Tell the world about yourself..." multiline textAlignVertical="top" maxLength={150} />
              <Text style={s.charCount}>{editBio.length}/150</Text>

              <Text style={[s.editLabel, { marginTop: 18 }]}>Location</Text>
              <View style={s.editInputRow}>
                <Ionicons name="location-outline" size={16} color="#555" />
                <TextInput style={[s.editInput, { flex: 1, borderBottomWidth: 0 }]} value={editLocation} onChangeText={setEditLocation} placeholderTextColor="#555" placeholder="City, Country" />
              </View>
              <View style={s.editInputUnderline} />

              <Text style={[s.editLabel, { marginTop: 18 }]}>Website</Text>
              <View style={s.editInputRow}>
                <Ionicons name="link-outline" size={16} color="#555" />
                <TextInput style={[s.editInput, { flex: 1, borderBottomWidth: 0 }]} value={editWebsite} onChangeText={setEditWebsite} placeholderTextColor="#555" placeholder="https://yoursite.com" autoCapitalize="none" keyboardType="url" />
              </View>
              <View style={s.editInputUnderline} />

              <View style={{ height: 40 }} />
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* ── Followers / Following Modal ── */}
      <Modal visible={!!showFollowList} animationType="slide" transparent onRequestClose={() => setShowFollowList(null)}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: '#FFFFFF', borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: '75%', paddingBottom: 30 }}>
            <View style={{ alignItems: 'center', paddingVertical: 12 }}>
              <View style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: '#D8D0C0' }} />
            </View>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 0.5, borderBottomColor: '#F5F0E4' }}>
              <Text style={{ fontSize: 18, fontWeight: '700', color: '#2C1810' }}>
                {showFollowList === 'followers' ? 'Followers' : 'Following'}
              </Text>
              <TouchableOpacity onPress={() => setShowFollowList(null)}>
                <Ionicons name="close" size={24} color="#2C1810" />
              </TouchableOpacity>
            </View>
            {followListLoading ? (
              <View style={{ padding: 40, alignItems: 'center' }}>
                <Text style={{ color: '#8A7860' }}>Loading...</Text>
              </View>
            ) : followList.length === 0 ? (
              <View style={{ padding: 40, alignItems: 'center' }}>
                <Ionicons name="people-outline" size={40} color="#333" />
                <Text style={{ color: '#8A7860', marginTop: 8 }}>No {showFollowList} yet</Text>
              </View>
            ) : (
              <FlatList
                data={followList}
                keyExtractor={(item, i) => item.user_id || String(i)}
                renderItem={({ item }) => (
                  <TouchableOpacity
                    style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 12, paddingHorizontal: 16, borderBottomWidth: 0.5, borderBottomColor: '#F5F0E4' }}
                    onPress={() => { setShowFollowList(null); navigation?.navigate?.('UserProfile', { userId: item.user_id }); }}
                  >
                    <View style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: '#F5F0E4', justifyContent: 'center', alignItems: 'center', marginRight: 12 }}>
                      {item.avatar_url
                        ? <Image source={{ uri: item.avatar_url }} style={{ width: 44, height: 44, borderRadius: 22 }} />
                        : <Ionicons name="person" size={20} color="#555" />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={{ color: '#2C1810', fontSize: 15, fontWeight: '600' }}>{item.display_name || item.username}</Text>
                      <Text style={{ color: '#8A7860', fontSize: 13 }}>@{item.username}</Text>
                    </View>
                    <View style={{ paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16, backgroundColor: ACCENT + '15' }}>
                      <Text style={{ color: ACCENT, fontSize: 12, fontWeight: '600' }}>{item.badge || 'Newcomer'}</Text>
                    </View>
                  </TouchableOpacity>
                )}
              />
            )}
          </View>
        </View>
      </Modal>

      {/* ── Settings Modal ── */}
      <Modal visible={showSettings} animationType="slide" transparent>
        <View style={s.modalOverlay}>
          <View style={s.settingsModal}>
            <View style={s.sheetHandle}><View style={s.handleBar} /></View>
            <View style={s.settingsHeader}>
              <Text style={s.settingsTitle}>Settings</Text>
              <TouchableOpacity onPress={() => setShowSettings(false)}>
                <Ionicons name="close" size={24} color="#2C1810" />
              </TouchableOpacity>
            </View>
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={s.settingsSectionTitle}>ACCOUNT</Text>
              {renderSettingsItem({ icon: 'person-outline', label: 'Account Info', value: `@${profile?.username}`, onPress: () => Alert.alert('Account', `@${profile?.username}`) })}
              {renderSettingsItem({ icon: 'pencil-outline', label: 'Edit Profile', onPress: () => { setShowSettings(false); openEditModal(); } })}
              {renderSettingsItem({ icon: 'key-outline', label: 'Password & Security', onPress: () => Alert.alert('Security', 'Coming soon') })}

              <Text style={s.settingsSectionTitle}>PREFERENCES</Text>
              {renderSettingsItem({ icon: 'notifications-outline', label: 'Push Notifications', isToggle: true, toggleValue: notifEnabled, onToggle: setNotifEnabled })}
              {renderSettingsItem({ icon: 'lock-closed-outline', label: 'Private Account', isToggle: true, toggleValue: privateAccount, onToggle: setPrivateAccount })}
              {renderSettingsItem({ icon: 'moon-outline', label: 'Dark Mode', isToggle: true, toggleValue: isDarkTheme, onToggle: toggleTheme })}

              <Text style={s.settingsSectionTitle}>CONTENT</Text>
              {renderSettingsItem({ icon: 'bookmark-outline', label: 'Saved Content', onPress: () => { setShowSettings(false); setActiveTab('saved'); } })}
              {renderSettingsItem({ icon: 'flash-outline', label: 'IQ Points', value: `${profile?.iq_score || 0} IQ`, color: ACCENT })}
              {renderSettingsItem({ icon: 'share-social-outline', label: 'Share Profile', onPress: handleShare })}

              <Text style={s.settingsSectionTitle}>ABOUT</Text>
              {renderSettingsItem({ icon: 'information-circle-outline', label: 'About ScrollUForward', onPress: () => Alert.alert('About', 'v1.0.0') })}
              {renderSettingsItem({ icon: 'help-circle-outline', label: 'Help & Support', onPress: () => Alert.alert('Help', 'support@scrolluforward.app') })}

              <View style={{ marginTop: 10 }}>
                {renderSettingsItem({ icon: 'log-out-outline', label: 'Log Out', onPress: handleLogout, color: '#ED4956', showChevron: false })}
              </View>
              <Text style={s.versionText}>ScrollUForward v1.0.0</Text>
              <View style={{ height: 40 }} />
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 54, paddingBottom: 10 },
  headerTitle: { fontSize: 16, fontWeight: '700', color: '#2C1810' },
  headerBtn: { width: 38, height: 38, backgroundColor: '#F5F0E4', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 },

  // ── Profile Card — polaroid sketch style ──
  profileCard: {
    marginHorizontal: 16, marginTop: 8,
    backgroundColor: '#FFFCF2',
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 12,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 3,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 5 },
    }),
    transform: [{ rotate: '-0.3deg' }],
  },

  // Cover photo area — polaroid style with extra bottom padding
  coverArea: { height: CARD_PHOTO_HEIGHT, backgroundColor: '#F3EACD', position: 'relative', padding: 7, paddingBottom: 0 },
  coverPhoto: { width: '100%', height: CARD_PHOTO_HEIGHT - 7, resizeMode: 'cover', borderTopLeftRadius: 2, borderTopRightRadius: 8 },
  coverOverlay: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 60, backgroundColor: 'transparent' },
  coverPlaceholder: { width: '100%', height: CARD_PHOTO_HEIGHT, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5F0E4' },
  cameraFab: {
    position: 'absolute', bottom: 12, right: 16,
    width: 36, height: 36,
    backgroundColor: '#2563EB',
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 1.5, borderColor: '#2C1810',
    borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },

  // Name + verified
  nameRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 14 },
  displayName: { fontSize: 24, fontWeight: '900', color: '#2C1810', letterSpacing: -0.5 },

  // Bio
  bio: { fontSize: 14, lineHeight: 20, color: '#8A7860', paddingHorizontal: 16, marginTop: 6 },
  bioPlaceholder: { fontSize: 14, color: '#8A7558', fontStyle: 'italic', paddingHorizontal: 16, marginTop: 6 },

  // Extra info
  extraRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, paddingHorizontal: 16, marginTop: 8 },
  extraItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  extraText: { fontSize: 13, color: '#8A7860' },

  // Tags
  tagsScroll: { marginTop: 10 },
  tagsContent: { paddingHorizontal: 16, gap: 8 },
  tagChip: { paddingHorizontal: 10, paddingVertical: 5, borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#2C1810' },
  tagText: { fontSize: 12, fontWeight: '600', color: '#5A4A30' },

  // Stats + CTA row — sketch card style
  statsCtaRow: {
    flexDirection: 'row', alignItems: 'center',
    marginTop: 16, marginHorizontal: 16, marginBottom: 12,
    backgroundColor: '#FFFCF2',
    paddingVertical: 12, paddingHorizontal: 12,
    borderWidth: 2, borderColor: '#2C1810',
    borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3,
    ...Platform.select({
      ios: { shadowColor: '#B8AE90', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  statItem: { flex: 1, alignItems: 'center' },
  statNum: { fontSize: 18, fontWeight: '800', color: '#2C1810' },
  statLabel: { fontSize: 11, color: '#8A7860', marginTop: 2 },
  statDivider: { width: 1.5, height: 28, backgroundColor: '#2C1810', marginHorizontal: 4, opacity: 0.15 },
  ctaBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#2563EB',
    paddingHorizontal: 14, paddingVertical: 8, marginLeft: 8,
    borderWidth: 1.5, borderColor: '#2C1810',
    borderTopLeftRadius: 2, borderTopRightRadius: 8, borderBottomLeftRadius: 8, borderBottomRightRadius: 2,
  },
  ctaBtnFollowing: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: ACCENT },
  ctaBtnText: { fontSize: 13, fontWeight: '700', color: '#FFFFFF' },

  // IQ row
  iqRow: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 16, paddingBottom: 14 },
  iqText: { fontSize: 12, color: '#8A7860', fontWeight: '600' },
  iqDot: { width: 3, height: 3, borderRadius: 2, backgroundColor: '#D8D0C0' },

  // Streak & Daily Goal
  streakRow: {
    flexDirection: 'row', gap: 8, paddingHorizontal: 16, paddingBottom: 14, marginTop: 4,
  },
  streakCard: {
    flex: 1, alignItems: 'center', paddingVertical: 10, paddingHorizontal: 6,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#2C1810',
    borderTopLeftRadius: 3, borderTopRightRadius: 10,
    borderBottomLeftRadius: 10, borderBottomRightRadius: 3,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 2 },
    }),
  },
  streakIconWrap: {
    width: 32, height: 32, borderRadius: 3,
    borderWidth: 1, borderColor: '#D8D0C0',
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#FFFCF2', marginBottom: 4,
  },
  streakNum: { fontSize: 16, fontWeight: '800', color: '#2C1810' },
  streakLabel: { fontSize: 10, fontWeight: '600', color: '#8A7860', marginTop: 2 },
  dailyGoalWrap: { width: '100%', paddingHorizontal: 4, marginBottom: 4 },
  dailyGoalBg: {
    height: 8, borderRadius: 4, backgroundColor: '#E8E0D0',
    borderWidth: 1, borderColor: '#D8D0C0', overflow: 'hidden',
  },
  dailyGoalFill: { height: '100%', backgroundColor: '#27AE60', borderRadius: 3 },
  dailyGoalPct: { fontSize: 14, fontWeight: '800', color: '#27AE60', textAlign: 'center', marginTop: 2 },
  dailyGoalSub: { fontSize: 9, color: '#8A7860', marginTop: 1 },

  // Action row (for other profiles)
  actionRow: { flexDirection: 'row', paddingHorizontal: 16, gap: 10, marginTop: 12 },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, height: 44, backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3, ...Platform.select({ ios: { shadowColor: '#B8AE90', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 }, android: { elevation: 2 } }) },
  actionBtnText: { fontSize: 14, fontWeight: '600', color: '#2C1810' },

  // Tabs — sketch style with ink border
  tabsRow: { flexDirection: 'row', marginTop: 20, borderTopWidth: 2, borderTopColor: '#2C1810', marginHorizontal: 0, backgroundColor: '#FFFCF2' },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', gap: 4 },
  tabActive: { borderTopWidth: 3, borderTopColor: '#2563EB', backgroundColor: 'rgba(37,99,235,0.06)' },
  tabLabel: { fontSize: 10, color: '#8A7860', fontWeight: '600' },
  tabLabelActive: { color: '#2C1810' },

  // Grid
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  gridItem: { width: POST_SIZE, height: POST_SIZE, padding: 1, position: 'relative' },
  gridImg: { width: '100%', height: '100%', borderRadius: 2 },
  gridReelIcon: { position: 'absolute', top: 6, right: 6, backgroundColor: 'rgba(0,0,0,0.5)', width: 24, height: 24, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },

  emptyBox: { alignItems: 'center', paddingVertical: 50, width: '100%', gap: 10 },
  emptyText: { color: '#8A7860', fontSize: 14 },

  // Edit Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#FBF8F0', borderTopLeftRadius: 24, borderTopRightRadius: 24, maxHeight: '92%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 0.5, borderBottomColor: '#D8D0C0' },
  modalTitle: { fontSize: 16, fontWeight: '700', color: '#2C1810' },
  modalCancel: { fontSize: 16, color: '#8A7860' },
  modalDone: { fontSize: 16, fontWeight: '700', color: '#2563EB' },
  editAvatarWrap: { alignItems: 'center', marginBottom: 24 },
  editAvatar: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#F3EACD', justifyContent: 'center', alignItems: 'center', overflow: 'hidden', marginBottom: 10, borderWidth: 2, borderColor: '#C4AA78' },
  editAvatarImg: { width: 100, height: 100, borderRadius: 50 },
  editPhotoBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#2563EB', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 7 },
  editPhotoText: { fontSize: 13, fontWeight: '700', color: '#FFFFFF' },
  editLabel: { fontSize: 12, fontWeight: '600', color: '#8A7860', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.8 },
  editInput: { borderBottomWidth: 1, borderBottomColor: '#D8D0C0', paddingVertical: 10, fontSize: 16, color: '#2C1810' },
  editInputRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  editInputUnderline: { height: 1, backgroundColor: '#F5F0E4', marginTop: 0 },
  editTextarea: { borderBottomWidth: 1, borderBottomColor: '#D8D0C0', paddingVertical: 10, fontSize: 16, color: '#2C1810', minHeight: 80 },
  charCount: { fontSize: 11, color: '#8A7860', textAlign: 'right', marginTop: 4 },

  // Settings
  settingsModal: { backgroundColor: '#FBF8F0', borderTopLeftRadius: 24, borderTopRightRadius: 24, height: '90%' },
  sheetHandle: { alignItems: 'center', paddingVertical: 12 },
  handleBar: { width: 40, height: 4, borderRadius: 2, backgroundColor: '#D8D0C0' },
  settingsHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 14, borderBottomWidth: 0.5, borderBottomColor: '#D8D0C0' },
  settingsTitle: { fontSize: 20, fontWeight: '700', color: '#2C1810' },
  settingsSectionTitle: { fontSize: 11, fontWeight: '700', letterSpacing: 1.2, color: '#8A7860', paddingHorizontal: 16, paddingTop: 20, paddingBottom: 8 },
  settingsItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 14, gap: 14 },
  settingsIconCircle: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  settingsLabel: { fontSize: 15, fontWeight: '500' },
  settingsValue: { fontSize: 12, color: '#8A7860', marginTop: 1 },
  versionText: { textAlign: 'center', fontSize: 12, color: '#8A7860', marginTop: 20 },
});
