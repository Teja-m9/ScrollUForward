import React, { useState, useRef, useEffect, useContext, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  StatusBar, TextInput, KeyboardAvoidingView, Platform,
  Animated, ActivityIndicator, Image, Vibration, Modal, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ThemeContext, AuthContext } from '../../App';
import { chatAPI, getWebSocketURL, usersAPI } from '../api';
import { DoodleDivider, SketchAvatar, StickyNote, NotebookMargin } from '../components/SketchComponents';

// ─── Helpers ──────────────────────────────────────────
const formatTime = (isoOrDate) => {
  if (!isoOrDate) return '';
  const d = typeof isoOrDate === 'string' ? new Date(isoOrDate) : isoOrDate;
  if (isNaN(d.getTime())) return typeof isoOrDate === 'string' ? isoOrDate : '';
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'Now';
  if (diffMin < 60) return `${diffMin}m`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d`;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
};

const formatMessageTime = (isoOrDate) => {
  if (!isoOrDate) return '';
  const d = typeof isoOrDate === 'string' ? new Date(isoOrDate) : isoOrDate;
  if (isNaN(d.getTime())) return typeof isoOrDate === 'string' ? isoOrDate : '';
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
};

const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name[0].toUpperCase();
};

const avatarColors = [
  '#6C5CE7', '#00B894', '#E17055', '#0984E3',
  '#FDCB6E', '#E84393', '#00CEC9', '#D63031',
];
const getAvatarColor = (id) => {
  if (!id) return avatarColors[0];
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = id.charCodeAt(i) + ((hash << 5) - hash);
  return avatarColors[Math.abs(hash) % avatarColors.length];
};

// Check if two dates are different calendar days
const isDifferentDay = (d1, d2) => {
  if (!d1 || !d2) return true;
  const a = new Date(d1);
  const b = new Date(d2);
  return a.getFullYear() !== b.getFullYear() ||
    a.getMonth() !== b.getMonth() ||
    a.getDate() !== b.getDate();
};

const formatDaySeparator = (iso) => {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round((today - target) / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return d.toLocaleDateString(undefined, { weekday: 'long' });
  return d.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' });
};

// ─── Typing Indicator Dots ────────────────────────────
function TypingDots({ color }) {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animate = (dot, delay) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(dot, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0, duration: 300, useNativeDriver: true }),
          Animated.delay(600 - delay),
        ])
      );
    const a1 = animate(dot1, 0);
    const a2 = animate(dot2, 200);
    const a3 = animate(dot3, 400);
    a1.start(); a2.start(); a3.start();
    return () => { a1.stop(); a2.stop(); a3.stop(); };
  }, []);

  const dotStyle = (anim) => ({
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: color,
    marginHorizontal: 2,
    opacity: anim.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] }),
    transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [0, -4] }) }],
  });

  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 4 }}>
      <Animated.View style={dotStyle(dot1)} />
      <Animated.View style={dotStyle(dot2)} />
      <Animated.View style={dotStyle(dot3)} />
    </View>
  );
}

// ─── Avatar Component ─────────────────────────────────
function Avatar({ name, id, size = 48, online, avatarUrl }) {
  const bgColor = getAvatarColor(id || name);
  return (
    <View style={{ width: size, height: size }}>
      {avatarUrl ? (
        <Image
          source={{ uri: avatarUrl }}
          style={{ width: size, height: size, borderRadius: size * 0.5, borderWidth: 1.5, borderColor: '#2C1810' }}
        />
      ) : (
        <View style={{
          width: size, height: size, borderRadius: size * 0.5,
          backgroundColor: bgColor + '20',
          justifyContent: 'center', alignItems: 'center',
          borderWidth: 1.5, borderColor: '#2C1810',
        }}>
          <Text style={{
            fontSize: size * 0.38, fontWeight: '700',
            color: bgColor,
          }}>
            {getInitials(name)}
          </Text>
        </View>
      )}
      {online && (
        <View style={{
          width: size * 0.26, height: size * 0.26,
          borderRadius: 2,
          backgroundColor: '#27AE60',
          borderWidth: 1.5, borderColor: '#2C1810',
          position: 'absolute', bottom: -1, right: -1,
          transform: [{ rotate: '45deg' }],
        }} />
      )}
    </View>
  );
}

// ─── Main ChatScreen ──────────────────────────────────
export default function ChatScreen({ dmTarget = null, onClose = null }) {
  const { theme } = useContext(ThemeContext);
  const authContext = useContext(AuthContext);
  const currentUser = authContext?.user;

  // ── State ──
  const [activeRoom, setActiveRoom] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [typingUsers, setTypingUsers] = useState({});
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [wsConnected, setWsConnected] = useState(false);

  // Edit mode
  const [editMode, setEditMode] = useState(false);
  const [selectedRooms, setSelectedRooms] = useState(new Set());

  // New message modal
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMsgSearch, setNewMsgSearch] = useState('');
  const [followList, setFollowList] = useState([]);
  const [followListLoading, setFollowListLoading] = useState(false);
  const [sendingHi, setSendingHi] = useState({});

  const flatListRef = useRef(null);
  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // ── WebSocket ──
  const connectWebSocket = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;
      const wsUrl = getWebSocketURL(token);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        // Stop polling if WS connected
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWsMessage(data);
        } catch (e) { /* ignore non-JSON */ }
      };

      ws.onerror = () => {
        setWsConnected(false);
        startPolling();
      };

      ws.onclose = () => {
        setWsConnected(false);
        wsRef.current = null;
        // Reconnect after 3s
        setTimeout(connectWebSocket, 3000);
        startPolling();
      };

      wsRef.current = ws;
    } catch (e) {
      startPolling();
    }
  }, []);

  const handleWsMessage = useCallback((data) => {
    switch (data.type) {
      case 'new_message':
        // Update messages if in the relevant room
        if (activeRoom && data.room_id === activeRoom.id) {
          setMessages(prev => {
            if (prev.find(m => m.id === data.message.id)) return prev;
            return [...prev, data.message];
          });
          setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
        }
        // Update room preview
        setRooms(prev => prev.map(r =>
          r.id === data.room_id
            ? {
                ...r,
                last_message: data.message.body || data.message.content,
                last_message_time: data.message.created_at || new Date().toISOString(),
                unread_count: activeRoom?.id === data.room_id ? r.unread_count : (r.unread_count || 0) + 1,
              }
            : r
        ));
        break;

      case 'typing':
        if (data.user_id !== currentUser?.id) {
          setTypingUsers(prev => ({ ...prev, [data.room_id]: data.username || 'Someone' }));
          setTimeout(() => {
            setTypingUsers(prev => {
              const next = { ...prev };
              delete next[data.room_id];
              return next;
            });
          }, 3000);
        }
        break;

      case 'presence':
      case 'online':
        setOnlineUsers(prev => {
          const next = new Set(prev);
          if (data.status === 'online') next.add(data.user_id);
          else next.delete(data.user_id);
          return next;
        });
        break;

      default:
        break;
    }
  }, [activeRoom, currentUser]);

  const sendWsMessage = (payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  };

  const sendTypingIndicator = () => {
    if (!activeRoom) return;
    sendWsMessage({ type: 'typing', room_id: activeRoom.id });
  };

  // ── Polling fallback ──
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return; // already polling
    pollIntervalRef.current = setInterval(() => {
      fetchRooms(true);
      if (activeRoom) fetchMessages(activeRoom.id, true);
    }, 3000);
  }, [activeRoom]);

  // ── Data fetching ──
  const fetchRooms = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const res = await chatAPI.listRooms();
      const roomsData = res.data?.rooms || res.data || [];
      setRooms(Array.isArray(roomsData) ? roomsData : []);
    } catch (e) {
      // If API fails on first load, use empty array
      if (!silent) setRooms([]);
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  const fetchMessages = useCallback(async (roomId, silent = false) => {
    try {
      if (!silent) setMessagesLoading(true);
      const res = await chatAPI.listMessages(roomId, 50);
      const msgData = res.data?.messages || res.data || [];
      setMessages(Array.isArray(msgData) ? msgData : []);
    } catch (e) {
      if (!silent) setMessages([]);
    } finally {
      if (!silent) setMessagesLoading(false);
    }
  }, []);

  // ── Open or create DM room with a target user ──
  const openOrCreateDM = useCallback(async (targetUser) => {
    try {
      setLoading(true);
      // Try to find existing DM room with this user
      const res = await chatAPI.listRooms();
      const existingRooms = res.data?.rooms || res.data || [];
      const dmName = `dm_${[currentUser?.user_id, targetUser.user_id].sort().join('_')}`;
      const existing = existingRooms.find(r => r.name === dmName);
      if (existing) {
        setActiveRoom(existing);
      } else {
        // Create a new DM room
        const created = await chatAPI.createRoom({
          name: dmName,
          is_group: false,
          participant_ids: [targetUser.user_id],
        });
        const newRoom = created.data;
        setRooms(prev => [newRoom, ...prev]);
        setActiveRoom(newRoom);
      }
    } catch (e) {
      // Fallback: create a local-only room object
      setActiveRoom({
        id: `local_${targetUser.user_id}`,
        name: targetUser.display_name || targetUser.username || 'Chat',
        participants: [currentUser?.user_id, targetUser.user_id],
        is_group: false,
        last_message: '',
      });
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  // ── Effects ──
  useEffect(() => {
    fetchRooms();
    connectWebSocket();

    // Fade in
    Animated.timing(fadeAnim, {
      toValue: 1, duration: 300, useNativeDriver: true,
    }).start();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    };
  }, []);

  // Auto-open DM when dmTarget is passed from ProfileScreen
  useEffect(() => {
    if (dmTarget?.user_id) {
      openOrCreateDM(dmTarget);
    }
  }, [dmTarget]);

  useEffect(() => {
    if (activeRoom) {
      fetchMessages(activeRoom.id);
      // Mark room as read
      setRooms(prev => prev.map(r =>
        r.id === activeRoom.id ? { ...r, unread_count: 0 } : r
      ));
    }
  }, [activeRoom]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0 && activeRoom) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 150);
    }
  }, [messages.length]);

  // ── Edit mode helpers ──
  const toggleRoomSelection = (roomId) => {
    setSelectedRooms(prev => {
      const next = new Set(prev);
      if (next.has(roomId)) next.delete(roomId);
      else next.add(roomId);
      return next;
    });
  };

  const deleteSelectedRooms = () => {
    if (selectedRooms.size === 0) return;
    Alert.alert(
      'Delete Conversations',
      `Delete ${selectedRooms.size} conversation${selectedRooms.size > 1 ? 's' : ''}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete', style: 'destructive',
          onPress: async () => {
            for (const roomId of selectedRooms) {
              try { await chatAPI.deleteRoom(roomId); } catch {}
            }
            setRooms(prev => prev.filter(r => !selectedRooms.has(r.id)));
            setSelectedRooms(new Set());
            setEditMode(false);
          },
        },
      ]
    );
  };

  // ── New Message: fetch followers + following ──
  const fetchFollowList = useCallback(async () => {
    if (!currentUser?.user_id) return;
    setFollowListLoading(true);
    try {
      const [followersRes, followingRes] = await Promise.all([
        usersAPI.followers(currentUser.user_id, 100),
        usersAPI.following(currentUser.user_id, 100),
      ]);
      const followers = followersRes.data || [];
      const following = followingRes.data || [];
      // Merge and dedupe by user_id
      const map = new Map();
      [...followers, ...following].forEach(u => {
        const id = u.user_id || u.$id || u.id;
        if (id && !map.has(id)) map.set(id, { user_id: id, username: u.username || '', display_name: u.display_name || u.username || '', avatar_url: u.avatar_url || null });
      });
      setFollowList(Array.from(map.values()));
    } catch {
      setFollowList([]);
    } finally {
      setFollowListLoading(false);
    }
  }, [currentUser]);

  const sendHiAndOpen = useCallback(async (targetUser) => {
    setSendingHi(prev => ({ ...prev, [targetUser.user_id]: true }));
    try {
      // Open or create DM
      const dmName = `dm_${[currentUser?.user_id, targetUser.user_id].sort().join('_')}`;
      const res = await chatAPI.listRooms();
      const existingRooms = res.data?.rooms || res.data || [];
      let room = existingRooms.find(r => r.name === dmName);
      if (!room) {
        const created = await chatAPI.createRoom({ name: dmName, is_group: false, participant_ids: [targetUser.user_id] });
        room = created.data;
      }
      // Send "Hi" message
      await chatAPI.sendMessage({ room_id: room.id, body: 'Hi 👋', content: 'Hi 👋' });
      // Open the room
      setShowNewMessage(false);
      setNewMsgSearch('');
      fetchRooms();
      setActiveRoom(room);
    } catch (e) {
      Alert.alert('Error', 'Could not send message. Try again.');
    } finally {
      setSendingHi(prev => ({ ...prev, [targetUser.user_id]: false }));
    }
  }, [currentUser]);

  // ── Send message ──
  const handleSend = async () => {
    const text = message.trim();
    if (!text) return;

    const optimisticMsg = {
      id: 'temp_' + Date.now(),
      sender_id: currentUser?.id,
      sender_username: currentUser?.username || 'me',
      sender_name: currentUser?.display_name || currentUser?.username || 'Me',
      body: text,
      content: text,
      created_at: new Date().toISOString(),
      is_me: true,
      _pending: true,
    };

    setMessages(prev => [...prev, optimisticMsg]);
    setMessage('');
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 50);

    try {
      const res = await chatAPI.sendMessage({
        room_id: activeRoom.id,
        body: text,
        content: text,
      });
      // Replace optimistic message with server response
      const serverMsg = res.data?.message || res.data;
      if (serverMsg) {
        setMessages(prev => prev.map(m =>
          m.id === optimisticMsg.id ? { ...serverMsg, is_me: true } : m
        ));
      }
      // Also send over WS for real-time
      sendWsMessage({
        type: 'new_message',
        room_id: activeRoom.id,
        message: serverMsg || optimisticMsg,
      });
    } catch (e) {
      // Mark message as failed
      setMessages(prev => prev.map(m =>
        m.id === optimisticMsg.id ? { ...m, _failed: true, _pending: false } : m
      ));
    }

    // Update room list preview
    setRooms(prev => prev.map(r =>
      r.id === activeRoom.id
        ? { ...r, last_message: text, last_message_time: new Date().toISOString() }
        : r
    ));
  };

  // ── Handle typing ──
  const handleTextChange = (text) => {
    setMessage(text);
    sendTypingIndicator();
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {}, 2000);
  };

  // ── Filter rooms ──
  const filteredRooms = rooms.filter(r => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const name = (r.name || r.room_name || '').toLowerCase();
    const other = (r.other_user?.display_name || r.other_user?.username || '').toLowerCase();
    return name.includes(q) || other.includes(q);
  });

  // Sort rooms by last message time
  const sortedRooms = [...filteredRooms].sort((a, b) => {
    const timeA = new Date(a.last_message_time || a.updated_at || 0).getTime();
    const timeB = new Date(b.last_message_time || b.updated_at || 0).getTime();
    return timeB - timeA;
  });

  // ── Determine if message is from current user ──
  const isMyMessage = (msg) => {
    if (msg.is_me !== undefined) return msg.is_me;
    if (currentUser?.id && msg.sender_id) return msg.sender_id === currentUser.id;
    if (currentUser?.username && msg.sender_username) return msg.sender_username === currentUser.username;
    return false;
  };

  // ── Get room display info ──
  const getRoomDisplay = (room) => {
    const name = room.name || room.room_name ||
      room.other_user?.display_name || room.other_user?.username ||
      'Unknown';
    const isOnline = room.is_online ||
      (room.other_user?.id && onlineUsers.has(room.other_user.id)) ||
      false;
    const avatarUrl = room.avatar_url || room.other_user?.avatar_url || null;
    const lastMsg = room.last_message || room.last_message_body || '';
    const lastTime = room.last_message_time || room.updated_at || room.created_at || '';
    const unread = room.unread_count || 0;
    const isGroup = room.is_group || room.type === 'group' || false;
    return { name, isOnline, avatarUrl, lastMsg, lastTime, unread, isGroup };
  };

  // ════════════════════════════════════════════════════
  //  MESSAGE THREAD VIEW
  // ════════════════════════════════════════════════════
  if (activeRoom) {
    const room = getRoomDisplay(activeRoom);
    const typing = typingUsers[activeRoom.id];

    // Build messages with day separators
    const messagesWithSeparators = [];
    messages.forEach((msg, i) => {
      const msgTime = msg.created_at || msg.time;
      const prevTime = i > 0 ? (messages[i - 1].created_at || messages[i - 1].time) : null;
      if (isDifferentDay(prevTime, msgTime)) {
        messagesWithSeparators.push({ _type: 'day_separator', date: msgTime, id: 'sep_' + i });
      }
      messagesWithSeparators.push(msg);
    });

    const renderMessage = ({ item, index }) => {
      // Day separator
      if (item._type === 'day_separator') {
        return (
          <View style={s.daySeparator}>
            <View style={[s.daySeparatorLine, { backgroundColor: theme.border }]} />
            <Text style={[s.daySeparatorText, { color: theme.textMuted, backgroundColor: theme.background }]}>
              {formatDaySeparator(item.date)}
            </Text>
            <View style={[s.daySeparatorLine, { backgroundColor: theme.border }]} />
          </View>
        );
      }

      const mine = isMyMessage(item);
      const msgBody = item.body || item.content || '';
      const msgTime = formatMessageTime(item.created_at || item.time);
      const senderName = item.sender_name || item.sender_username || '';

      // Check if previous non-separator message is from same sender (for grouping)
      const prevMessages = messagesWithSeparators.slice(0, messagesWithSeparators.indexOf(item));
      const prevMsg = [...prevMessages].reverse().find(m => !m._type);
      const sameSenderAsPrev = prevMsg && isMyMessage(prevMsg) === mine &&
        (mine || (prevMsg.sender_id === item.sender_id));

      return (
        <View style={[
          s.messageRow,
          mine ? s.messageRowRight : s.messageRowLeft,
          sameSenderAsPrev && { marginTop: 2 },
        ]}>
          {/* Their avatar (only first in group) */}
          {!mine && (
            <View style={{ width: 32 }}>
              {!sameSenderAsPrev && (
                <Avatar
                  name={senderName}
                  id={item.sender_id}
                  size={28}
                  avatarUrl={item.sender_avatar}
                />
              )}
            </View>
          )}

          <View style={[
            s.bubble,
            mine ? s.bubbleMine : s.bubbleTheirs,
            mine
              ? (sameSenderAsPrev ? { borderTopRightRadius: 3 } : {})
              : (sameSenderAsPrev ? { borderTopLeftRadius: 3 } : {}),
          ]}>
            {/* Sender name for group chats, only first in group */}
            {!mine && activeRoom.is_group && !sameSenderAsPrev && (
              <Text style={[s.bubbleSender, { color: getAvatarColor(item.sender_id) }]}>
                {senderName}
              </Text>
            )}

            <Text style={[
              s.bubbleText,
              { color: mine ? '#2C1810' : '#2C1810' },
            ]}>
              {msgBody}
            </Text>

            <View style={s.bubbleMeta}>
              <Text style={[
                s.bubbleTime,
                { color: '#8A7860' },
              ]}>
                {msgTime}
              </Text>
              {mine && (
                <Ionicons
                  name={item._failed ? 'alert-circle' : item._pending ? 'time-outline' : 'checkmark-done'}
                  size={14}
                  color={item._failed ? theme.error : mine ? 'rgba(10,10,10,0.5)' : theme.textMuted}
                  style={{ marginLeft: 4 }}
                />
              )}
            </View>
          </View>
        </View>
      );
    };

    return (
      <KeyboardAvoidingView
        style={[s.container, { backgroundColor: theme.background }]}
        behavior="padding"
        keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}
      >
        <StatusBar barStyle="dark-content" />

        {/* ── Thread Header ── */}
        <View style={[s.threadHeader, { backgroundColor: theme.background, borderBottomColor: theme.border }]}>
          <TouchableOpacity
            onPress={() => { setActiveRoom(null); setMessages([]); }}
            style={s.backBtn}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="chevron-back" size={28} color={theme.primary} />
          </TouchableOpacity>

          <TouchableOpacity style={s.threadHeaderProfile} activeOpacity={0.7}>
            <Avatar
              name={room.name}
              id={activeRoom.id}
              size={38}
              online={room.isOnline}
              avatarUrl={room.avatarUrl}
            />
            <View style={s.threadHeaderInfo}>
              <Text style={[s.threadHeaderName, { color: theme.textPrimary }]} numberOfLines={1}>
                {room.name}
              </Text>
              {typing ? (
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Text style={[s.threadHeaderStatus, { color: theme.primary }]}>typing</Text>
                  <TypingDots color={theme.primary} />
                </View>
              ) : (
                <Text style={[s.threadHeaderStatus, { color: room.isOnline ? theme.success : theme.textMuted }]}>
                  {room.isOnline ? 'Online' : 'Offline'}
                </Text>
              )}
            </View>
          </TouchableOpacity>

          <View style={s.threadHeaderActions}>
            <TouchableOpacity style={s.headerIconBtn}>
              <Ionicons name="call-outline" size={22} color={theme.textSecondary} />
            </TouchableOpacity>
            <TouchableOpacity style={s.headerIconBtn}>
              <Ionicons name="videocam-outline" size={24} color={theme.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* ── Messages ── */}
        {messagesLoading ? (
          <View style={s.centered}>
            <ActivityIndicator size="large" color={theme.primary} />
          </View>
        ) : messages.length === 0 ? (
          <View style={s.centered}>
            <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '-2deg' }], marginBottom: 16 }}>
              <Ionicons name="chatbubble-ellipses-outline" size={36} color="#C8BFA8" />
            </View>
            <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>No messages yet</Text>
            <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20, paddingHorizontal: 30 }}>Break the ice! Send the first message and get the conversation going.</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
              <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
              <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            </View>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messagesWithSeparators}
            keyExtractor={(item, i) => item.id?.toString() || `msg_${i}`}
            renderItem={renderMessage}
            contentContainerStyle={s.messagesContainer}
            showsVerticalScrollIndicator={false}
            onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
            onLayout={() => flatListRef.current?.scrollToEnd({ animated: false })}
            keyboardDismissMode="interactive"
            keyboardShouldPersistTaps="handled"
          />
        )}

        {/* ── Typing indicator above input ── */}
        {typing && messages.length > 0 && (
          <View style={[s.typingBar, { borderTopColor: theme.border }]}>
            <TypingDots color={theme.textMuted} />
            <Text style={[s.typingBarText, { color: theme.textMuted }]}>
              {typing} is typing
            </Text>
          </View>
        )}

        {/* ── Input Bar ── */}
        <View style={[s.inputBar, { backgroundColor: theme.background, borderTopColor: theme.border }]}>
          <TouchableOpacity style={s.inputIconBtn}>
            <Ionicons name="add-circle" size={28} color={theme.primary} />
          </TouchableOpacity>

          <View style={[s.inputContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <TextInput
              style={[s.input, { color: theme.textPrimary }]}
              placeholder="Type a message..."
              placeholderTextColor={theme.textMuted}
              value={message}
              onChangeText={handleTextChange}
              multiline
              maxLength={5000}
            />
            <TouchableOpacity style={s.inputEmojiBtn}>
              <Ionicons name="happy-outline" size={22} color={theme.textMuted} />
            </TouchableOpacity>
          </View>

          {message.trim() ? (
            <TouchableOpacity onPress={handleSend} style={s.sendBtn}>
              <Ionicons name="arrow-up" size={20} color="#2C1810" />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={s.inputIconBtn}>
              <Ionicons name="mic" size={24} color={theme.textSecondary} />
            </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>
    );
  }

  // ════════════════════════════════════════════════════
  //  CONVERSATIONS LIST VIEW
  // ════════════════════════════════════════════════════
  const renderRoom = ({ item }) => {
    const room = getRoomDisplay(item);
    const typing = typingUsers[item.id];

    const isSelected = selectedRooms.has(item.id);

    return (
      <TouchableOpacity
        style={s.roomItem}
        onPress={() => editMode ? toggleRoomSelection(item.id) : setActiveRoom(item)}
        activeOpacity={0.6}
      >
        {editMode && (
          <View style={[s.selectCircle, isSelected && { backgroundColor: theme.primary, borderColor: theme.primary }]}>
            {isSelected && <Ionicons name="checkmark" size={16} color="#FFFFFF" />}
          </View>
        )}
        <Avatar
          name={room.name}
          id={item.id}
          size={54}
          online={room.isOnline}
          avatarUrl={room.avatarUrl}
        />

        <View style={s.roomInfo}>
          <View style={s.roomInfoTop}>
            <Text style={[s.roomName, { color: theme.textPrimary }]} numberOfLines={1}>
              {room.name}
            </Text>
            <Text style={[
              s.roomTime,
              { color: room.unread > 0 ? theme.primary : theme.textMuted },
            ]}>
              {formatTime(room.lastTime)}
            </Text>
          </View>
          <View style={s.roomInfoBottom}>
            {typing ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                <Text style={[s.roomTyping, { color: theme.primary }]}>typing</Text>
                <TypingDots color={theme.primary} />
              </View>
            ) : (
              <Text
                style={[
                  s.roomLastMsg,
                  {
                    color: room.unread > 0 ? theme.textPrimary : theme.textMuted,
                    fontWeight: room.unread > 0 ? '500' : '400',
                  },
                ]}
                numberOfLines={1}
              >
                {room.lastMsg || 'No messages yet'}
              </Text>
            )}
            {room.unread > 0 && (
              <View style={[s.unreadBadge, { backgroundColor: theme.primary }]}>
                <Text style={s.unreadBadgeText}>
                  {room.unread > 99 ? '99+' : room.unread}
                </Text>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <Animated.View style={[s.container, { backgroundColor: theme.background, opacity: fadeAnim }]}>
      <StatusBar barStyle="dark-content" />

      {/* ── Header ── */}
      <View style={[s.listHeader, { borderBottomColor: theme.border }]}>
        <View style={s.listHeaderLeft}>
          {editMode ? (
            <TouchableOpacity onPress={() => { setEditMode(false); setSelectedRooms(new Set()); }}>
              <Text style={[s.editDoneText, { color: theme.primary }]}>Done</Text>
            </TouchableOpacity>
          ) : (
            <>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={{ flexDirection: 'row', gap: 4 }}>
                  <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
                  <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
                  <View style={{ width: 5, height: 5, borderRadius: 2.5, borderWidth: 1.5, borderColor: '#C8BFA8' }} />
                </View>
                <Text style={[s.listHeaderTitle, { color: theme.textPrimary }]}>Messages</Text>
              </View>
              {wsConnected && <View style={s.connectedDot} />}
            </>
          )}
        </View>
        <View style={s.listHeaderRight}>
          {editMode ? (
            <TouchableOpacity
              style={[s.deleteSelectedBtn, selectedRooms.size === 0 && { opacity: 0.4 }]}
              onPress={deleteSelectedRooms}
              disabled={selectedRooms.size === 0}
            >
              <Ionicons name="trash-outline" size={22} color="#ED4956" />
            </TouchableOpacity>
          ) : (
            <>
              <TouchableOpacity style={s.headerIconBtn} onPress={() => setEditMode(true)}>
                <Ionicons name="create-outline" size={24} color={theme.textPrimary} />
              </TouchableOpacity>
              <TouchableOpacity style={s.headerIconBtn} onPress={() => { setShowNewMessage(true); fetchFollowList(); }}>
                <Ionicons name="add-circle-outline" size={26} color={theme.textPrimary} />
              </TouchableOpacity>
            </>
          )}
          {onClose && (
            <TouchableOpacity style={s.headerIconBtn} onPress={onClose}>
              <Ionicons name="close" size={24} color={theme.textPrimary} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* ── Search ── */}
      <View style={[s.searchBar, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Ionicons name="search" size={18} color={theme.textMuted} />
        <TextInput
          style={[s.searchInput, { color: theme.textPrimary }]}
          placeholder="Search conversations"
          placeholderTextColor={theme.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={18} color={theme.textMuted} />
          </TouchableOpacity>
        )}
      </View>

      {/* ── Online Now (horizontal scroll) ── */}
      {rooms.some(r => getRoomDisplay(r).isOnline) && (
        <View style={[s.onlineSection, { borderBottomColor: theme.border }]}>
          <FlatList
            horizontal
            data={rooms.filter(r => getRoomDisplay(r).isOnline)}
            keyExtractor={item => 'online_' + item.id}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={s.onlineScrollContent}
            renderItem={({ item }) => {
              const r = getRoomDisplay(item);
              return (
                <TouchableOpacity
                  style={s.onlineItem}
                  onPress={() => setActiveRoom(item)}
                >
                  <Avatar
                    name={r.name}
                    id={item.id}
                    size={56}
                    online
                    avatarUrl={r.avatarUrl}
                  />
                  <Text style={[s.onlineName, { color: theme.textSecondary }]} numberOfLines={1}>
                    {r.name.split(' ')[0]}
                  </Text>
                </TouchableOpacity>
              );
            }}
          />
        </View>
      )}

      {/* ── Room list ── */}
      {loading ? (
        <View style={s.centered}>
          <ActivityIndicator size="large" color={theme.primary} />
          <Text style={[s.loadingText, { color: theme.textMuted }]}>Loading conversations...</Text>
        </View>
      ) : sortedRooms.length === 0 ? (
        <View style={s.centered}>
          <View style={{ width: 80, height: 80, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '3deg' }], marginBottom: 16 }}>
            <Ionicons name={searchQuery ? 'search-outline' : 'chatbubbles-outline'} size={36} color="#C8BFA8" />
          </View>
          <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 16, marginBottom: 6 }}>
            {searchQuery ? 'No results found' : 'No conversations yet'}
          </Text>
          <Text style={{ color: '#8A7860', fontSize: 13, textAlign: 'center', lineHeight: 20, paddingHorizontal: 30 }}>
            {searchQuery
              ? 'Try a different search term'
              : 'Your inbox is a blank page! Start a conversation and fill it with ideas.'}
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 8 }}>
            <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
            <View style={{ width: 6, height: 6, borderWidth: 1, borderColor: '#C8BFA8', transform: [{ rotate: '45deg' }] }} />
            <View style={{ width: 20, height: 1.5, backgroundColor: '#C8BFA8' }} />
          </View>
          {!searchQuery && (
            <TouchableOpacity style={{ flexDirection: 'row', alignItems: 'center', marginTop: 20, backgroundColor: '#F9D84A', paddingHorizontal: 20, paddingVertical: 10, borderWidth: 1.5, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 12, borderBottomLeftRadius: 12, borderBottomRightRadius: 3 }} onPress={() => { setShowNewMessage(true); fetchFollowList(); }}>
              <Ionicons name="add" size={20} color="#2C1810" />
              <Text style={{ color: '#2C1810', fontWeight: '700', marginLeft: 6 }}>New Message</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        <FlatList
          data={sortedRooms}
          keyExtractor={item => item.id?.toString() || Math.random().toString()}
          renderItem={renderRoom}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}
      {/* ── New Message Modal ── */}
      <Modal visible={showNewMessage} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => { setShowNewMessage(false); setNewMsgSearch(''); }}>
        <View style={[s.newMsgContainer, { backgroundColor: theme.background }]}>
          {/* Header */}
          <View style={[s.newMsgHeader, { borderBottomColor: theme.border }]}>
            <TouchableOpacity onPress={() => { setShowNewMessage(false); setNewMsgSearch(''); }}>
              <Text style={{ color: theme.textSecondary, fontSize: 16 }}>Cancel</Text>
            </TouchableOpacity>
            <Text style={[s.newMsgTitle, { color: theme.textPrimary }]}>New Message</Text>
            <View style={{ width: 50 }} />
          </View>

          {/* Search */}
          <View style={[s.newMsgSearchBar, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Ionicons name="search" size={18} color={theme.textMuted} />
            <TextInput
              style={[s.newMsgSearchInput, { color: theme.textPrimary }]}
              placeholder="Search followers & following..."
              placeholderTextColor={theme.textMuted}
              value={newMsgSearch}
              onChangeText={setNewMsgSearch}
              autoFocus
            />
            {newMsgSearch.length > 0 && (
              <TouchableOpacity onPress={() => setNewMsgSearch('')}>
                <Ionicons name="close-circle" size={18} color={theme.textMuted} />
              </TouchableOpacity>
            )}
          </View>

          {/* List */}
          {followListLoading ? (
            <View style={s.centered}>
              <ActivityIndicator size="large" color={theme.primary} />
            </View>
          ) : (
            <FlatList
              data={followList.filter(u => {
                if (!newMsgSearch.trim()) return true;
                const q = newMsgSearch.toLowerCase();
                return (u.username || '').toLowerCase().includes(q) || (u.display_name || '').toLowerCase().includes(q);
              })}
              keyExtractor={item => item.user_id}
              renderItem={({ item }) => (
                <View style={s.newMsgRow}>
                  <Avatar name={item.display_name || item.username} id={item.user_id} size={48} avatarUrl={item.avatar_url} />
                  <View style={s.newMsgInfo}>
                    <Text style={[s.newMsgName, { color: theme.textPrimary }]} numberOfLines={1}>{item.display_name || item.username}</Text>
                    <Text style={[s.newMsgUsername, { color: theme.textMuted }]} numberOfLines={1}>@{item.username}</Text>
                  </View>
                  <TouchableOpacity
                    style={[s.newMsgSendBtn, { backgroundColor: theme.primary }]}
                    onPress={() => sendHiAndOpen(item)}
                    disabled={sendingHi[item.user_id]}
                  >
                    {sendingHi[item.user_id] ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <Ionicons name="chatbubble-outline" size={18} color="#FFFFFF" />
                    )}
                  </TouchableOpacity>
                </View>
              )}
              contentContainerStyle={{ paddingBottom: 40 }}
              ListEmptyComponent={
                <View style={s.centered}>
                  <View style={{ width: 70, height: 70, borderWidth: 2, borderColor: '#2C1810', borderTopLeftRadius: 3, borderTopRightRadius: 16, borderBottomLeftRadius: 16, borderBottomRightRadius: 3, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFCF2', transform: [{ rotate: '-1deg' }], marginBottom: 14 }}>
                    <Ionicons name="people-outline" size={32} color="#C8BFA8" />
                  </View>
                  <Text style={{ color: '#2C1810', fontWeight: '800', fontSize: 15, marginBottom: 4 }}>
                    {newMsgSearch ? 'No matches found' : 'No connections yet'}
                  </Text>
                  <Text style={{ color: '#8A7860', fontSize: 12, textAlign: 'center', lineHeight: 18 }}>
                    {newMsgSearch ? 'Try searching by username' : 'Follow some people to start chatting!'}
                  </Text>
                </View>
              }
            />
          )}
        </View>
      </Modal>
    </Animated.View>
  );
}

// ════════════════════════════════════════════════════
//  STYLES
// ════════════════════════════════════════════════════
const s = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FDF6E3',
  },

  // ── List Header ──
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 18,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 14 : 54,
    paddingBottom: 12,
  },
  listHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  listHeaderTitle: {
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    color: '#2C1810',
  },
  connectedDot: {
    width: 8,
    height: 8,
    borderRadius: 1,
    backgroundColor: '#27AE60',
    borderWidth: 1,
    borderColor: '#2C1810',
    marginTop: 2,
    transform: [{ rotate: '45deg' }],
  },
  listHeaderRight: {
    flexDirection: 'row',
    gap: 8,
  },
  headerIconBtn: {
    padding: 6,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 8,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 3,
    backgroundColor: '#FFFCF2',
  },

  // ── Search ──
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 10,
    marginBottom: 4,
    paddingHorizontal: 14,
    height: 40,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    backgroundColor: '#FFFCF2',
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#2C1810',
  },

  // ── Online Section ──
  onlineSection: {
    paddingVertical: 12,
  },
  onlineScrollContent: {
    paddingHorizontal: 16,
    gap: 16,
  },
  onlineItem: {
    alignItems: 'center',
    width: 64,
  },
  onlineName: {
    fontSize: 11,
    marginTop: 4,
    textAlign: 'center',
    color: '#5A4A30',
    fontWeight: '600',
  },

  // ── Room Item ──
  roomItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 12,
    marginVertical: 3,
    borderWidth: 1.5,
    borderColor: '#E6D5B8',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    backgroundColor: '#FFFCF2',
    gap: 12,
  },
  roomInfo: {
    flex: 1,
  },
  roomInfoTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 3,
  },
  roomName: {
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
    marginRight: 8,
    color: '#2C1810',
  },
  roomTime: {
    fontSize: 11,
    fontWeight: '600',
    color: '#8A7860',
  },
  roomInfoBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  roomLastMsg: {
    fontSize: 13,
    flex: 1,
    marginRight: 8,
    color: '#5A4A30',
  },
  roomTyping: {
    fontSize: 13,
    fontStyle: 'italic',
    marginRight: 4,
  },
  unreadBadge: {
    minWidth: 20,
    height: 20,
    borderRadius: 3,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 5,
    backgroundColor: '#FFD60A',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    transform: [{ rotate: '-3deg' }],
  },
  unreadBadgeText: {
    color: '#2C1810',
    fontSize: 11,
    fontWeight: '700',
  },

  // ── Thread Header ──
  threadHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 52,
    paddingBottom: 10,
    borderBottomWidth: 1.5,
    borderBottomColor: '#2C1810',
  },
  backBtn: {
    padding: 6,
    marginRight: 6,
  },
  threadHeaderProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 10,
  },
  threadHeaderInfo: {
    flex: 1,
  },
  threadHeaderName: {
    fontSize: 16,
    fontWeight: '700',
  },
  threadHeaderStatus: {
    fontSize: 12,
    marginRight: 4,
  },
  threadHeaderActions: {
    flexDirection: 'row',
    gap: 12,
    marginLeft: 8,
  },

  // ── Messages ──
  messagesContainer: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 8,
  },
  messageRow: {
    flexDirection: 'row',
    marginBottom: 4,
    paddingHorizontal: 4,
  },
  messageRowLeft: {
    justifyContent: 'flex-start',
    gap: 6,
  },
  messageRowRight: {
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '78%',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 12,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 3,
  },
  bubbleMine: {
    borderTopLeftRadius: 12,
    borderTopRightRadius: 3,
    borderBottomLeftRadius: 3,
    borderBottomRightRadius: 12,
    backgroundColor: '#FFD60A',
    borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  bubbleTheirs: {
    backgroundColor: '#FFFCF2',
    borderColor: '#C8BFA8',
  },
  bubbleSender: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 21,
  },
  bubbleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 3,
  },
  bubbleTime: {
    fontSize: 11,
  },

  // ── Day Separator ──
  daySeparator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 16,
    paddingHorizontal: 20,
  },
  daySeparatorLine: {
    flex: 1,
    height: 1.5,
    backgroundColor: '#C8BFA8',
  },
  daySeparatorText: {
    fontSize: 10,
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 3,
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    color: '#8A7860',
    backgroundColor: '#FFD60A',
    borderWidth: 1,
    borderColor: '#2C1810',
    borderRadius: 2,
    transform: [{ rotate: '-1deg' }],
    overflow: 'hidden',
  },

  // ── Typing Bar ──
  typingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 6,
    gap: 6,
    borderTopWidth: 0.5,
  },
  typingBarText: {
    fontSize: 13,
    fontStyle: 'italic',
  },

  // ── Input Bar ──
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 10,
    paddingVertical: 8,
    paddingBottom: Platform.OS === 'ios' ? 30 : 10,
    gap: 8,
    borderTopWidth: 1.5,
    borderTopColor: '#2C1810',
    backgroundColor: '#FDF6E3',
  },
  inputIconBtn: {
    padding: 4,
    marginBottom: 4,
  },
  inputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 16,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 3,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === 'ios' ? 8 : 4,
    minHeight: 42,
    maxHeight: 120,
    backgroundColor: '#FFFCF2',
  },
  input: {
    flex: 1,
    fontSize: 15,
    lineHeight: 20,
    paddingVertical: 0,
    maxHeight: 100,
  },
  inputEmojiBtn: {
    padding: 4,
    marginLeft: 4,
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 3,
    backgroundColor: '#FFD60A',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },

  // ── Empty / Loading ──
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingText: {
    fontSize: 14,
    marginTop: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 14,
    marginTop: 6,
    textAlign: 'center',
    lineHeight: 20,
  },
  emptyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    backgroundColor: '#FFD60A',
    marginTop: 24,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  emptyBtnText: {
    color: '#2C1810',
    fontSize: 15,
    fontWeight: '700',
  },

  // ── Edit mode ──
  editDoneText: {
    fontSize: 17,
    fontWeight: '600',
  },
  deleteSelectedBtn: {
    padding: 8,
  },
  selectCircle: {
    width: 22,
    height: 22,
    borderRadius: 3,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },

  // ── New Message Modal ──
  newMsgContainer: {
    flex: 1,
  },
  newMsgHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 54,
    paddingBottom: 14,
    borderBottomWidth: 0.5,
  },
  newMsgTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  newMsgSearchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
    paddingHorizontal: 14,
    height: 42,
    borderWidth: 1.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    gap: 8,
  },
  newMsgSearchInput: {
    flex: 1,
    fontSize: 15,
  },
  newMsgRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    gap: 14,
  },
  newMsgInfo: {
    flex: 1,
  },
  newMsgName: {
    fontSize: 15,
    fontWeight: '600',
  },
  newMsgUsername: {
    fontSize: 13,
    marginTop: 1,
  },
  newMsgSendBtn: {
    width: 42,
    height: 42,
    borderTopLeftRadius: 3,
    borderTopRightRadius: 10,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 3,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9D84A',
    borderWidth: 1.5,
    borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
});
