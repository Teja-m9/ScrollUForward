/**
 * Notebook Couture Components — 2026
 * Premium hand-crafted notebook UI kit. Every component feels like it was
 * lovingly placed into a real journal: washi tape, watercolor washes,
 * ink stamps, spiral bindings, polaroid frames, bookmark ribbons, and doodles.
 */
import React from 'react';
import { View, Text, StyleSheet, Platform, Dimensions } from 'react-native';
import { DOMAIN_COLORS, DOMAIN_STAMP } from '../theme';

const { width: SW } = Dimensions.get('window');

// ─── Washi Tape — semi-transparent patterned tape strips ───
export function Tape({ color = 'yellow', style, width = 65, rotate = -3 }) {
  const colors = {
    blue: 'rgba(100,180,255,0.55)',
    yellow: 'rgba(255,214,10,0.60)',
    purple: 'rgba(196,181,253,0.55)',
    green: 'rgba(110,231,183,0.55)',
    red: 'rgba(239,68,68,0.40)',
    pink: 'rgba(249,168,212,0.50)',
    orange: 'rgba(253,186,116,0.55)',
    mint: 'rgba(167,243,208,0.55)',
    lavender: 'rgba(221,214,254,0.55)',
  };
  const bg = colors[color] || colors.yellow;
  return (
    <View style={[styles.tape, { backgroundColor: bg, width, transform: [{ rotate: `${rotate}deg` }] }, style]}>
      <View style={[styles.tapeStripe, { left: '15%' }]} />
      <View style={[styles.tapeStripe, { left: '40%', opacity: 0.12 }]} />
      <View style={[styles.tapeStripe, { left: '65%' }]} />
      <View style={[styles.tapeStripe, { left: '85%', opacity: 0.10 }]} />
      <View style={styles.tapeTornLeft} />
      <View style={styles.tapeTornRight} />
    </View>
  );
}

// ─── Neubrutalist Stamp — bold bordered badge ───
export function Stamp({ domain, label, style, color: customColor, size = 'normal' }) {
  const domainInfo = DOMAIN_STAMP[domain] || {};
  const color = customColor || domainInfo.color || '#78716C';
  const bg = domainInfo.bg || '#F5F5F4';
  const displayLabel = label || domainInfo.label || domain?.toUpperCase() || '';
  const isSmall = size === 'small';
  return (
    <View style={[
      styles.stamp,
      {
        borderColor: color,
        backgroundColor: bg,
        paddingHorizontal: isSmall ? 7 : 10,
        paddingVertical: isSmall ? 2 : 4,
      },
      style,
    ]}>
      <Text style={[styles.stampText, { color, fontSize: isSmall ? 8 : 10 }]}>
        {displayLabel}
      </Text>
    </View>
  );
}

// ─── Neubrutalist Card — thick border, hard shadow ───
export function SketchCard({ children, style, rotate = 0, color }) {
  return (
    <View style={[
      styles.card,
      color && { backgroundColor: color },
      rotate !== 0 && { transform: [{ rotate: `${rotate}deg` }] },
      style,
    ]}>
      {children}
    </View>
  );
}

// ─── Avatar with bold border ───
export function SketchAvatar({ letter, size = 28, bgColor = '#059669', textColor = '#fff', style }) {
  return (
    <View style={[styles.avatar, {
      width: size, height: size,
      borderRadius: size * 0.5,
      backgroundColor: bgColor,
    }, style]}>
      <Text style={[styles.avatarText, { fontSize: size * 0.40, color: textColor }]}>
        {letter || '?'}
      </Text>
    </View>
  );
}

// ─── Doodle Divider — hand-drawn squiggly line ───
export function DoodleDivider({ style, color = '#C4AA78' }) {
  return (
    <View style={[styles.doodleDivider, style]}>
      <View style={[styles.doodleDash, { backgroundColor: color, width: 12 }]} />
      <View style={[styles.doodleDot, { backgroundColor: color }]} />
      <View style={[styles.doodleDash, { backgroundColor: color, width: 20, opacity: 0.5 }]} />
      <View style={[styles.doodleStar, { borderColor: color }]} />
      <View style={[styles.doodleDash, { backgroundColor: color, width: 20, opacity: 0.5 }]} />
      <View style={[styles.doodleDot, { backgroundColor: color }]} />
      <View style={[styles.doodleDash, { backgroundColor: color, width: 12 }]} />
    </View>
  );
}

// ─── Section Header — bold with marker underline ───
export function SketchSectionHeader({ title, style, color = '#2C1810', markerColor = '#FFD60A' }) {
  return (
    <View style={[styles.sectionHeader, style]}>
      <Text style={[styles.sectionHeaderText, { color }]}>{title}</Text>
      <View style={styles.sectionUnderline}>
        <View style={[styles.markerLine, { backgroundColor: markerColor }]} />
        <View style={[styles.markerLineThin, { backgroundColor: color, opacity: 0.15 }]} />
      </View>
    </View>
  );
}

// ─── Paper Corner Fold ───
export function PaperCorner({ style, size = 22 }) {
  return (
    <View style={[styles.paperCorner, { width: size, height: size }, style]}>
      <View style={[styles.paperCornerFold, { width: size * 1.4, height: size * 1.4 }]} />
    </View>
  );
}

// ─── Sticky Note — bold colored note ───
export function StickyNote({ children, color = '#FFD60A', rotate = -1.5, style }) {
  return (
    <View style={[styles.stickyNote, { backgroundColor: color, transform: [{ rotate: `${rotate}deg` }] }, style]}>
      <View style={[styles.stickyNoteGlue, { backgroundColor: color }]} />
      {children}
    </View>
  );
}

// ─── Notebook Margin Line ───
export function NotebookMargin({ style }) {
  return <View style={[styles.notebookMargin, style]} />;
}

// ─── Notebook Page — ruled lines + margin + holes ───
export function NotebookPage({ children, showRuledLines = true, showMargin = true, showHoles = false, lineSpacing = 28, style }) {
  const lines = showRuledLines ? Array.from({ length: 40 }, (_, i) => i) : [];
  const holes = showHoles ? Array.from({ length: 12 }, (_, i) => i) : [];
  return (
    <View style={[styles.notebookPage, style]}>
      {lines.map(i => (
        <View key={`rule-${i}`} style={{
          position: 'absolute', left: 0, right: 0,
          top: 60 + i * lineSpacing,
          height: 1,
          backgroundColor: 'rgba(90,150,210,0.14)',
        }} />
      ))}
      {showMargin && <View style={styles.notebookMarginLine} />}
      {holes.map(i => (
        <View key={`hole-${i}`} style={{
          position: 'absolute', left: 8, top: 50 + i * 80,
          width: 16, height: 16, borderRadius: 8,
          backgroundColor: '#E8DCBE',
          borderWidth: 1.5, borderColor: '#C4AA78',
        }} />
      ))}
      {children}
    </View>
  );
}

// ─── Scribble Highlight — marker stroke behind text ───
export function ScribbleHighlight({ children, color = 'rgba(255,214,10,0.40)', style }) {
  return (
    <View style={[styles.scribbleWrap, style]}>
      <View style={[styles.scribbleBg, { backgroundColor: color }]} />
      {children}
    </View>
  );
}

// ─── Torn Edge ───
export function TornEdge({ position = 'bottom', color = '#FDF6E3', style }) {
  const teeth = Array.from({ length: 22 }, (_, i) => i);
  return (
    <View style={[styles.tornEdge, position === 'top' ? { top: -8 } : { bottom: -8 }, style]}>
      {teeth.map(i => (
        <View key={`tooth-${i}`} style={{
          width: SW / 20,
          height: 10 + (i % 3) * 4,
          backgroundColor: color,
          borderRadius: i % 2 === 0 ? 5 : 1,
          marginHorizontal: -0.5,
        }} />
      ))}
    </View>
  );
}

// ─── Ink Blot ───
export function InkBlot({ size = 10, color = '#2C1810', opacity = 0.06, style }) {
  return (
    <View style={[{
      width: size, height: size,
      borderRadius: size / 2,
      backgroundColor: color, opacity,
    }, style]} />
  );
}

// ─── Pencil Line — sketchy divider ───
export function PencilLine({ style, color = '#C4AA78' }) {
  return (
    <View style={[styles.pencilLine, style]}>
      <View style={{ backgroundColor: color, width: '25%', height: 2, borderRadius: 1 }} />
      <View style={{ backgroundColor: color, width: '40%', height: 1.5, opacity: 0.5, borderRadius: 1 }} />
      <View style={{ backgroundColor: color, width: '20%', height: 2, opacity: 0.3, borderRadius: 1 }} />
    </View>
  );
}

// ─── Sticker Badge — bold circular sticker ───
export function StickerBadge({ label, color = '#FFD60A', textColor = '#2C1810', size = 48, rotate = -8, style }) {
  return (
    <View style={[{
      width: size, height: size, borderRadius: size / 2,
      backgroundColor: color,
      justifyContent: 'center', alignItems: 'center',
      borderWidth: 2.5, borderColor: '#2C1810',
      transform: [{ rotate: `${rotate}deg` }],
      ...Platform.select({
        ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
        android: { elevation: 5 },
      }),
    }, style]}>
      <Text style={{ fontSize: size * 0.22, fontWeight: '900', color: textColor, textAlign: 'center' }}>{label}</Text>
    </View>
  );
}

// ─── Page Header — notebook header with ring holes + marker ───
export function PageHeader({ title, subtitle, style, markerColor = '#FFD60A' }) {
  return (
    <View style={[styles.pageHeader, style]}>
      <View style={styles.pageHeaderDeco}>
        {[0,1,2].map(i => (
          <View key={i} style={styles.ringHole}>
            <View style={styles.ringHoleInner} />
          </View>
        ))}
      </View>
      <View style={{ position: 'relative', alignSelf: 'flex-start' }}>
        <View style={[styles.titleMarker, { backgroundColor: markerColor }]} />
        <Text style={styles.pageHeaderTitle}>{title}</Text>
      </View>
      {subtitle && <Text style={styles.pageHeaderSubtitle}>{subtitle}</Text>}
      <View style={styles.pageHeaderLine}>
        <View style={{ height: 3.5, backgroundColor: '#2C1810', width: 35, borderRadius: 2 }} />
        <View style={{ height: 2, backgroundColor: markerColor, width: 55, marginLeft: 4, borderRadius: 2 }} />
        <View style={{ height: 1.5, backgroundColor: '#E6D5B8', flex: 1, marginLeft: 4 }} />
      </View>
    </View>
  );
}

// ─── Spiral Binding ───
export function SpiralBinding({ count = 8, style }) {
  return (
    <View style={[styles.spiralBinding, style]}>
      {Array.from({ length: count }, (_, i) => (
        <View key={i} style={styles.spiralHole}>
          <View style={styles.spiralRing} />
        </View>
      ))}
    </View>
  );
}

// ─── Clipboard Clip — bold binder clip ───
export function ClipboardClip({ style, color = '#2C1810' }) {
  return (
    <View style={[styles.clipWrap, style]}>
      <View style={[styles.clipTop, { backgroundColor: color }]} />
      <View style={[styles.clipBody, { borderColor: color }]} />
    </View>
  );
}

// ─── Coffee Stain Ring ───
export function CoffeeStain({ size = 50, style }) {
  return (
    <View style={[{
      width: size, height: size,
      borderRadius: size / 2,
      borderWidth: size * 0.08,
      borderColor: 'rgba(160,120,60,0.08)',
      transform: [{ rotate: '15deg' }],
    }, style]} />
  );
}

// ─── Masking Tape Label — rectangular tape with text ───
export function MaskingTapeLabel({ text, color = 'rgba(255,214,10,0.60)', textColor = '#2C1810', style, rotate = -2 }) {
  return (
    <View style={[styles.maskingTape, { backgroundColor: color, transform: [{ rotate: `${rotate}deg` }] }, style]}>
      <Text style={[styles.maskingTapeText, { color: textColor }]}>{text}</Text>
    </View>
  );
}

// ─── Push Pin — decorative pin on cards ───
export function PushPin({ color = '#DC2626', style }) {
  return (
    <View style={[styles.pushPinWrap, style]}>
      <View style={[styles.pushPinHead, { backgroundColor: color }]}>
        <View style={styles.pushPinShine} />
      </View>
      <View style={styles.pushPinNeedle} />
    </View>
  );
}

// ─── Marker Underline — thick wavy marker stroke ───
export function MarkerUnderline({ color = '#FFD60A', width = 80, style }) {
  return (
    <View style={[{ width, height: 8, position: 'relative' }, style]}>
      <View style={{
        position: 'absolute', left: 0, right: 0,
        height: 6, backgroundColor: color,
        borderRadius: 3,
        transform: [{ rotate: '-0.8deg' }],
      }} />
      <View style={{
        position: 'absolute', left: 4, right: 8,
        top: 2, height: 4, backgroundColor: color,
        borderRadius: 2, opacity: 0.6,
        transform: [{ rotate: '0.5deg' }],
      }} />
    </View>
  );
}

// ─── Postage Stamp Frame — perforated edge stamp ───
export function PostageStamp({ children, color = '#FFFCF2', borderColor = '#2C1810', style }) {
  return (
    <View style={[styles.postageOuter, { borderColor }, style]}>
      <View style={[styles.postageInner, { backgroundColor: color }]}>
        {children}
      </View>
      {Array.from({ length: 8 }, (_, i) => (
        <View key={`pt-${i}`} style={[styles.perforation, { top: -3, left: 8 + i * 12 }]} />
      ))}
      {Array.from({ length: 8 }, (_, i) => (
        <View key={`pb-${i}`} style={[styles.perforation, { bottom: -3, left: 8 + i * 12 }]} />
      ))}
      {Array.from({ length: 6 }, (_, i) => (
        <View key={`pl-${i}`} style={[styles.perforation, { left: -3, top: 8 + i * 12 }]} />
      ))}
      {Array.from({ length: 6 }, (_, i) => (
        <View key={`pr-${i}`} style={[styles.perforation, { right: -3, top: 8 + i * 12 }]} />
      ))}
    </View>
  );
}

// ─── Brutalist Button — thick border, hard shadow ───
export function BrutalistButton({ label, color = '#FFD60A', textColor = '#2C1810', onPress, style, icon }) {
  const Touchable = require('react-native').TouchableOpacity;
  return (
    <Touchable onPress={onPress} activeOpacity={0.8} style={[styles.brutalistBtn, { backgroundColor: color }, style]}>
      {icon && <View style={{ marginRight: 6 }}>{icon}</View>}
      <Text style={[styles.brutalistBtnText, { color: textColor }]}>{label}</Text>
    </Touchable>
  );
}

// ─── Zigzag Border — decorative zigzag line ───
export function ZigzagBorder({ color = '#2C1810', style }) {
  return (
    <View style={[styles.zigzagRow, style]}>
      {Array.from({ length: 30 }, (_, i) => (
        <View key={i} style={[styles.zigzagTooth, {
          backgroundColor: 'transparent',
          borderBottomColor: color,
          borderBottomWidth: 2,
          borderLeftWidth: i % 2 === 0 ? 0 : 6,
          borderRightWidth: i % 2 === 0 ? 6 : 0,
          borderLeftColor: 'transparent',
          borderRightColor: 'transparent',
        }]} />
      ))}
    </View>
  );
}

// ─── Sketch Tag — hashtag-style label ───
export function SketchTag({ text, color = '#EFF6FF', borderColor = '#2563EB', textColor = '#2563EB', style }) {
  return (
    <View style={[styles.sketchTag, { backgroundColor: color, borderColor }, style]}>
      <Text style={[styles.sketchTagText, { color: textColor }]}>#{text}</Text>
    </View>
  );
}

// ══════════════════════════════════════════════════════════
// ─── NEW CREATIVE COMPONENTS ─────────────────────────────
// ══════════════════════════════════════════════════════════

// ─── Bookmark Ribbon — fabric ribbon hanging from top ───
export function BookmarkRibbon({ color = '#DC2626', width: ribbonWidth = 24, height: ribbonHeight = 60, style }) {
  return (
    <View style={[{
      width: ribbonWidth, height: ribbonHeight,
      position: 'absolute', right: 20, top: -4, zIndex: 10,
    }, style]}>
      <View style={{
        width: ribbonWidth, height: ribbonHeight - 12,
        backgroundColor: color,
        borderBottomLeftRadius: 0,
        borderBottomRightRadius: 0,
      }} />
      {/* V-cut at bottom */}
      <View style={{ flexDirection: 'row' }}>
        <View style={{
          width: 0, height: 0,
          borderLeftWidth: ribbonWidth / 2,
          borderRightWidth: 0,
          borderBottomWidth: 12,
          borderLeftColor: color,
          borderRightColor: 'transparent',
          borderBottomColor: 'transparent',
        }} />
        <View style={{
          width: 0, height: 0,
          borderLeftWidth: 0,
          borderRightWidth: ribbonWidth / 2,
          borderBottomWidth: 12,
          borderLeftColor: 'transparent',
          borderRightColor: color,
          borderBottomColor: 'transparent',
        }} />
      </View>
      {/* Subtle shadow stripe */}
      <View style={{
        position: 'absolute', right: 0, top: 0, bottom: 12,
        width: 4, backgroundColor: 'rgba(0,0,0,0.1)',
      }} />
    </View>
  );
}

// ─── Watercolor Splash — soft watercolor background blob ───
export function WatercolorSplash({ color = 'rgba(37,99,235,0.06)', size = 120, style }) {
  return (
    <View style={[{
      width: size, height: size * 0.8,
      borderRadius: size / 2,
      backgroundColor: color,
      transform: [{ rotate: '-15deg' }, { scaleX: 1.3 }],
    }, style]}>
      <View style={{
        position: 'absolute', top: '10%', left: '10%',
        width: '80%', height: '80%',
        borderRadius: size / 2,
        backgroundColor: color,
        opacity: 0.6,
        transform: [{ rotate: '30deg' }],
      }} />
      <View style={{
        position: 'absolute', top: '20%', right: '5%',
        width: '40%', height: '50%',
        borderRadius: size / 3,
        backgroundColor: color,
        opacity: 0.4,
      }} />
    </View>
  );
}

// ─── Polaroid Frame — photo with polaroid-style white border ───
export function PolaroidFrame({ children, caption, rotate = -2, style }) {
  return (
    <View style={[styles.polaroid, { transform: [{ rotate: `${rotate}deg` }] }, style]}>
      <View style={styles.polaroidPhoto}>
        {children}
      </View>
      {caption && (
        <Text style={styles.polaroidCaption}>{caption}</Text>
      )}
    </View>
  );
}

// ─── Notebook Tab Divider — colored tab on the edge ───
export function NotebookTabDivider({ label, color = '#FFD60A', active = false, style }) {
  return (
    <View style={[styles.notebookTab, {
      backgroundColor: active ? color : '#F3EACD',
      borderColor: active ? '#2C1810' : '#C4AA78',
      borderWidth: active ? 2.5 : 1.5,
    }, style]}>
      <Text style={[styles.notebookTabText, {
        color: active ? '#2C1810' : '#8A7558',
        fontWeight: active ? '900' : '700',
      }]}>{label}</Text>
      {active && <View style={[styles.notebookTabDot, { backgroundColor: '#2C1810' }]} />}
    </View>
  );
}

// ─── Ink Wash Banner — watercolor-style section banner ───
export function InkWashBanner({ children, color = 'rgba(255,214,10,0.15)', style }) {
  return (
    <View style={[styles.inkWashBanner, { backgroundColor: color }, style]}>
      {/* Left edge bleed */}
      <View style={[styles.inkWashEdge, { left: -8, backgroundColor: color, opacity: 0.5 }]} />
      {/* Right edge bleed */}
      <View style={[styles.inkWashEdge, { right: -8, backgroundColor: color, opacity: 0.3 }]} />
      {children}
    </View>
  );
}

// ─── Paper Clip — realistic paper clip decoration ───
export function PaperClip({ color = '#C4AA78', style }) {
  return (
    <View style={[styles.paperClipWrap, style]}>
      <View style={[styles.paperClipOuter, { borderColor: color }]} />
      <View style={[styles.paperClipInner, { borderColor: color }]} />
    </View>
  );
}

// ─── Hand-Drawn Circle — emphasis circle around content ───
export function HandDrawnCircle({ size = 60, color = '#DC2626', strokeWidth = 2, style }) {
  return (
    <View style={[{
      width: size, height: size,
      borderRadius: size / 2,
      borderWidth: strokeWidth,
      borderColor: color,
      borderStyle: 'solid',
      opacity: 0.5,
      transform: [{ rotate: '5deg' }, { scaleX: 1.1 }],
    }, style]} />
  );
}

// ─── Doodle Star — hand-drawn star decoration ───
export function DoodleStar({ size = 20, color = '#FFD60A', style }) {
  return (
    <View style={[{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }, style]}>
      <View style={{
        width: size * 0.9, height: size * 0.3,
        backgroundColor: color,
        borderRadius: 2,
        transform: [{ rotate: '0deg' }],
        position: 'absolute',
      }} />
      <View style={{
        width: size * 0.9, height: size * 0.3,
        backgroundColor: color,
        borderRadius: 2,
        transform: [{ rotate: '60deg' }],
        position: 'absolute',
      }} />
      <View style={{
        width: size * 0.9, height: size * 0.3,
        backgroundColor: color,
        borderRadius: 2,
        transform: [{ rotate: '120deg' }],
        position: 'absolute',
      }} />
    </View>
  );
}

// ─── Page Number — notebook-style page number ───
export function PageNumber({ number, style }) {
  return (
    <View style={[styles.pageNumber, style]}>
      <View style={styles.pageNumberLine} />
      <Text style={styles.pageNumberText}>{number}</Text>
      <View style={styles.pageNumberLine} />
    </View>
  );
}

// ─── Washi Tape Strip — long decorative tape with pattern ───
export function WashiTapeStrip({ color = 'rgba(255,214,10,0.50)', pattern = 'dots', width: stripWidth, style }) {
  const finalWidth = stripWidth || SW - 40;
  return (
    <View style={[styles.washiStrip, { backgroundColor: color, width: finalWidth }, style]}>
      {pattern === 'dots' && Array.from({ length: Math.floor(finalWidth / 14) }, (_, i) => (
        <View key={i} style={[styles.washiDot, { left: 7 + i * 14 }]} />
      ))}
      {pattern === 'stripes' && Array.from({ length: Math.floor(finalWidth / 10) }, (_, i) => (
        <View key={i} style={[styles.washiStripeLine, { left: i * 10 }]} />
      ))}
      {pattern === 'zigzag' && Array.from({ length: Math.floor(finalWidth / 8) }, (_, i) => (
        <View key={i} style={{
          position: 'absolute',
          left: i * 8, top: i % 2 === 0 ? 2 : 8,
          width: 6, height: 6, borderRadius: 3,
          backgroundColor: 'rgba(255,255,255,0.3)',
        }} />
      ))}
    </View>
  );
}

// ─── Ruled Paper Background — standalone ruled paper effect ───
export function RuledPaperBg({ lineSpacing = 28, marginLeft = 42, style }) {
  const lineCount = 45;
  return (
    <View style={[StyleSheet.absoluteFill, style]} pointerEvents="none">
      {/* Ruled lines */}
      {Array.from({ length: lineCount }, (_, i) => (
        <View key={`line-${i}`} style={{
          position: 'absolute', left: 0, right: 0,
          top: i * lineSpacing,
          height: 1,
          backgroundColor: 'rgba(90,150,210,0.12)',
        }} />
      ))}
      {/* Margin line */}
      <View style={{
        position: 'absolute', left: marginLeft, top: 0, bottom: 0,
        width: 1.5, backgroundColor: 'rgba(200,55,55,0.16)',
      }} />
    </View>
  );
}

// ─── Sketch Underline — hand-drawn underline effect ───
export function SketchUnderline({ width: lineWidth = 100, color = '#2C1810', style }) {
  return (
    <View style={[{ width: lineWidth, height: 6 }, style]}>
      <View style={{
        position: 'absolute', left: 2, right: 6,
        bottom: 0, height: 3,
        backgroundColor: color, opacity: 0.15,
        borderRadius: 2,
        transform: [{ rotate: '-0.5deg' }],
      }} />
      <View style={{
        position: 'absolute', left: 0, right: 10,
        bottom: 2, height: 2.5,
        backgroundColor: color, opacity: 0.25,
        borderRadius: 2,
        transform: [{ rotate: '0.3deg' }],
      }} />
    </View>
  );
}

// ─── Journal Date Stamp — date shown like a rubber stamp ───
export function JournalDateStamp({ date, color = '#8A7558', style }) {
  return (
    <View style={[styles.dateStamp, { borderColor: color }, style]}>
      <Text style={[styles.dateStampText, { color }]}>{date}</Text>
      <View style={[styles.dateStampLine, { backgroundColor: color }]} />
    </View>
  );
}


const styles = StyleSheet.create({
  // ─── Tape ───
  tape: {
    position: 'absolute', top: -9, alignSelf: 'center',
    height: 22, zIndex: 5, borderRadius: 1,
    opacity: 0.92, overflow: 'hidden',
  },
  tapeStripe: {
    position: 'absolute', top: 0, bottom: 0,
    width: 3, backgroundColor: 'rgba(255,255,255,0.25)',
  },
  tapeTornLeft: {
    position: 'absolute', left: -2, top: 2, bottom: 2,
    width: 4, backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 2,
  },
  tapeTornRight: {
    position: 'absolute', right: -2, top: 2, bottom: 2,
    width: 4, backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 2,
  },

  // ─── Stamp ───
  stamp: {
    alignSelf: 'flex-start',
    borderWidth: 2.5,
    borderRadius: 2,
    borderStyle: 'solid',
    transform: [{ rotate: '-2deg' }],
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 1, height: 1 }, shadowOpacity: 0.3, shadowRadius: 0 },
      android: { elevation: 2 },
    }),
  },
  stampText: {
    fontWeight: '900',
    letterSpacing: 2,
    textTransform: 'uppercase',
  },

  // ─── Card ───
  card: {
    backgroundColor: '#FFFCF2',
    borderWidth: 2.5,
    borderColor: '#2C1810',
    borderTopLeftRadius: 2,
    borderTopRightRadius: 18,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 2,
    overflow: 'hidden',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 8 },
    }),
  },

  // ─── Avatar ───
  avatar: {
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 2.5, borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 1, height: 2 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  avatarText: { fontWeight: '800' },

  // ─── Doodle divider ───
  doodleDivider: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', paddingVertical: 10, gap: 6,
  },
  doodleDash: { height: 2.5, borderRadius: 1 },
  doodleDot: { width: 5, height: 5, borderRadius: 2.5 },
  doodleStar: {
    width: 10, height: 10,
    borderWidth: 2, borderRadius: 1,
    transform: [{ rotate: '45deg' }],
  },

  // ─── Section header ───
  sectionHeader: { paddingHorizontal: 20, marginTop: 18, marginBottom: 14 },
  sectionHeaderText: { fontSize: 14, fontWeight: '900', letterSpacing: 2.5, textTransform: 'uppercase' },
  sectionUnderline: { marginTop: 5, gap: 3 },
  markerLine: { height: 5, width: 45, borderRadius: 2.5 },
  markerLineThin: { height: 1.5, width: 75 },

  // ─── Paper corner ───
  paperCorner: { position: 'absolute', bottom: 0, right: 0, overflow: 'hidden' },
  paperCornerFold: {
    position: 'absolute', bottom: 0, right: 0,
    backgroundColor: '#E6D5B8',
    transform: [{ rotate: '45deg' }, { translateX: 10 }, { translateY: 10 }],
    borderWidth: 1, borderColor: '#C4AA78',
  },

  // ─── Sticky note ───
  stickyNote: {
    padding: 16,
    borderTopLeftRadius: 1, borderTopRightRadius: 1,
    borderBottomLeftRadius: 2, borderBottomRightRadius: 12,
    borderWidth: 2, borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  stickyNoteGlue: {
    position: 'absolute', top: 0, left: '20%', right: '20%',
    height: 4, opacity: 0.3, borderBottomLeftRadius: 2, borderBottomRightRadius: 2,
  },

  // ─── Notebook ───
  notebookMargin: {
    position: 'absolute', left: 38, top: 0, bottom: 0,
    width: 2, backgroundColor: 'rgba(200,55,55,0.16)', zIndex: 1,
  },
  notebookPage: { flex: 1, backgroundColor: '#FDF6E3', overflow: 'hidden' },
  notebookMarginLine: {
    position: 'absolute', left: 42, top: 0, bottom: 0,
    width: 1.5, backgroundColor: 'rgba(200,55,55,0.16)', zIndex: 1,
  },

  // ─── Scribble highlight ───
  scribbleWrap: { position: 'relative' },
  scribbleBg: {
    position: 'absolute', left: -6, right: -6,
    top: '20%', bottom: -2,
    borderRadius: 3,
    transform: [{ rotate: '-0.7deg' }],
  },

  // ─── Torn edge ───
  tornEdge: {
    position: 'absolute', left: 0, right: 0,
    flexDirection: 'row', zIndex: 10, overflow: 'hidden',
  },

  // ─── Pencil line ───
  pencilLine: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 12, gap: 4,
  },

  // ─── Page header ───
  pageHeader: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 14 },
  pageHeaderDeco: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  ringHole: {
    width: 14, height: 14, borderRadius: 7,
    backgroundColor: '#E6D5B8', borderWidth: 2,
    borderColor: '#C4AA78', justifyContent: 'center', alignItems: 'center',
  },
  ringHoleInner: {
    width: 6, height: 6, borderRadius: 3,
    backgroundColor: '#FDF6E3', borderWidth: 1, borderColor: '#C4AA78',
  },
  titleMarker: {
    position: 'absolute', left: -4, right: -4,
    bottom: 0, height: '45%',
    borderRadius: 3,
    transform: [{ rotate: '-0.5deg' }],
  },
  pageHeaderTitle: { fontSize: 28, fontWeight: '900', color: '#2C1810', letterSpacing: -1 },
  pageHeaderSubtitle: { fontSize: 12, color: '#8A7558', fontStyle: 'italic', marginTop: 4, letterSpacing: 0.3 },
  pageHeaderLine: { flexDirection: 'row', alignItems: 'center', marginTop: 10 },

  // ─── Spiral binding ───
  spiralBinding: {
    position: 'absolute', left: 10, top: 60, bottom: 20,
    width: 22, justifyContent: 'space-evenly', zIndex: 5,
  },
  spiralHole: {
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: '#E6D5B8', borderWidth: 2,
    borderColor: '#C4AA78', justifyContent: 'center', alignItems: 'center',
  },
  spiralRing: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: '#FDF6E3', borderWidth: 1.5, borderColor: '#C4AA78',
  },

  // ─── Clipboard clip ───
  clipWrap: {
    position: 'absolute', top: -14, alignSelf: 'center',
    alignItems: 'center', zIndex: 10,
  },
  clipTop: {
    width: 40, height: 16,
    borderTopLeftRadius: 5, borderTopRightRadius: 5,
    borderWidth: 1.5, borderColor: '#333',
  },
  clipBody: {
    width: 30, height: 20,
    backgroundColor: 'transparent',
    borderBottomLeftRadius: 4, borderBottomRightRadius: 4,
    borderWidth: 2, borderTopWidth: 0, marginTop: -1,
  },

  // ─── Masking tape label ───
  maskingTape: {
    paddingHorizontal: 14, paddingVertical: 6,
    borderRadius: 1,
  },
  maskingTapeText: {
    fontSize: 10, fontWeight: '800',
    letterSpacing: 1.5, textTransform: 'uppercase',
  },

  // ─── Push pin ───
  pushPinWrap: { alignItems: 'center', zIndex: 10 },
  pushPinHead: {
    width: 16, height: 16, borderRadius: 8,
    borderWidth: 1.5, borderColor: '#2C1810',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 1, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  pushPinShine: {
    position: 'absolute', top: 3, left: 4,
    width: 4, height: 4, borderRadius: 2,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  pushPinNeedle: {
    width: 2, height: 8,
    backgroundColor: '#666', borderRadius: 1, marginTop: -2,
  },

  // ─── Postage stamp ───
  postageOuter: {
    borderWidth: 2.5, borderRadius: 2,
    padding: 6, overflow: 'visible',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 2, height: 3 }, shadowOpacity: 0.5, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  postageInner: { padding: 4 },
  perforation: {
    position: 'absolute', width: 6, height: 6,
    borderRadius: 3, backgroundColor: '#FDF6E3',
  },

  // ─── Brutalist button ───
  brutalistBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 20, paddingVertical: 13,
    borderWidth: 2.5, borderColor: '#2C1810',
    borderRadius: 4,
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  brutalistBtnText: { fontSize: 14, fontWeight: '900', letterSpacing: 0.8 },

  // ─── Zigzag border ───
  zigzagRow: { flexDirection: 'row', overflow: 'hidden', height: 8 },
  zigzagTooth: { width: 0, height: 0, borderStyle: 'solid' },

  // ─── Sketch tag ───
  sketchTag: {
    paddingHorizontal: 10, paddingVertical: 4,
    borderWidth: 2, borderRadius: 3,
    alignSelf: 'flex-start',
    transform: [{ rotate: '-1deg' }],
  },
  sketchTagText: { fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },

  // ─── Polaroid ───
  polaroid: {
    backgroundColor: '#fff',
    padding: 8, paddingBottom: 28,
    borderWidth: 1.5, borderColor: '#E6D5B8',
    ...Platform.select({
      ios: { shadowColor: '#2C1810', shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.4, shadowRadius: 2 },
      android: { elevation: 6 },
    }),
  },
  polaroidPhoto: {
    overflow: 'hidden',
    backgroundColor: '#F3EACD',
  },
  polaroidCaption: {
    position: 'absolute', bottom: 6, left: 10, right: 10,
    fontSize: 11, fontWeight: '400', fontStyle: 'italic',
    color: '#8A7558', textAlign: 'center',
    ...(Platform.OS === 'ios' ? { fontFamily: 'Georgia' } : {}),
  },

  // ─── Notebook tab ───
  notebookTab: {
    paddingHorizontal: 14, paddingVertical: 8,
    borderTopLeftRadius: 10, borderTopRightRadius: 10,
    borderBottomLeftRadius: 0, borderBottomRightRadius: 0,
    alignItems: 'center', justifyContent: 'center',
    minWidth: 55,
  },
  notebookTabText: {
    fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase',
  },
  notebookTabDot: {
    width: 4, height: 4, borderRadius: 2,
    marginTop: 3,
  },

  // ─── Ink wash banner ───
  inkWashBanner: {
    paddingVertical: 12, paddingHorizontal: 16,
    marginHorizontal: -4,
    borderRadius: 2,
    overflow: 'visible',
  },
  inkWashEdge: {
    position: 'absolute', top: 0, bottom: 0,
    width: 12, borderRadius: 6,
  },

  // ─── Paper clip ───
  paperClipWrap: {
    width: 20, height: 50,
    position: 'absolute', top: -10, right: 16, zIndex: 10,
  },
  paperClipOuter: {
    width: 16, height: 40,
    borderWidth: 2, borderRadius: 8,
    position: 'absolute', top: 0, left: 2,
  },
  paperClipInner: {
    width: 10, height: 28,
    borderWidth: 2, borderRadius: 5,
    position: 'absolute', top: 6, left: 5,
    backgroundColor: '#FFFCF2',
  },

  // ─── Page number ───
  pageNumber: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', paddingVertical: 16, gap: 10,
  },
  pageNumberLine: {
    height: 1, width: 30,
    backgroundColor: '#C4AA78',
  },
  pageNumberText: {
    fontSize: 11, fontWeight: '700', color: '#8A7558',
    letterSpacing: 2,
  },

  // ─── Washi tape strip ───
  washiStrip: {
    height: 16, borderRadius: 1,
    overflow: 'hidden', opacity: 0.85,
  },
  washiDot: {
    position: 'absolute', top: 5,
    width: 5, height: 5, borderRadius: 2.5,
    backgroundColor: 'rgba(255,255,255,0.35)',
  },
  washiStripeLine: {
    position: 'absolute', top: 0, bottom: 0,
    width: 2, backgroundColor: 'rgba(255,255,255,0.2)',
  },

  // ─── Date stamp ───
  dateStamp: {
    borderWidth: 2, borderRadius: 2,
    paddingHorizontal: 10, paddingVertical: 4,
    alignSelf: 'flex-start',
    transform: [{ rotate: '-3deg' }],
    opacity: 0.7,
  },
  dateStampText: {
    fontSize: 9, fontWeight: '800',
    letterSpacing: 2, textTransform: 'uppercase',
  },
  dateStampLine: {
    height: 1, marginTop: 2, opacity: 0.4,
  },
});
