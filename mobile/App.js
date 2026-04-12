import React, { useState, useEffect, createContext, useContext } from 'react';
import { View, StyleSheet, StatusBar, TouchableOpacity, Text, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SplashScreen from './src/screens/SplashScreen';
import { NavigationContainer } from '@react-navigation/native';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

// Screens
import AuthScreen from './src/screens/AuthScreen';
import ReelsScreen from './src/screens/ReelsScreen';
import ArticlesScreen from './src/screens/ArticlesScreen';
import DiscussionsScreen from './src/screens/DiscussionsScreen';
import NewsScreen from './src/screens/NewsScreen';
import ExploreScreen from './src/screens/ExploreScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import ChatScreen from './src/screens/ChatScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';

// Theme
import { SketchTheme } from './src/theme';

// Auth + Theme Context
export const AuthContext = createContext(null);
export const ThemeContext = createContext(null);

const Tab = createMaterialTopTabNavigator();
const Stack = createNativeStackNavigator();

// ─── Tab config ───
const TABS = [
  { name: 'Home', icon: 'play-circle', iconOutline: 'play-circle-outline', color: '#FFD60A' },
  { name: 'Search', icon: 'search', iconOutline: 'search-outline', color: '#7DD3FC' },
  { name: 'Articles', icon: 'book', iconOutline: 'book-outline', color: '#6EE7B7' },
  { name: 'Discuss', icon: 'chatbubbles', iconOutline: 'chatbubbles-outline', color: '#C4B5FD' },
  { name: 'News', icon: 'newspaper', iconOutline: 'newspaper-outline', color: '#FDBA74' },
  { name: 'Profile', icon: 'person-circle', iconOutline: 'person-circle-outline', color: '#F9A8D4' },
];

function MainTabs() {
  const { theme } = useContext(ThemeContext);

  return (
    <Tab.Navigator
      tabBarPosition="bottom"
      screenOptions={{
        swipeEnabled: true,
        lazy: true,
        animationEnabled: true,
      }}
      tabBar={({ state, descriptors, navigation }) => (
        <View style={[tabStyles.bar, {
          backgroundColor: theme.tabBarBg,
          borderTopColor: theme.borderLight,
          paddingBottom: Platform.OS === 'ios' ? 22 : 8,
        }]}>
          {state.routes.map((route, index) => {
            const focused = state.index === index;
            const tab = TABS.find(t => t.name === route.name) || TABS[0];

            return (
              <TouchableOpacity
                key={route.key}
                activeOpacity={0.7}
                onPress={() => {
                  const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
                  if (!event.defaultPrevented) {
                    navigation.navigate(route.name);
                  }
                }}
                style={tabStyles.tabItem}
              >
                <View style={[
                  tabStyles.iconWrap,
                  focused && {
                    backgroundColor: tab.color,
                    borderColor: theme.ink,
                    borderWidth: 2,
                    ...Platform.select({
                      ios: { shadowColor: theme.ink, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
                      android: { elevation: 4 },
                    }),
                  },
                ]}>
                  <Ionicons
                    name={focused ? tab.icon : tab.iconOutline}
                    size={20}
                    color={focused ? theme.ink : theme.inkFaint}
                  />
                </View>
                <Text style={[
                  tabStyles.label,
                  { color: focused ? theme.ink : theme.inkFaint },
                  focused && tabStyles.labelActive,
                ]}>
                  {route.name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      )}
    >
      <Tab.Screen name="Home" component={ReelsScreen} />
      <Tab.Screen name="Search" component={ExploreScreen} />
      <Tab.Screen name="Articles" component={ArticlesScreen} />
      <Tab.Screen name="Discuss" component={DiscussionsScreen} />
      <Tab.Screen name="News" component={NewsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

const tabStyles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    borderTopWidth: 1.5,
    paddingTop: 8,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrap: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderWidth: 0,
    borderColor: 'transparent',
  },
  label: {
    fontSize: 9,
    fontWeight: '600',
    marginTop: 3,
    letterSpacing: 0.3,
  },
  labelActive: {
    fontWeight: '800',
  },
});

export default function App() {
  const [appReady, setAppReady] = useState(false);
  const [showSplash, setShowSplash] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [dmTarget, setDmTarget] = useState(null);
  const [isDarkTheme, setIsDarkTheme] = useState(false);

  const theme = SketchTheme;

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const stored = await AsyncStorage.getItem('scrollu_user');
        if (stored) {
          setUser(JSON.parse(stored));
          setIsAuthenticated(true);
        } else {
          const token = await AsyncStorage.getItem('auth_token');
          const userId = await AsyncStorage.getItem('user_id');
          const username = await AsyncStorage.getItem('username');
          if (token && userId) {
            const userData = { access_token: token, user_id: userId, username: username || '' };
            setUser(userData);
            setIsAuthenticated(true);
            await AsyncStorage.setItem('scrollu_user', JSON.stringify(userData));
          }
        }
      } catch (e) {
      } finally {
        setAppReady(true);
      }
    };
    restoreSession();
  }, []);

  const handleAuth = async (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    try {
      await AsyncStorage.setItem('scrollu_user', JSON.stringify(userData));
    } catch (e) {}
  };

  const handleLogout = async () => {
    setUser(null);
    setIsAuthenticated(false);
    try {
      await AsyncStorage.multiRemove(['scrollu_user', 'auth_token']);
    } catch (e) {}
  };

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  if (!appReady) return null;

  if (!isAuthenticated) {
    return (
      <ThemeContext.Provider value={{ theme, isDarkTheme, toggleTheme: () => setIsDarkTheme(p => !p) }}>
        <AuthScreen onAuth={handleAuth} />
      </ThemeContext.Provider>
    );
  }

  const authContextValue = {
    user,
    onLogout: handleLogout,
    openChat: () => { setDmTarget(null); setShowChat(true); },
    openDM: (targetUser) => { setDmTarget(targetUser); setShowChat(true); },
  };
  const themeContextValue = { theme, isDarkTheme, toggleTheme: () => setIsDarkTheme(prev => !prev) };

  return (
    <ThemeContext.Provider value={themeContextValue}>
      <AuthContext.Provider value={authContextValue}>
        <NavigationContainer>
          <StatusBar barStyle={theme.statusBarStyle} backgroundColor={theme.background} />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="MainTabs" component={MainTabs} />
            <Stack.Screen name="Notifications" component={NotificationsScreen} options={{ animation: 'slide_from_right' }} />
            <Stack.Screen name="UserProfile" component={ProfileScreen} options={{ animation: 'slide_from_right' }} />
          </Stack.Navigator>

          {showChat && (
            <View style={[styles.overlay, { backgroundColor: theme.background }]}>
              <ChatScreen dmTarget={dmTarget} onClose={() => { setShowChat(false); setDmTarget(null); }} />
            </View>
          )}
        </NavigationContainer>
      </AuthContext.Provider>
    </ThemeContext.Provider>
  );
}

const styles = StyleSheet.create({
  overlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 },
});
