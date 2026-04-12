/**
 * ScrollUForward Design System — Notebook Couture (2026)
 * A premium hand-crafted notebook aesthetic: ruled pages, ink splashes,
 * watercolor washes, washi tape, stamps, doodles, and mixed-media collage.
 * Every screen feels like opening a beautiful, well-loved journal.
 */

import { Platform } from 'react-native';

export const SketchTheme = {
  id: 'sketch',

  // ─── Core Surfaces — warm paper tones ───
  background: '#FDF6E3',       // sun-bleached journal paper
  surface: '#FFFCF2',          // fresh cream page
  surfaceLight: '#F3EACD',     // aged kraft page
  card: '#FFFCF2',
  cardHover: '#FFF5DC',
  border: '#2C1810',           // rich dark ink
  borderLight: '#C4AA78',
  borderFaint: '#E6D5B8',

  // ─── Paper textures ───
  paper: '#FDF6E3',
  paperLight: '#FFFCF2',
  paperDark: '#E8DCBE',
  paperGrid: 'rgba(170,155,128,0.08)',
  paperRuled: 'rgba(90,150,210,0.18)',
  paperMargin: 'rgba(200,55,55,0.20)',
  paperCream: '#FFF8E7',
  paperVintage: '#F5E6C8',
  paperBlush: '#FFF0E8',

  // ─── Neubrutalist shadows — HARD, no blur, solid offset ───
  shadowColor: '#2C1810',
  cardShadow: {
    shadowColor: '#2C1810',
    shadowOffset: { width: 4, height: 5 },
    shadowOpacity: 1,
    shadowRadius: 0,
    elevation: 8,
  },
  smallShadow: {
    shadowColor: '#2C1810',
    shadowOffset: { width: 3, height: 3 },
    shadowOpacity: 1,
    shadowRadius: 0,
    elevation: 5,
  },
  softShadow: {
    shadowColor: '#2C1810',
    shadowOffset: { width: 2, height: 2 },
    shadowOpacity: 0.7,
    shadowRadius: 0,
    elevation: 3,
  },
  glowShadow: {
    shadowColor: '#FFD60A',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 4,
  },

  // ─── Text — rich ink ───
  textPrimary: '#2C1810',
  textSecondary: '#4A3520',
  textMuted: '#8A7558',
  textLink: '#2563EB',
  textPencil: '#6B5E48',
  textInk: '#1A0E08',

  // ─── Primary — golden amber ───
  primary: '#FFD60A',
  primaryDark: '#E6B800',
  primaryText: '#2C1810',
  primaryLight: '#FFF3B0',

  // ─── BOLD accent palette — notebook ink colors ───
  ink: '#2C1810',
  inkMid: '#4A3520',
  inkFaint: '#8A7558',
  blue: '#2563EB',
  yellow: '#FFD60A',
  green: '#059669',
  red: '#DC2626',
  purple: '#7C3AED',
  orange: '#EA580C',
  teal: '#0D9488',
  pink: '#DB2777',
  cyan: '#0891B2',
  indigo: '#4F46E5',

  // ─── Watercolor washes — soft transparent fills ───
  watercolorBlue: 'rgba(37,99,235,0.08)',
  watercolorPink: 'rgba(219,39,119,0.07)',
  watercolorGreen: 'rgba(5,150,105,0.07)',
  watercolorYellow: 'rgba(255,214,10,0.12)',
  watercolorPurple: 'rgba(124,58,237,0.07)',
  watercolorOrange: 'rgba(234,88,12,0.08)',
  watercolorTeal: 'rgba(13,148,136,0.07)',

  // ─── Neubrutalist accent combos ───
  electricYellow: '#FFD60A',
  hotCoral: '#FF6B6B',
  mintFresh: '#6EE7B7',
  lavenderPop: '#C4B5FD',
  skyPunch: '#7DD3FC',
  peachCrush: '#FDBA74',
  bubblegum: '#F9A8D4',
  limeZest: '#BEF264',
  roseGold: '#F4A6C1',
  sunsetGlow: '#FB923C',

  // ─── Highlight markers (thick, visible) ───
  highlightYellow: 'rgba(255,214,10,0.40)',
  highlightGreen: 'rgba(110,231,183,0.35)',
  highlightPink: 'rgba(249,168,212,0.35)',
  highlightBlue: 'rgba(125,211,252,0.35)',
  highlightOrange: 'rgba(253,186,116,0.30)',
  highlightPurple: 'rgba(196,181,253,0.30)',
  highlightCoral: 'rgba(255,107,107,0.25)',

  // ─── Tape colors (bolder, more variety) ───
  tapeBlue: 'rgba(100,180,255,0.50)',
  tapeYellow: 'rgba(255,214,10,0.55)',
  tapePurple: 'rgba(196,181,253,0.50)',
  tapeGreen: 'rgba(110,231,183,0.50)',
  tapePink: 'rgba(249,168,212,0.45)',
  tapeOrange: 'rgba(253,186,116,0.50)',
  tapeMint: 'rgba(167,243,208,0.50)',
  tapeLavender: 'rgba(221,214,254,0.55)',

  // ─── Status ───
  success: '#059669',
  error: '#DC2626',
  warning: '#EA580C',
  info: '#2563EB',

  // ─── Tab bar ───
  tabBarBg: '#FDF6E3',
  statusBarStyle: 'dark-content',

  // ─── Notebook radius patterns — playful asymmetry ───
  sketchRadius: {
    borderTopLeftRadius: 2,
    borderTopRightRadius: 18,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 2,
  },
  sketchRadiusSmall: {
    borderTopLeftRadius: 2,
    borderTopRightRadius: 12,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 2,
  },
  sketchRadiusInverse: {
    borderTopLeftRadius: 18,
    borderTopRightRadius: 2,
    borderBottomLeftRadius: 2,
    borderBottomRightRadius: 18,
  },
  pillRadius: {
    borderRadius: 50,
  },
  notebookRadius: {
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 12,
  },
};

export const DarkTheme = SketchTheme;
export const LightTheme = SketchTheme;

// ─── Domain colors — rich notebook ink palette ───
export const DOMAIN_COLORS = {
  physics: '#EA580C',
  nature: '#059669',
  ai: '#0D9488',
  history: '#7C3AED',
  technology: '#2563EB',
  space: '#4F46E5',
  biology: '#059669',
  mathematics: '#EA580C',
  philosophy: '#7C3AED',
  engineering: '#78716C',
  chemistry: '#0D9488',
  ancient_civilizations: '#9333EA',
  arts: '#DC2626',
};

export const DOMAIN_STAMP = {
  physics: { color: '#EA580C', label: 'PHYSICS', bg: '#FFF7ED', emoji: '~' },
  nature: { color: '#059669', label: 'NATURE', bg: '#ECFDF5', emoji: '~' },
  ai: { color: '#0D9488', label: 'A.I.', bg: '#F0FDFA', emoji: '>' },
  history: { color: '#7C3AED', label: 'HISTORY', bg: '#F5F3FF', emoji: '~' },
  technology: { color: '#2563EB', label: 'TECH', bg: '#EFF6FF', emoji: '>' },
  space: { color: '#4F46E5', label: 'SPACE', bg: '#EEF2FF', emoji: '*' },
  biology: { color: '#059669', label: 'BIO', bg: '#ECFDF5', emoji: '~' },
  mathematics: { color: '#EA580C', label: 'MATH', bg: '#FFF7ED', emoji: '#' },
  engineering: { color: '#78716C', label: 'ENG', bg: '#F5F5F4', emoji: '>' },
  ancient_civilizations: { color: '#9333EA', label: 'ANCIENT', bg: '#FAF5FF', emoji: '*' },
  arts: { color: '#DC2626', label: 'ARTS', bg: '#FEF2F2', emoji: '~' },
};

// ─── Typography — notebook handwriting meets bold display ───
export const Typography = {
  headerLarge: { fontSize: 32, fontWeight: '900', letterSpacing: -1.2 },
  headerMedium: { fontSize: 24, fontWeight: '900', letterSpacing: -0.5 },
  headerSmall: { fontSize: 18, fontWeight: '800', letterSpacing: -0.3 },
  bodyLarge: { fontSize: 16, fontWeight: '500', lineHeight: 26 },
  bodyMedium: { fontSize: 14, fontWeight: '500', lineHeight: 22 },
  bodySmall: { fontSize: 12, fontWeight: '500', lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: '800', letterSpacing: 2, textTransform: 'uppercase' },
  button: { fontSize: 14, fontWeight: '800', letterSpacing: 0.8 },
  handwritten: {
    fontSize: 15,
    fontWeight: '400',
    fontStyle: 'italic',
    letterSpacing: 0.5,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },
  mono: { fontSize: 12, fontWeight: '600', letterSpacing: 1 },
  journalTitle: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -0.8,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },
  journalBody: {
    fontSize: 15,
    fontWeight: '400',
    lineHeight: 28,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },
  stamp: { fontSize: 10, fontWeight: '900', letterSpacing: 2.5, textTransform: 'uppercase' },
  tapeLabel: { fontSize: 9, fontWeight: '800', letterSpacing: 1.5, textTransform: 'uppercase' },
};

// ─── Neubrutalist sketch card builder ───
export const sketchCard = (rotate = 0) => ({
  backgroundColor: '#FFFCF2',
  borderWidth: 2.5,
  borderColor: '#2C1810',
  borderTopLeftRadius: 2,
  borderTopRightRadius: 18,
  borderBottomLeftRadius: 18,
  borderBottomRightRadius: 2,
  ...Platform.select({
    ios: { shadowColor: '#2C1810', shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
    android: { elevation: 8 },
  }),
  transform: rotate ? [{ rotate: `${rotate}deg` }] : [],
});

// ─── Notebook line spacing ───
export const NOTEBOOK = {
  lineSpacing: 28,
  marginLeft: 42,
  marginColor: 'rgba(200,55,55,0.20)',
  ruleColor: 'rgba(90,150,210,0.18)',
  holeSize: 16,
  holeGap: 60,
  spiralColor: '#C4AA78',
};

export default SketchTheme;
