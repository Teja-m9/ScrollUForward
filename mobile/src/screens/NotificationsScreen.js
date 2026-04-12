import React, { useState, useCallback, useContext } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  RefreshControl, Platform, StatusBar, Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ThemeContext } from '../../App';
import { DoodleDivider, Stamp, SketchAvatar, StickyNote, NotebookMargin } from '../components/SketchComponents';

const { width } = Dimensions.get('window');

// Notification Item Component — sketch card style
function NotificationItem({ item, onPress, theme }) {
  const typeConfig = {
    like: { icon: 'heart', color: '#E74C3C', stamp: 'LIKED' },
    comment: { icon: 'chatbubble', color: '#3A5A9C', stamp: 'COMMENT' },
    follow: { icon: 'person-add', color: '#27AE60', stamp: 'FOLLOWED' },
    mention: { icon: 'at', color: '#8E44AD', stamp: 'MENTION' },
    repost: { icon: 'repeat', color: '#D35400', stamp: 'REPOST' },
  };
  const config = typeConfig[item.type] || { icon: item.icon || 'notifications', color: item.iconColor || '#5A4A30', stamp: 'ACTIVITY' };

  return (
    <TouchableOpacity
      style={[styles.notifItem, item.unread && styles.notifItemUnread]}
      onPress={() => onPress(item)}
      activeOpacity={0.7}
    >
      {/* Notebook margin line */}
      <View style={styles.itemMarginLine} />

      {item.unread && <View style={styles.unreadDot} />}

      <SketchAvatar
        letter={item.avatar || '?'}
        size={42}
        bgColor={config.color + '20'}
        textColor={config.color}
      />

      {/* Type icon badge */}
      <View style={[styles.iconBadge, { backgroundColor: config.color + '15', borderColor: config.color }]}>
        <Ionicons name={config.icon} size={11} color={config.color} />
      </View>

      <View style={styles.notifContent}>
        <Text style={styles.notifMessage} numberOfLines={2}>
          <Text style={styles.notifUser}>{item.user} </Text>
          {item.message}
        </Text>
        <View style={styles.notifMeta}>
          <Text style={styles.notifTime}>{item.time}</Text>
          <Stamp label={config.stamp} color={config.color} style={styles.miniStamp} />
        </View>
      </View>

      {item.type === 'follow' && (
        <TouchableOpacity style={styles.followBtn} activeOpacity={0.8}>
          <Text style={styles.followBtnText}>Follow</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

// Section Header — hand-drawn underline
function SectionHeader({ title, count }) {
  return (
    <View style={styles.sectionHeader}>
      <View style={styles.sectionTitleRow}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {count > 0 && (
          <View style={styles.countBadge}>
            <Text style={styles.countBadgeText}>{count}</Text>
          </View>
        )}
      </View>
      <View style={styles.sectionUnderline}>
        <View style={styles.underlineThick} />
        <View style={styles.underlineThin} />
      </View>
    </View>
  );
}

// Main Screen
export default function NotificationsScreen({ navigation }) {
  const themeCtx = useContext(ThemeContext);
  const theme = themeCtx?.theme;
  const [notifications, setNotifications] = useState({ new: [], earlier: [] });
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      // TODO: Replace with real API call when notifications endpoint is ready
    } catch (e) {
      console.log('Failed to refresh notifications', e);
    } finally {
      setRefreshing(false);
    }
  }, []);

  const handleNotificationPress = useCallback((item) => {
    setNotifications((prev) => ({
      new: prev.new.map((n) =>
        n.id === item.id ? { ...n, unread: false } : n
      ),
      earlier: prev.earlier.map((n) =>
        n.id === item.id ? { ...n, unread: false } : n
      ),
    }));
  }, []);

  const sections = [];
  if (notifications.new.length > 0) {
    sections.push({ type: 'header', key: 'header-new', title: 'New', count: notifications.new.length });
    notifications.new.forEach((n) => sections.push({ type: 'item', key: n.id, data: n }));
  }
  if (notifications.earlier.length > 0) {
    sections.push({ type: 'header', key: 'header-earlier', title: 'Earlier', count: 0 });
    notifications.earlier.forEach((n) => sections.push({ type: 'item', key: n.id, data: n }));
  }

  const renderItem = ({ item }) => {
    if (item.type === 'header') {
      return <SectionHeader title={item.title} count={item.count} />;
    }
    return <NotificationItem item={item.data} onPress={handleNotificationPress} theme={theme} />;
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FBF8F0" />

      {/* Notebook margin running down the page */}
      <NotebookMargin />

      {/* Header — notebook sketch style */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="arrow-back" size={22} color="#2C1810" />
        </TouchableOpacity>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View style={{ flexDirection: 'row', gap: 3 }}>
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
            <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
          </View>
          <Text style={styles.headerTitle}>Notifications</Text>
        </View>
        <TouchableOpacity
          style={styles.markReadBtn}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          onPress={() => {
            setNotifications((prev) => ({
              new: prev.new.map((n) => ({ ...n, unread: false })),
              earlier: prev.earlier,
            }));
          }}
        >
          <View style={styles.markReadBox}>
            <Ionicons name="checkmark-done" size={18} color="#2C1810" />
          </View>
        </TouchableOpacity>
      </View>

      <FlatList
        data={sections}
        keyExtractor={(item) => item.key}
        renderItem={renderItem}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#F9D84A"
            colors={['#F9D84A']}
            progressBackgroundColor="#FFFFFF"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <StickyNote color="rgba(249,216,74,0.3)" rotate={-2}>
              <View style={{ alignItems: 'center', padding: 10 }}>
                <Ionicons name="notifications-off-outline" size={48} color="#8A7860" />
                <Text style={styles.emptyText}>No notifications yet</Text>
                <Text style={styles.emptySubtext}>
                  When someone interacts with your content, you'll see it here.
                </Text>
              </View>
            </StickyNote>
            <DoodleDivider style={{ marginTop: 20, width: 200 }} />
          </View>
        }
      />
    </View>
  );
}

const TOP_PADDING = Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 50;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF6E3' },

  // Header
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingTop: TOP_PADDING, paddingBottom: 12, paddingHorizontal: 16,
    backgroundColor: '#FFFCF2', zIndex: 2,
  },
  backBtn: {
    marginRight: 12,
    width: 34, height: 34,
    borderWidth: 1.5, borderColor: '#2C1810',
    borderTopLeftRadius: 3, borderTopRightRadius: 8,
    borderBottomLeftRadius: 8, borderBottomRightRadius: 3,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#FFFCF2',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  headerTitle: {
    flex: 1, color: '#2C1810', fontSize: 22, fontWeight: '900',
    letterSpacing: 1.5, textTransform: 'uppercase',
  },
  markReadBtn: { padding: 4 },
  markReadBox: {
    backgroundColor: '#F9D84A', borderWidth: 1.5, borderColor: '#2C1810',
    borderRadius: 3, paddingHorizontal: 8, paddingVertical: 4,
    transform: [{ rotate: '1deg' }],
  },

  // List
  listContent: { paddingBottom: 40, paddingLeft: 42 },

  // Section Header
  sectionHeader: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 8 },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sectionTitle: { color: '#2C1810', fontSize: 14, fontWeight: '800', letterSpacing: 2, textTransform: 'uppercase' },
  countBadge: {
    backgroundColor: '#FFD60A', borderWidth: 1.5, borderColor: '#2C1810',
    borderRadius: 3, minWidth: 22, height: 22,
    justifyContent: 'center', alignItems: 'center', paddingHorizontal: 6,
    transform: [{ rotate: '-2deg' }],
  },
  countBadgeText: { color: '#2C1810', fontSize: 11, fontWeight: '700' },
  sectionUnderline: { marginTop: 4, gap: 2 },
  underlineThick: { height: 3, width: 40, borderRadius: 2, backgroundColor: '#FFD60A' },
  underlineThin: { height: 1, width: 70, backgroundColor: '#D8D0C0' },

  // Notification Item
  notifItem: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 12, paddingHorizontal: 14, paddingLeft: 16,
    marginHorizontal: 8, marginVertical: 3,
    backgroundColor: '#FFFCF2',
    borderWidth: 1.5, borderColor: '#E6D5B8',
    borderTopLeftRadius: 3, borderTopRightRadius: 10,
    borderBottomLeftRadius: 10, borderBottomRightRadius: 3,
    gap: 10,
  },
  notifItemUnread: {
    backgroundColor: '#FFFCF2',
    borderColor: '#2C1810',
    borderWidth: 2,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  itemMarginLine: {
    position: 'absolute', left: 0, top: 0, bottom: 0,
    width: 3, backgroundColor: 'rgba(192,57,43,0.12)',
    borderTopLeftRadius: 3,
    borderBottomLeftRadius: 10,
  },
  unreadDot: {
    position: 'absolute', left: 6, top: 6,
    width: 8, height: 8, borderRadius: 1,
    backgroundColor: '#F9D84A', borderWidth: 1, borderColor: '#2C1810',
    transform: [{ rotate: '45deg' }],
  },
  iconBadge: {
    position: 'absolute', left: 50, top: 38,
    width: 20, height: 20, borderRadius: 3,
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 1.5, transform: [{ rotate: '-3deg' }],
  },
  notifContent: { flex: 1, marginLeft: 4 },
  notifMessage: { color: '#5A4A30', fontSize: 14, lineHeight: 20 },
  notifUser: { color: '#2C1810', fontWeight: '700' },
  notifMeta: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 4 },
  notifTime: { color: '#8A7860', fontSize: 12 },
  miniStamp: { paddingHorizontal: 5, paddingVertical: 1, borderWidth: 1.5, transform: [{ rotate: '-1deg' }, { scale: 0.75 }] },

  // Follow Button
  followBtn: {
    backgroundColor: '#FFD60A', paddingHorizontal: 14, paddingVertical: 7,
    borderWidth: 1.5, borderColor: '#2C1810',
    borderTopLeftRadius: 3, borderTopRightRadius: 8,
    borderBottomLeftRadius: 8, borderBottomRightRadius: 3,
    transform: [{ rotate: '1deg' }],
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  followBtnText: { color: '#2C1810', fontSize: 13, fontWeight: '700' },

  // Empty State
  emptyState: { alignItems: 'center', justifyContent: 'center', paddingTop: 60, paddingHorizontal: 40 },
  emptyText: { color: '#2C1810', fontSize: 18, fontWeight: '700', marginTop: 12 },
  emptySubtext: { color: '#8A7860', fontSize: 14, textAlign: 'center', marginTop: 6, lineHeight: 20 },
});
