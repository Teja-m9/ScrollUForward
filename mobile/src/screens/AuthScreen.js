import React, { useState, useRef, useEffect, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, StatusBar, ActivityIndicator,
  Dimensions, Alert, ScrollView, Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import { Typography } from '../theme';
import { ThemeContext } from '../../App';
import { authAPI } from '../api';

WebBrowser.maybeCompleteAuthSession();

const { width, height } = Dimensions.get('window');
const ACCENT = '#FFD60A';
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const PAPER_CREAM = '#FFFCF2';
const RULED = 'rgba(90,150,210,0.14)';
const MARGIN_RED = 'rgba(200,55,55,0.18)';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

export default function AuthScreen({ onAuth }) {
  const [screen, setScreen] = useState('welcome');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const coverSlide = useRef(new Animated.Value(0)).current;
  const stampScale = useRef(new Animated.Value(0)).current;
  const ribbonSlide = useRef(new Animated.Value(-80)).current;

  const { theme } = useContext(ThemeContext);

  const GOOGLE_CLIENT_ID = '1069161488243-5ncjgh87c10rvclqeg7vvai3sf81o1f7.apps.googleusercontent.com';

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      const redirectUri = 'https://scrolluforward-production.up.railway.app/auth/google/callback';
      const nonce = Date.now().toString(36) + Math.random().toString(36).slice(2);
      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${GOOGLE_CLIENT_ID}` +
        `&redirect_uri=${encodeURIComponent(redirectUri)}` +
        `&response_type=id_token` +
        `&scope=${encodeURIComponent('openid email profile')}` +
        `&nonce=${nonce}` +
        `&prompt=select_account`;

      const result = await WebBrowser.openAuthSessionAsync(authUrl, 'scrolluforward://');

      if (result.type === 'success' && result.url) {
        const idToken = result.url.match(/[?&#]id_token=([^&]+)/)?.[1] ||
                        result.url.match(/[?&]token=([^&]+)/)?.[1];
        const userId = result.url.match(/[?&]user_id=([^&]+)/)?.[1];
        const uname = result.url.match(/[?&]username=([^&]+)/)?.[1];
        const error = result.url.match(/[?&]error=([^&]+)/)?.[1];

        if (userId && uname) {
          const token = result.url.match(/[?&]token=([^&]+)/)?.[1];
          await AsyncStorage.setItem('auth_token', token);
          await AsyncStorage.setItem('user_id', userId);
          await AsyncStorage.setItem('username', decodeURIComponent(uname));
          onAuth({ access_token: token, user_id: userId, username: decodeURIComponent(uname) });
        } else if (idToken) {
          const response = await authAPI.google({ id_token: decodeURIComponent(idToken) });
          const userData = response.data;
          await AsyncStorage.setItem('auth_token', userData.access_token);
          await AsyncStorage.setItem('user_id', userData.user_id);
          await AsyncStorage.setItem('username', userData.username);
          onAuth(userData);
        } else if (error) {
          Alert.alert('Error', `Google: ${decodeURIComponent(error)}`);
        } else {
          Alert.alert('Error', 'Sign-in incomplete. Please try again.');
        }
      }
    } catch (e) {
      console.log('Google Sign-In error:', e);
      Alert.alert('Error', `Google Sign-In failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fadeAnim.setValue(0);
    slideAnim.setValue(30);
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, friction: 6, tension: 80, useNativeDriver: true }),
    ]).start();

    if (screen === 'welcome') {
      Animated.sequence([
        Animated.delay(400),
        Animated.spring(stampScale, { toValue: 1, friction: 4, tension: 120, useNativeDriver: true }),
        Animated.spring(ribbonSlide, { toValue: 0, friction: 5, tension: 60, useNativeDriver: true }),
      ]).start();
    }
  }, [screen]);

  const handleAuth = async () => {
    if (screen === 'login') {
      if (!email || !password) { Alert.alert('Error', 'Please fill in all fields'); return; }
    } else {
      if (!email || !password || !username) { Alert.alert('Error', 'Please fill in all required fields'); return; }
    }

    setLoading(true);
    try {
      let response;
      if (screen === 'login') {
        response = await authAPI.login({ email, password });
      } else {
        response = await authAPI.register({ email, password, username, display_name: displayName || username });
      }
      const userData = response.data;
      await AsyncStorage.setItem('auth_token', userData.access_token);
      await AsyncStorage.setItem('user_id', userData.user_id);
      await AsyncStorage.setItem('username', userData.username);
      setLoading(false);
      onAuth(userData);
    } catch (err) {
      setLoading(false);
      const errorMsg = err.response?.data?.detail || err.message || '';
      if (errorMsg.includes('Network') || errorMsg.includes('timeout') || !err.response) {
        const mockUser = {
          access_token: 'demo-token-' + Date.now(),
          user_id: 'user_' + Date.now(),
          username: username || email.split('@')[0],
        };
        await AsyncStorage.setItem('auth_token', mockUser.access_token);
        await AsyncStorage.setItem('user_id', mockUser.user_id);
        await AsyncStorage.setItem('username', mockUser.username);
        onAuth(mockUser);
      } else {
        Alert.alert('Error', errorMsg || 'Authentication failed');
      }
    }
  };

  // ─── RULED PAPER BACKGROUND ───
  const RuledBackground = () => (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {Array.from({ length: 35 }, (_, i) => (
        <View key={i} style={{ position: 'absolute', left: 0, right: 0, top: i * 28, height: 1, backgroundColor: RULED }} />
      ))}
      <View style={{ position: 'absolute', left: 42, top: 0, bottom: 0, width: 1.5, backgroundColor: MARGIN_RED }} />
      {/* Hole punches */}
      {[0.18, 0.5, 0.82].map((p, i) => (
        <View key={`h-${i}`} style={{
          position: 'absolute', left: 12, top: `${p * 100}%`,
          width: 16, height: 16, borderRadius: 8,
          backgroundColor: '#E6D5B8', borderWidth: 1.5, borderColor: '#C4AA78',
        }} />
      ))}
    </View>
  );

  // ─── WELCOME SCREEN ───
  if (screen === 'welcome') {
    return (
      <View style={[s.container, { backgroundColor: PAPER }]}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <RuledBackground />

        {/* Bookmark ribbon */}
        <Animated.View style={[s.bookmarkRibbon, { transform: [{ translateY: ribbonSlide }] }]}>
          <View style={s.ribbonBody} />
          <View style={{ flexDirection: 'row' }}>
            <View style={s.ribbonVLeft} />
            <View style={s.ribbonVRight} />
          </View>
        </Animated.View>

        {/* Washi tape decoration */}
        <View style={s.washiTapeTop}>
          <View style={s.washiTapeStrip} />
        </View>

        <Animated.View style={[s.welcomeContent, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
          {/* Notebook ring holes header */}
          <View style={s.ringHolesRow}>
            {[0,1,2,3,4].map(i => (
              <View key={i} style={s.ringHole}>
                <View style={s.ringHoleInner} />
              </View>
            ))}
          </View>

          {/* Logo — hand-drawn style */}
          <View style={s.logoNotebook}>
            <View style={s.logoCircle}>
              <Ionicons name="school" size={40} color={ACCENT} />
            </View>
            {/* Scribble underline */}
            <View style={s.scribbleUnder}>
              <View style={[s.scribbleLine, { width: 60 }]} />
              <View style={[s.scribbleLine, { width: 40, opacity: 0.4, marginTop: 2 }]} />
            </View>
          </View>

          {/* App name — like it's written in the notebook */}
          <Text style={s.appNameWelcome}>
            Scroll<Text style={{ color: ACCENT }}>U</Text>Forward
          </Text>
          <View style={s.markerHighlight}>
            <Text style={s.taglineWelcome}>Where Curiosity Scales</Text>
          </View>

          {/* Hand-written style description */}
          <Text style={s.handwrittenDesc}>
            Open your journal. Feed your mind.{'\n'}Every scroll is a step forward.
          </Text>

          {/* Rubber stamp decoration */}
          <Animated.View style={[s.rubberStamp, { transform: [{ scale: stampScale }, { rotate: '-6deg' }] }]}>
            <Text style={s.rubberStampText}>WELCOME</Text>
            <View style={s.rubberStampLine} />
            <Text style={s.rubberStampSmall}>EXPLORER</Text>
          </Animated.View>

          {/* Dots — like notebook bullet points */}
          <View style={s.dotsRow}>
            <View style={s.dot} />
            <View style={s.dotActive} />
            <View style={s.dot} />
          </View>
        </Animated.View>

        {/* Bottom Buttons — sticker style */}
        <View style={s.welcomeBottom}>
          <TouchableOpacity style={s.loginBtn} onPress={() => setScreen('login')}>
            <Text style={s.loginBtnText}>Log in</Text>
          </TouchableOpacity>

          <TouchableOpacity style={s.signupBtn} onPress={() => setScreen('signup')}>
            <Text style={s.signupBtnText}>Sign up</Text>
          </TouchableOpacity>
        </View>

        {/* Tape label at bottom */}
        <View style={s.tapeLabel}>
          <Text style={s.tapeLabelText}>YOUR JOURNEY STARTS HERE</Text>
        </View>
      </View>
    );
  }

  // ─── LOGIN / SIGNUP FORM ───
  return (
    <KeyboardAvoidingView
      style={[s.container, { backgroundColor: PAPER }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
      <RuledBackground />

      <ScrollView
        contentContainerStyle={s.formScroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Back button — sketchy circle */}
        <TouchableOpacity style={s.backBtn} onPress={() => setScreen('welcome')}>
          <View style={s.backBtnCircle}>
            <Ionicons name="arrow-back" size={20} color={INK} />
          </View>
        </TouchableOpacity>

        {/* Header with notebook decoration */}
        <Animated.View style={[s.formHeader, { opacity: fadeAnim }]}>
          {/* Ring holes */}
          <View style={[s.ringHolesRow, { marginBottom: 14 }]}>
            {[0,1,2].map(i => (
              <View key={i} style={s.ringHole}>
                <View style={s.ringHoleInner} />
              </View>
            ))}
          </View>

          <Text style={s.formGreeting}>Hi ! Welcome to</Text>
          <View style={{ position: 'relative', alignSelf: 'flex-start' }}>
            <View style={s.titleHighlight} />
            <Text style={s.formAppName}>
              Scroll<Text style={{ color: ACCENT }}>U</Text>Forward
            </Text>
          </View>

          {/* Marker underline */}
          <View style={s.markerUnderline}>
            <View style={[s.markerStroke, { width: 50, backgroundColor: ACCENT }]} />
            <View style={[s.markerStroke, { width: 30, backgroundColor: INK, opacity: 0.1, marginLeft: 4 }]} />
          </View>
        </Animated.View>

        {/* Form Fields — notebook input style */}
        <View style={s.formFields}>
          {screen === 'signup' && (
            <>
              <View style={s.fieldGroup}>
                <Text style={s.fieldLabel}>Username</Text>
                <View style={s.inputWrap}>
                  <Ionicons name="person-outline" size={16} color="#8A7558" style={s.inputIcon} />
                  <TextInput
                    style={s.input}
                    placeholder="your_username"
                    placeholderTextColor="#C4AA78"
                    value={username}
                    onChangeText={setUsername}
                    autoCapitalize="none"
                  />
                  <View style={s.inputUnderline} />
                </View>
              </View>

              <View style={s.fieldGroup}>
                <Text style={s.fieldLabel}>Display Name</Text>
                <View style={s.inputWrap}>
                  <Ionicons name="person-circle-outline" size={16} color="#8A7558" style={s.inputIcon} />
                  <TextInput
                    style={s.input}
                    placeholder="Display Name"
                    placeholderTextColor="#C4AA78"
                    value={displayName}
                    onChangeText={setDisplayName}
                  />
                  <View style={s.inputUnderline} />
                </View>
              </View>
            </>
          )}

          <View style={s.fieldGroup}>
            <Text style={s.fieldLabel}>Email</Text>
            <View style={s.inputWrap}>
              <Ionicons name="mail-outline" size={16} color="#8A7558" style={s.inputIcon} />
              <TextInput
                style={s.input}
                placeholder="you@email.com"
                placeholderTextColor="#C4AA78"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              <View style={s.inputUnderline} />
            </View>
          </View>

          <View style={s.fieldGroup}>
            <Text style={s.fieldLabel}>Password</Text>
            <View style={s.inputWrap}>
              <Ionicons name="lock-closed-outline" size={16} color="#8A7558" style={s.inputIcon} />
              <TextInput
                style={s.input}
                placeholder="password"
                placeholderTextColor="#C4AA78"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={s.eyeBtn}>
                <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={16} color="#8A7558" />
              </TouchableOpacity>
              <View style={s.inputUnderline} />
            </View>
          </View>

          {/* Auth Button — brutalist sticker style */}
          <TouchableOpacity style={s.authBtn} onPress={handleAuth} disabled={loading}>
            {loading ? (
              <ActivityIndicator color={INK} />
            ) : (
              <Text style={s.authBtnText}>
                {screen === 'login' ? 'Log In' : 'Sign Up'}
              </Text>
            )}
          </TouchableOpacity>

          {/* Divider — notebook style */}
          <View style={s.dividerWrap}>
            <View style={s.dividerDash} />
            <View style={s.dividerStamp}>
              <Text style={s.dividerText}>Or</Text>
            </View>
            <View style={s.dividerDash} />
          </View>

          {/* Google — postcard style button */}
          <TouchableOpacity style={s.googleBtn} onPress={handleGoogleSignIn} disabled={loading}>
            <Text style={s.googleG}>G</Text>
            <Text style={s.googleText}>Continue with Google</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Bottom Toggle — tape label */}
      <View style={s.bottomBar}>
        <Text style={s.bottomText}>
          {screen === 'login' ? "Don't Have an Account? " : "Already have an account? "}
        </Text>
        <TouchableOpacity onPress={() => setScreen(screen === 'login' ? 'signup' : 'login')}>
          <Text style={s.bottomLink}>
            {screen === 'login' ? 'Signup' : 'Login'}
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },

  // ─── Bookmark ribbon ───
  bookmarkRibbon: { position: 'absolute', right: 32, top: -4, zIndex: 10 },
  ribbonBody: { width: 20, height: 55, backgroundColor: '#DC2626' },
  ribbonVLeft: {
    width: 0, height: 0,
    borderLeftWidth: 10, borderBottomWidth: 8,
    borderLeftColor: '#DC2626', borderBottomColor: 'transparent',
  },
  ribbonVRight: {
    width: 0, height: 0,
    borderRightWidth: 10, borderBottomWidth: 8,
    borderRightColor: '#DC2626', borderBottomColor: 'transparent',
  },

  // ─── Washi tape ───
  washiTapeTop: {
    position: 'absolute', top: 40, left: width * 0.05,
    zIndex: 6, transform: [{ rotate: '-4deg' }],
  },
  washiTapeStrip: {
    width: 80, height: 18,
    backgroundColor: 'rgba(255,214,10,0.45)',
    borderRadius: 1,
  },

  // ─── Welcome content ───
  welcomeContent: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    paddingHorizontal: 36, paddingLeft: 56,
  },

  ringHolesRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  ringHole: {
    width: 12, height: 12, borderRadius: 6,
    backgroundColor: '#E6D5B8', borderWidth: 1.5, borderColor: '#C4AA78',
    justifyContent: 'center', alignItems: 'center',
  },
  ringHoleInner: {
    width: 5, height: 5, borderRadius: 2.5,
    backgroundColor: PAPER, borderWidth: 1, borderColor: '#C4AA78',
  },

  logoNotebook: { alignItems: 'center', marginBottom: 20 },
  logoCircle: {
    width: 90, height: 90, borderRadius: 45,
    backgroundColor: 'rgba(255,214,10,0.12)',
    borderWidth: 2.5, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },
  scribbleUnder: { marginTop: 8, alignItems: 'center' },
  scribbleLine: {
    height: 2.5, backgroundColor: ACCENT, borderRadius: 2,
  },

  appNameWelcome: {
    fontSize: 30, fontWeight: '900', color: INK,
    letterSpacing: -1, marginBottom: 8,
  },
  markerHighlight: {
    backgroundColor: 'rgba(255,214,10,0.30)',
    paddingHorizontal: 12, paddingVertical: 4,
    borderRadius: 2, transform: [{ rotate: '-1deg' }],
    marginBottom: 16,
  },
  taglineWelcome: {
    fontSize: 15, fontWeight: '700', color: '#4A3520',
    letterSpacing: 2, textTransform: 'uppercase',
  },

  handwrittenDesc: {
    fontSize: 14, color: '#8A7558', textAlign: 'center',
    lineHeight: 22, fontStyle: 'italic', letterSpacing: 0.3,
    marginBottom: 20,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },

  rubberStamp: {
    borderWidth: 3, borderColor: '#DC2626', borderRadius: 4,
    paddingHorizontal: 18, paddingVertical: 8,
    opacity: 0.55, marginBottom: 24,
  },
  rubberStampText: {
    fontSize: 14, fontWeight: '900', color: '#DC2626',
    letterSpacing: 5, textAlign: 'center',
  },
  rubberStampLine: {
    height: 1.5, backgroundColor: '#DC2626', marginVertical: 4, opacity: 0.4,
  },
  rubberStampSmall: {
    fontSize: 8, fontWeight: '800', color: '#DC2626',
    letterSpacing: 3, textAlign: 'center',
  },

  dotsRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#C4AA78' },
  dotActive: {
    width: 26, height: 8, borderRadius: 4, backgroundColor: ACCENT,
    borderWidth: 1.5, borderColor: INK,
  },

  // ─── Bottom buttons ───
  welcomeBottom: {
    flexDirection: 'row', paddingHorizontal: 24, paddingBottom: 16, gap: 12,
  },
  loginBtn: {
    flex: 1, height: 52,
    borderWidth: 2.5, borderColor: INK,
    borderTopLeftRadius: 2, borderTopRightRadius: 14,
    borderBottomLeftRadius: 14, borderBottomRightRadius: 2,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: PAPER_CREAM,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  loginBtnText: { fontSize: 16, fontWeight: '800', color: INK, letterSpacing: 0.5 },
  signupBtn: {
    flex: 1, height: 52,
    borderWidth: 2.5, borderColor: INK,
    borderTopLeftRadius: 14, borderTopRightRadius: 2,
    borderBottomLeftRadius: 2, borderBottomRightRadius: 14,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: ACCENT,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  signupBtnText: { fontSize: 16, fontWeight: '800', color: INK, letterSpacing: 0.5 },

  tapeLabel: {
    backgroundColor: 'rgba(255,214,10,0.45)',
    paddingVertical: 8, marginHorizontal: 60, marginBottom: 28,
    borderRadius: 1, transform: [{ rotate: '-1deg' }],
  },
  tapeLabelText: {
    fontSize: 9, fontWeight: '800', color: '#4A3520',
    letterSpacing: 2, textAlign: 'center', textTransform: 'uppercase',
  },

  // ─── Form screen ───
  formScroll: {
    flexGrow: 1, paddingHorizontal: 28, paddingTop: 50, paddingLeft: 56,
  },
  backBtn: { marginBottom: 12 },
  backBtnCircle: {
    width: 38, height: 38, borderRadius: 19,
    borderWidth: 2, borderColor: INK,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: PAPER_CREAM,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },

  formHeader: { marginBottom: 28 },
  formGreeting: {
    fontSize: 22, fontWeight: '400', color: '#8A7558',
    fontStyle: 'italic', marginBottom: 4,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },
  titleHighlight: {
    position: 'absolute', left: -4, right: -4,
    bottom: 0, height: '40%',
    backgroundColor: 'rgba(255,214,10,0.30)',
    borderRadius: 2, transform: [{ rotate: '-0.5deg' }],
  },
  formAppName: { fontSize: 28, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  markerUnderline: { flexDirection: 'row', marginTop: 8, alignItems: 'center' },
  markerStroke: { height: 4, borderRadius: 2 },

  // ─── Form fields ───
  formFields: {},
  fieldGroup: { marginBottom: 18 },
  fieldLabel: {
    fontSize: 11, fontWeight: '800', color: '#8A7558',
    letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 6,
  },
  inputWrap: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(255,252,242,0.7)',
    paddingHorizontal: 0, paddingVertical: 2,
    position: 'relative',
  },
  inputIcon: { marginRight: 10, width: 20 },
  input: {
    flex: 1, fontSize: 15, color: INK, paddingVertical: 10,
    fontWeight: '500',
  },
  inputUnderline: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    height: 2, backgroundColor: '#C4AA78',
    borderRadius: 1,
  },
  eyeBtn: { padding: 8 },

  // ─── Auth button ───
  authBtn: {
    height: 52, marginTop: 24,
    backgroundColor: ACCENT,
    borderWidth: 2.5, borderColor: INK,
    borderTopLeftRadius: 2, borderTopRightRadius: 16,
    borderBottomLeftRadius: 16, borderBottomRightRadius: 2,
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },
  authBtnText: { color: INK, fontWeight: '900', fontSize: 16, letterSpacing: 1 },

  // ─── Divider ───
  dividerWrap: { flexDirection: 'row', alignItems: 'center', marginVertical: 22 },
  dividerDash: { flex: 1, height: 1.5, backgroundColor: '#E6D5B8' },
  dividerStamp: {
    borderWidth: 1.5, borderColor: '#C4AA78', borderRadius: 2,
    paddingHorizontal: 12, paddingVertical: 3, marginHorizontal: 12,
    transform: [{ rotate: '-2deg' }],
  },
  dividerText: { fontSize: 11, fontWeight: '800', color: '#8A7558', letterSpacing: 1 },

  // ─── Google button ───
  googleBtn: {
    flexDirection: 'row', height: 50,
    borderWidth: 2, borderColor: '#C4AA78',
    borderTopLeftRadius: 2, borderTopRightRadius: 12,
    borderBottomLeftRadius: 12, borderBottomRightRadius: 2,
    justifyContent: 'center', alignItems: 'center',
    backgroundColor: PAPER_CREAM, gap: 10,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.5, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  googleG: { fontSize: 20, fontWeight: '700', color: '#EA4335' },
  googleText: { fontSize: 14, fontWeight: '700', color: INK },

  // ─── Bottom ───
  bottomBar: {
    flexDirection: 'row', justifyContent: 'center',
    paddingVertical: 16, borderTopWidth: 2, borderTopColor: '#E6D5B8',
    backgroundColor: 'rgba(253,246,227,0.95)',
  },
  bottomText: { fontSize: 13, color: '#8A7558' },
  bottomLink: {
    fontSize: 13, fontWeight: '900', color: ACCENT,
    textDecorationLine: 'underline', textDecorationColor: INK,
  },
});
