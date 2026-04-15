import React, { useState, useRef, useEffect, useContext } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  StatusBar, Dimensions, Platform, Animated, Easing, Alert, Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext, ThemeContext } from '../../App';
import { usersAPI, quizAPI } from '../api';
import { AnimatedCounter, ProgressRing } from '../components/PremiumAnimations';
import { PressableCard, SuccessCheck, FadeInView } from '../components/AnimatedComponents';
import { Stamp, DoodleDivider, MarkerUnderline } from '../components/SketchComponents';

const { width } = Dimensions.get('window');
const INK = '#2C1810';
const PAPER = '#FDF6E3';
const ACCENT = '#FFD60A';
const BLUE = '#2563EB';
const GREEN = '#059669';
const RED = '#DC2626';
const SERIF = Platform.OS === 'ios' ? 'Georgia' : 'serif';

// ─── Quiz Data by Domain ───
// Shuffle array helper
const shuffle = (arr) => { const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

// Pick N random questions from pool
const pickQuestions = (pool, n = 5) => shuffle(pool).slice(0, n);

const QUIZ_POOL = {
  physics: {
    icon: 'planet', color: '#EA580C', title: 'Physics',
    pool: [
      // Classic
      { q: 'What is the speed of light in vacuum?', options: ['3 × 10⁸ m/s', '3 × 10⁶ m/s', '3 × 10¹⁰ m/s', '3 × 10⁴ m/s'], correct: 0 },
      { q: 'What is the unit of electrical resistance?', options: ['Volt', 'Ampere', 'Ohm', 'Watt'], correct: 2 },
      { q: 'What force keeps planets in orbit around the Sun?', options: ['Electromagnetic', 'Strong nuclear', 'Gravity', 'Friction'], correct: 2 },
      // Tricky
      { q: 'If you drop a feather and a bowling ball on the Moon (no air), which hits the ground first?', options: ['Feather', 'Bowling ball', 'They hit at the same time', 'Neither — they float'], correct: 2 },
      { q: 'You\'re in a car moving at 60 mph. You throw a ball forward at 20 mph. How fast is the ball moving to someone standing outside?', options: ['20 mph', '40 mph', '60 mph', '80 mph'], correct: 3 },
      { q: 'A boat floats in a pool inside a locked room. If you drop anchor into the water, does the water level in the pool rise, fall, or stay the same?', options: ['Rises', 'Falls', 'Stays the same', 'Depends on anchor weight'], correct: 1 },
      // Scenario
      { q: 'An astronaut on the ISS pours water from a bottle. What shape does the water take?', options: ['Puddle on floor', 'Sphere floating in air', 'Flows upward', 'Stays in bottle'], correct: 1 },
      { q: 'You hear thunder 10 seconds after seeing lightning. Approximately how far away was the strike?', options: ['1 km', '2 km', '3.4 km', '10 km'], correct: 2 },
      { q: 'Why does a spinning ice skater speed up when pulling arms in?', options: ['Less air resistance', 'Conservation of angular momentum', 'Gravity pulls harder', 'More muscle force'], correct: 1 },
      { q: 'If Earth suddenly stopped spinning, what would happen to objects on the surface?', options: ['Nothing', 'They\'d fly eastward at high speed', 'They\'d float up', 'They\'d get heavier'], correct: 1 },
      { q: 'A mirror reflects light. What happens to the speed of light when it enters glass?', options: ['Speeds up', 'Slows down', 'Stays the same', 'Stops completely'], correct: 1 },
      { q: 'Which has more energy: a photon of red light or blue light?', options: ['Red', 'Blue', 'Equal energy', 'Depends on brightness'], correct: 1 },
    ],
  },
  ai: {
    icon: 'hardware-chip', color: '#0D9488', title: 'Artificial Intelligence',
    pool: [
      // Classic
      { q: 'What does GPT stand for?', options: ['General Processing Tool', 'Generative Pre-trained Transformer', 'Global Pattern Technology', 'Graph Processing Tree'], correct: 1 },
      { q: 'Which technique trains AI using rewards and penalties?', options: ['Supervised Learning', 'Reinforcement Learning', 'Transfer Learning', 'Clustering'], correct: 1 },
      // Tricky
      { q: 'A chatbot passes the Turing Test. Does this prove it\'s truly intelligent?', options: ['Yes, it thinks like humans', 'No, it only mimics intelligence', 'Only if it has emotions', 'Only if it has consciousness'], correct: 1 },
      { q: 'You train a model on 10,000 cat photos. It gets 99% accuracy on training data but 50% on new photos. What happened?', options: ['Underfitting', 'Overfitting', 'Perfect training', 'Data poisoning'], correct: 1 },
      { q: 'An AI recommends only action movies to a user. The user watches them and AI recommends more action. What problem is this?', options: ['Hallucination', 'Filter bubble / echo chamber', 'Data leakage', 'Mode collapse'], correct: 1 },
      // Scenario
      { q: 'A self-driving car must choose: hit 1 pedestrian or swerve and risk 3 passengers. What ethical framework is this?', options: ['The Trolley Problem', 'Turing Test', 'Chinese Room', 'Frame Problem'], correct: 0 },
      { q: 'You ask ChatGPT about a real person and it makes up false details. This is called:', options: ['Bias', 'Hallucination', 'Overfitting', 'Underfitting'], correct: 1 },
      { q: 'A company uses AI to screen resumes. It rejects most female candidates. What went wrong?', options: ['AI is inherently sexist', 'Training data had historical bias', 'Algorithm is too simple', 'Not enough data'], correct: 1 },
      { q: 'Which AI technique would you use to generate realistic human faces that don\'t exist?', options: ['Decision Trees', 'GANs (Generative Adversarial Networks)', 'Linear Regression', 'K-Means Clustering'], correct: 1 },
      { q: 'Your spam filter marks an important email as spam. This is a:', options: ['True positive', 'True negative', 'False positive', 'False negative'], correct: 2 },
      { q: 'An AI model trained on English text is asked to translate Chinese. It performs poorly because:', options: ['AI can\'t learn languages', 'It wasn\'t trained on Chinese data', 'Chinese is too complex', 'Translation is impossible for AI'], correct: 1 },
      { q: 'What makes a transformer model different from older RNN models?', options: ['Uses more data', 'Processes all words simultaneously via attention', 'Has more layers', 'Runs on better hardware'], correct: 1 },
    ],
  },
  space: {
    icon: 'rocket', color: '#4F46E5', title: 'Space & Astronomy',
    pool: [
      { q: 'Which planet is known as the Red Planet?', options: ['Venus', 'Jupiter', 'Mars', 'Saturn'], correct: 2 },
      { q: 'What is a light-year a measure of?', options: ['Time', 'Speed', 'Distance', 'Brightness'], correct: 2 },
      // Tricky
      { q: 'If you could fly to the Sun at airplane speed (900 km/h), approximately how long would it take?', options: ['1 month', '6 months', '17 years', '100 years'], correct: 2 },
      { q: 'The Sun makes up what percentage of our solar system\'s total mass?', options: ['50%', '75%', '90%', '99.8%'], correct: 3 },
      { q: 'There\'s a planet where it rains diamonds. Which one?', options: ['Mars', 'Jupiter', 'Neptune', 'Mercury'], correct: 2 },
      // Scenario
      { q: 'You\'re standing on Mars. The sky during daytime looks:', options: ['Blue like Earth', 'Black like space', 'Butterscotch/pinkish', 'Green'], correct: 2 },
      { q: 'If you scream in space, what happens?', options: ['Sound travels slowly', 'Sound travels faster', 'No one hears — no medium for sound', 'Only you hear it'], correct: 2 },
      { q: 'A neutron star the size of a sugar cube would weigh on Earth approximately:', options: ['1 ton', '100 tons', '1 billion tons', '1 gram'], correct: 2 },
      { q: 'Olympus Mons on Mars is 3x taller than Everest. Why can it be so tall?', options: ['More volcanism', 'Lower gravity allows taller structures', 'It\'s not actually a mountain', 'Thicker atmosphere pushes it up'], correct: 1 },
      { q: 'How long does light from the Sun take to reach Earth?', options: ['Instantly', '8 seconds', '8 minutes', '8 hours'], correct: 2 },
      { q: 'What would happen to your blood if you were exposed to space without a suit?', options: ['Freeze instantly', 'Boil due to low pressure', 'Nothing for a few seconds', 'Evaporate'], correct: 1 },
    ],
  },
  biology: {
    icon: 'flask', color: '#059669', title: 'Biology',
    pool: [
      { q: 'What is the powerhouse of the cell?', options: ['Nucleus', 'Ribosome', 'Mitochondria', 'Golgi body'], correct: 2 },
      { q: 'What molecule carries genetic information?', options: ['RNA', 'DNA', 'Protein', 'Lipid'], correct: 1 },
      // Tricky
      { q: 'Humans share approximately what % of DNA with bananas?', options: ['0%', '25%', '60%', '98%'], correct: 2 },
      { q: 'If all bacteria in your body disappeared instantly, what would happen?', options: ['Nothing', 'You\'d feel better', 'Your immune and digestive systems would fail', 'You\'d lose weight'], correct: 2 },
      { q: 'Which human organ can regenerate itself even after 75% is removed?', options: ['Heart', 'Brain', 'Liver', 'Kidney'], correct: 2 },
      // Scenario
      { q: 'A doctor uses CRISPR to edit a gene in an embryo. The change will pass to ALL future generations. This is called:', options: ['Somatic editing', 'Germline editing', 'Gene therapy', 'Cloning'], correct: 1 },
      { q: 'A patient can\'t produce insulin. Which disease do they most likely have?', options: ['Cancer', 'Diabetes', 'Alzheimer\'s', 'Malaria'], correct: 1 },
      { q: 'Tardigrades (water bears) can survive in space vacuum. How?', options: ['They breathe CO2', 'They enter cryptobiosis (suspended animation)', 'They have space suits', 'They\'re not actually alive'], correct: 1 },
      { q: 'You cut a planarian worm in half. What happens?', options: ['It dies', 'Only head half survives', 'Both halves grow into complete worms', 'They merge back'], correct: 2 },
      { q: 'Why can\'t humans digest cellulose (plant fiber) but cows can?', options: ['Humans lack the right gut bacteria', 'Cellulose is poisonous to humans', 'Humans have shorter intestines', 'Cows have 4 stomachs with special enzymes'], correct: 3 },
      { q: 'Identical twins have the same DNA. Can they have different fingerprints?', options: ['No, always identical', 'Yes, fingerprints are affected by environment in the womb', 'Only if they\'re different ages', 'Fingerprints aren\'t genetic'], correct: 1 },
    ],
  },
  history: {
    icon: 'library', color: '#7C3AED', title: 'History',
    pool: [
      { q: 'In what year did World War II end?', options: ['1943', '1944', '1945', '1946'], correct: 2 },
      { q: 'The Great Wall was built primarily to defend against:', options: ['Romans', 'Mongol invasions', 'Japanese', 'Indian armies'], correct: 1 },
      // Tricky
      { q: 'Cleopatra lived closer in time to the Moon landing than to the building of the Great Pyramid. True or false?', options: ['True', 'False', 'They were the same era', 'Cleopatra never existed'], correct: 0 },
      { q: 'Which empire was the largest in history by land area?', options: ['Roman Empire', 'Mongol Empire', 'British Empire', 'Ottoman Empire'], correct: 2 },
      { q: 'The shortest war in history lasted 38-45 minutes. Between which countries?', options: ['USA & Mexico', 'Britain & Zanzibar', 'France & Germany', 'Japan & Russia'], correct: 1 },
      // Scenario
      { q: 'A civilization builds pyramids without metal tools or wheels. How did they likely move massive stone blocks?', options: ['Aliens', 'Ramps, levers, and thousands of workers', 'Elephants', 'Magic'], correct: 1 },
      { q: 'The Library of Alexandria was destroyed. If it survived, scholars believe:', options: ['Nothing would change', 'We might be centuries more advanced', 'It only had fiction books', 'The books were already copied'], correct: 1 },
      { q: 'Before Columbus, many educated Europeans already knew Earth was round. Who proved it first?', options: ['Columbus', 'Ancient Greeks (Eratosthenes)', 'Galileo', 'Copernicus'], correct: 1 },
      { q: 'The Titanic sank in 1912. A novel written 14 years earlier described a ship called "Titan" sinking after hitting an iceberg. Coincidence?', options: ['The author was a time traveler', 'Yes, remarkable coincidence', 'The novel caused the disaster', 'It\'s a myth'], correct: 1 },
      { q: 'Napoleon was famously short. What was his actual height?', options: ['5\'2" (very short)', '5\'7" (average for his era)', '4\'11"', '6\'0"'], correct: 1 },
      { q: 'Which ancient civilization invented the concept of zero as a number?', options: ['Romans', 'Greeks', 'Indians', 'Egyptians'], correct: 2 },
    ],
  },
  technology: {
    icon: 'code-slash', color: '#2563EB', title: 'Technology',
    pool: [
      { q: 'What does HTML stand for?', options: ['Hyper Text Markup Language', 'High Tech Modern Language', 'Hyper Transfer Mail Language', 'Home Tool Markup Language'], correct: 0 },
      // Tricky
      { q: 'You have 1 GB of RAM. How many browser tabs with heavy websites can you realistically keep open?', options: ['100+', '50-60', '5-15', '1-2'], correct: 2 },
      { q: 'A website shows a green padlock (HTTPS). Does this mean the site is safe?', options: ['Yes, 100% safe', 'No, it only means data is encrypted in transit', 'Only if it\'s a .gov site', 'Green padlock no longer exists'], correct: 1 },
      { q: 'What happens when you type "google.com" and press Enter? The FIRST thing that happens is:', options: ['Google\'s page loads', 'DNS lookup converts domain to IP address', 'Your browser sends encrypted data', 'Google sends you cookies'], correct: 1 },
      // Scenario
      { q: 'A company stores passwords as plain text in their database. A hacker gets access. What\'s the impact?', options: ['No impact', 'All users\' passwords are immediately exposed', 'Only admin passwords are exposed', 'Passwords auto-reset'], correct: 1 },
      { q: 'You\'re building an app that needs to work offline. Which technology would you use to store data locally?', options: ['Cloud database', 'Local storage / SQLite', 'CDN', 'DNS'], correct: 1 },
      { q: 'Blockchain is "decentralized." What does this actually mean in practice?', options: ['No single company controls the database', 'It\'s faster than regular databases', 'Data can\'t be stored', 'Only banks can use it'], correct: 0 },
      { q: 'A programmer writes an infinite loop. What happens to the application?', options: ['It runs forever efficiently', 'It freezes/crashes from using all resources', 'The computer shuts down', 'Nothing — modern OSes prevent this'], correct: 1 },
      { q: 'Why do phones get warm when running heavy apps?', options: ['Battery is defective', 'CPU generates heat from processing', 'Screen produces heat', 'Wireless signals cause heat'], correct: 1 },
      { q: 'What\'s the difference between 4G and 5G in simple terms?', options: ['5G has better cameras', '5G is faster with lower latency', '5G uses different satellites', '5G only works indoors'], correct: 1 },
      { q: 'You delete a file and empty the recycle bin. Is the data truly gone?', options: ['Yes, completely erased', 'No — the space is marked as available but data remains until overwritten', 'Only on SSDs', 'Only if you restart'], correct: 1 },
    ],
  },
  nature: {
    icon: 'leaf', color: '#059669', title: 'Nature',
    pool: [
      { q: 'What is the largest ocean on Earth?', options: ['Atlantic', 'Indian', 'Pacific', 'Arctic'], correct: 2 },
      // Tricky
      { q: 'Which is the deadliest animal to humans (kills the most people per year)?', options: ['Sharks', 'Snakes', 'Mosquitoes', 'Lions'], correct: 2 },
      { q: 'If all insects disappeared tomorrow, what would happen?', options: ['Nothing', 'Most ecosystems would collapse within decades', 'Only flowers would die', 'Fish would thrive'], correct: 1 },
      { q: 'The Amazon Rainforest produces 20% of Earth\'s oxygen. But it also consumes nearly all of it. Who actually produces most oxygen?', options: ['Forests', 'Ocean phytoplankton', 'Grass', 'Algae in lakes'], correct: 1 },
      // Scenario
      { q: 'You see a plant growing toward a window. This response to light is called:', options: ['Photosynthesis', 'Phototropism', 'Gravitropism', 'Osmosis'], correct: 1 },
      { q: 'A chameleon changes color. The PRIMARY reason is:', options: ['Camouflage', 'Temperature regulation and communication', 'To scare predators', 'To attract food'], correct: 1 },
      { q: 'Coral reefs are "bleaching" white worldwide. What causes this?', options: ['Pollution', 'Rising ocean temperatures stress corals', 'Too many fish', 'Volcanic ash'], correct: 1 },
      { q: 'Dogs can smell diseases like cancer. How?', options: ['They can\'t — it\'s a myth', 'Diseases produce volatile organic compounds dogs can detect', 'They sense body heat', 'They read facial expressions'], correct: 1 },
      { q: 'A single tree can "communicate" with others through underground networks. This is called:', options: ['Root mail', 'The Wood Wide Web (mycorrhizal networks)', 'Tree telepathy', 'Photosynthesis chains'], correct: 1 },
      { q: 'Why do leaves change color in autumn?', options: ['Cold air paints them', 'Trees stop producing green chlorophyll, revealing other pigments', 'Leaves die and rot', 'Sunlight changes angle'], correct: 1 },
      { q: 'If you put a goldfish in a dark room, what happens to its color?', options: ['Stays the same', 'Turns white/pale over time', 'Turns black', 'Glows in the dark'], correct: 1 },
    ],
  },
  mathematics: {
    icon: 'calculator', color: '#EA580C', title: 'Mathematics',
    pool: [
      { q: 'What is the value of Pi (first 3 digits)?', options: ['3.12', '3.14', '3.16', '3.18'], correct: 1 },
      // Tricky
      { q: 'You flip a fair coin 10 times and get heads every time. What\'s the probability the next flip is heads?', options: ['Very low — tails is "due"', 'Still exactly 50%', 'Higher than 50%', '100% — it\'s rigged'], correct: 1 },
      { q: '0.999999... (repeating forever) equals:', options: ['Almost 1 but not quite', 'Exactly 1', 'Less than 1', 'Undefined'], correct: 1 },
      { q: 'In a room of 23 people, what\'s the probability that at least 2 share a birthday?', options: ['About 5%', 'About 23%', 'About 50%', 'About 95%'], correct: 2 },
      // Scenario
      { q: 'A pizza place offers 2 sizes: 12-inch for $10 or 16-inch for $16. Which is the better deal by area?', options: ['12-inch', '16-inch has 78% more pizza for 60% more money', 'They\'re equal', 'Need more info'], correct: 1 },
      { q: 'You double a penny every day for 30 days. How much do you have?', options: ['$3.00', '$30.00', 'About $5.4 million', 'About $10.7 million'], correct: 3 },
      { q: 'A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How much does the ball cost?', options: ['$0.10', '$0.05', '$0.15', '$0.01'], correct: 1 },
      { q: 'There are 3 doors. Behind one is a car, behind others are goats. You pick door 1. Host opens door 3 (goat). Should you switch to door 2?', options: ['No — 50/50 either way', 'Yes — switching gives you 2/3 chance', 'Doesn\'t matter', 'Only if you like goats'], correct: 1 },
      { q: 'How many times can you fold a piece of paper in half?', options: ['Unlimited times', 'About 7-8 times', 'Exactly 12 times', '100+ times'], correct: 1 },
      { q: 'If you shuffle a deck of 52 cards, the number of possible arrangements is:', options: ['Thousands', 'Millions', 'More than atoms in the observable universe', 'Exactly 52'], correct: 2 },
      { q: 'What is the sum of all numbers from 1 to 100?', options: ['5,000', '5,050', '10,000', '10,100'], correct: 1 },
    ],
  },
};

// Build quiz bank with random selection
const QUIZ_BANK = {};
Object.keys(QUIZ_POOL).forEach(domain => {
  QUIZ_BANK[domain] = {
    icon: QUIZ_POOL[domain].icon,
    color: QUIZ_POOL[domain].color,
    title: QUIZ_POOL[domain].title,
    questions: pickQuestions(QUIZ_POOL[domain].pool, 5),
  };
});

const DOMAINS = Object.keys(QUIZ_BANK);

export default function QuizScreen({ navigation, route }) {
  const { user } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);
  const initialDomain = route?.params?.domain || null;

  const [phase, setPhase] = useState(initialDomain ? 'loading' : 'select'); // select, loading, quiz, result, history
  const [domain, setDomain] = useState(initialDomain || 'physics');
  const [questionIdx, setQuestionIdx] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [score, setScore] = useState(0);
  const [timer, setTimer] = useState(15);
  const [showCorrect, setShowCorrect] = useState(false);
  const [quizHistory, setQuizHistory] = useState([]);
  const [activeQuestions, setActiveQuestions] = useState([]);
  const [seenQuestions, setSeenQuestions] = useState({});
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [explanation, setExplanation] = useState('');

  // Load quiz history + seen questions on mount
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem('quiz_history');
        if (stored) setQuizHistory(JSON.parse(stored));
        const seen = await AsyncStorage.getItem('quiz_seen_questions');
        if (seen) setSeenQuestions(JSON.parse(seen));
      } catch {}
      if (initialDomain) fetchQuizQuestions(initialDomain);
    })();
  }, []);

  // Fetch AI-generated questions from Groq, fallback to local
  const fetchQuizQuestions = async (d) => {
    setLoadingQuiz(true);
    setPhase('loading');
    const domainSeen = seenQuestions[d] || [];

    try {
      const res = await quizAPI.generate({
        domain: d,
        count: 5,
        difficulty: 'mixed',
        exclude: domainSeen.slice(-30).join(','),
      });
      const questions = res.data?.questions || [];
      if (questions.length >= 3) {
        setActiveQuestions(questions);
        // Track seen questions
        const newSeen = { ...seenQuestions, [d]: [...domainSeen, ...questions.map(q => q.q.substring(0, 40))] };
        setSeenQuestions(newSeen);
        AsyncStorage.setItem('quiz_seen_questions', JSON.stringify(newSeen)).catch(() => {});
        setPhase('quiz');
        setLoadingQuiz(false);
        return;
      }
    } catch (e) {
      console.log('AI quiz generation failed, using local:', e?.message);
    }

    // Fallback to local questions
    const localPool = QUIZ_POOL[d]?.pool || [];
    const unseen = localPool.filter(q => !domainSeen.includes(q.q.substring(0, 40)));
    const pool = unseen.length >= 5 ? unseen : localPool;
    setActiveQuestions(pickQuestions(pool, 5).map(q => ({ ...q, explanation: '' })));
    setPhase('quiz');
    setLoadingQuiz(false);
  };

  // Animations
  const questionFade = useRef(new Animated.Value(0)).current;
  const optionAnims = useRef([0, 1, 2, 3].map(() => new Animated.Value(0))).current;
  const timerWidth = useRef(new Animated.Value(100)).current;
  const resultScale = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  const quiz = QUIZ_POOL[domain] || QUIZ_POOL.physics;
  const currentQ = activeQuestions[questionIdx];
  const totalQuestions = activeQuestions.length || 5;

  // Timer countdown
  useEffect(() => {
    if (phase !== 'quiz' || showCorrect) return;
    setTimer(15);
    timerWidth.setValue(100);
    Animated.timing(timerWidth, { toValue: 0, duration: 15000, easing: Easing.linear, useNativeDriver: false }).start();
    const interval = setInterval(() => {
      setTimer(prev => {
        if (prev <= 1) { clearInterval(interval); handleTimeout(); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [questionIdx, phase, showCorrect]);

  // Animate question entrance
  useEffect(() => {
    if (phase !== 'quiz') return;
    questionFade.setValue(0);
    optionAnims.forEach(a => a.setValue(0));
    Animated.sequence([
      Animated.timing(questionFade, { toValue: 1, duration: 300, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      Animated.stagger(80, optionAnims.map(a =>
        Animated.timing(a, { toValue: 1, duration: 250, easing: Easing.out(Easing.back(1.3)), useNativeDriver: true })
      )),
    ]).start();
  }, [questionIdx, phase]);

  const handleTimeout = () => {
    setAnswers(prev => [...prev, -1]);
    nextQuestion();
  };

  const handleAnswer = (idx) => {
    if (selectedAnswer !== null) return;
    setSelectedAnswer(idx);
    setShowCorrect(true);
    const isCorrect = idx === currentQ.correct;
    if (isCorrect) setScore(prev => prev + 1);
    setAnswers(prev => [...prev, idx]);
    setExplanation(currentQ.explanation || '');
    setTimeout(() => { setExplanation(''); nextQuestion(); }, currentQ.explanation ? 2200 : 1200);
  };

  const nextQuestion = () => {
    setSelectedAnswer(null);
    setShowCorrect(false);
    if (questionIdx + 1 >= totalQuestions) {
      const finalScore = score;
      setPhase('result');
      Animated.spring(resultScale, { toValue: 1, friction: 5, tension: 80, useNativeDriver: true }).start();
      // Award IQ points via API
      try { usersAPI.earnIQ({ action: 'complete_quiz', content_id: domain }); } catch {}
      // Save quiz to history
      const historyEntry = {
        id: Date.now().toString(),
        domain,
        title: quiz.title,
        score: finalScore,
        total: totalQuestions,
        accuracy: Math.round((finalScore / totalQuestions) * 100),
        iqEarned: finalScore * 5,
        date: new Date().toISOString(),
      };
      const newHistory = [historyEntry, ...quizHistory].slice(0, 50);
      setQuizHistory(newHistory);
      AsyncStorage.setItem('quiz_history', JSON.stringify(newHistory)).catch(() => {});
    } else {
      setQuestionIdx(prev => prev + 1);
    }
  };

  const restartQuiz = (newDomain) => {
    const d = newDomain || domain;
    setQuestionIdx(0); setSelectedAnswer(null); setAnswers([]);
    setScore(0); setShowCorrect(false); setExplanation('');
    resultScale.setValue(0);
    fetchQuizQuestions(d);
  };

  const getOptionStyle = (idx) => {
    if (!showCorrect) return selectedAnswer === idx ? s.optionSelected : s.option;
    if (idx === currentQ.correct) return s.optionCorrect;
    if (idx === selectedAnswer && idx !== currentQ.correct) return s.optionWrong;
    return s.option;
  };

  const getOptionIcon = (idx) => {
    if (!showCorrect) return null;
    if (idx === currentQ.correct) return <Ionicons name="checkmark-circle" size={20} color={GREEN} />;
    if (idx === selectedAnswer && idx !== currentQ.correct) return <Ionicons name="close-circle" size={20} color={RED} />;
    return null;
  };

  const accuracy = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;
  const iqEarned = score * 5;
  const grade = accuracy >= 90 ? 'A+' : accuracy >= 80 ? 'A' : accuracy >= 70 ? 'B' : accuracy >= 60 ? 'C' : accuracy >= 50 ? 'D' : 'F';

  // ─── DOMAIN SELECT SCREEN ───
  if (phase === 'select') {
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 35 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>

        <ScrollView contentContainerStyle={s.selectScroll} showsVerticalScrollIndicator={false}>
          {/* Header */}
          <View style={s.selectHeader}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
              <Ionicons name="arrow-back" size={20} color={INK} />
            </TouchableOpacity>
            <View>
              <Text style={s.selectTitle}>Knowledge Quiz</Text>
              <Text style={s.selectSubtitle}>Test what you've learned</Text>
            </View>
          </View>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginLeft: 20, marginBottom: 14 }}>
            <MarkerUnderline color={ACCENT} width={80} />
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#0D948815', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, borderWidth: 1, borderColor: '#0D948830' }}>
              <Ionicons name="sparkles" size={10} color="#0D9488" />
              <Text style={{ fontSize: 9, fontWeight: '800', color: '#0D9488', letterSpacing: 1 }}>AI POWERED</Text>
            </View>
          </View>

          {/* History button */}
          {quizHistory.length > 0 && (
            <TouchableOpacity style={s.historyBtn} onPress={() => setPhase('history')}>
              <Ionicons name="time-outline" size={16} color={BLUE} />
              <Text style={s.historyBtnText}>Quiz History ({quizHistory.length})</Text>
              <Ionicons name="chevron-forward" size={14} color={BLUE} />
            </TouchableOpacity>
          )}

          {/* Your Stats */}
          {quizHistory.length > 0 && (
            <View style={s.yourStats}>
              <View style={s.yourStatItem}>
                <Text style={s.yourStatNum}>{quizHistory.length}</Text>
                <Text style={s.yourStatLabel}>Quizzes</Text>
              </View>
              <View style={s.yourStatItem}>
                <Text style={s.yourStatNum}>{Math.round(quizHistory.reduce((a, h) => a + h.accuracy, 0) / quizHistory.length)}%</Text>
                <Text style={s.yourStatLabel}>Avg Score</Text>
              </View>
              <View style={s.yourStatItem}>
                <Text style={s.yourStatNum}>{quizHistory.reduce((a, h) => a + h.iqEarned, 0)}</Text>
                <Text style={s.yourStatLabel}>IQ Earned</Text>
              </View>
            </View>
          )}

          {/* Domain cards */}
          <View style={s.domainGrid}>
            {DOMAINS.map((d, i) => {
              const q = QUIZ_BANK[d];
              return (
                <FadeInView key={d} delay={i * 60}>
                  <PressableCard
                    style={[s.domainCard, { borderColor: q.color }]}
                    onPress={() => { setDomain(d); restartQuiz(d); }}
                  >
                    <View style={[s.domainIconWrap, { backgroundColor: q.color + '12' }]}>
                      <Ionicons name={q.icon} size={28} color={q.color} />
                    </View>
                    <Text style={[s.domainName, { color: q.color }]}>{q.title}</Text>
                    <Text style={s.domainCount}>{QUIZ_POOL[d].pool.length} questions</Text>
                    <View style={[s.domainBadge, { backgroundColor: q.color + '15', borderColor: q.color + '30' }]}>
                      <Text style={[s.domainBadgeText, { color: q.color }]}>START</Text>
                    </View>
                  </PressableCard>
                </FadeInView>
              );
            })}
          </View>
        </ScrollView>
      </View>
    );
  }

  // ─── HISTORY SCREEN ───
  if (phase === 'history') {
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 35 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>
        <View style={s.selectHeader}>
          <TouchableOpacity onPress={() => setPhase('select')} style={s.backBtn}>
            <Ionicons name="arrow-back" size={20} color={INK} />
          </TouchableOpacity>
          <Text style={s.selectTitle}>Quiz History</Text>
        </View>
        <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
          {quizHistory.map((h, i) => {
            const qb = QUIZ_BANK[h.domain] || {};
            return (
              <FadeInView key={h.id} delay={i * 50}>
                <View style={[s.historyCard, { borderLeftColor: qb.color || '#C4AA78' }]}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <View style={[s.historyIcon, { backgroundColor: (qb.color || '#8A7558') + '15' }]}>
                      <Ionicons name={qb.icon || 'school'} size={18} color={qb.color || '#8A7558'} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.historyTitle}>{h.title}</Text>
                      <Text style={s.historyDate}>{new Date(h.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</Text>
                    </View>
                    <View style={[s.historyGrade, { backgroundColor: h.accuracy >= 60 ? GREEN + '15' : RED + '15' }]}>
                      <Text style={[s.historyGradeText, { color: h.accuracy >= 60 ? GREEN : RED }]}>{h.accuracy}%</Text>
                    </View>
                  </View>
                  <View style={{ flexDirection: 'row', gap: 16 }}>
                    <Text style={s.historyMeta}><Ionicons name="checkmark" size={12} color={GREEN} /> {h.score}/{h.total}</Text>
                    <Text style={s.historyMeta}><Ionicons name="flash" size={12} color="#EA580C" /> +{h.iqEarned} IQ</Text>
                  </View>
                </View>
              </FadeInView>
            );
          })}
          {quizHistory.length === 0 && (
            <View style={{ alignItems: 'center', paddingTop: 60 }}>
              <Ionicons name="time-outline" size={48} color="#C4AA78" />
              <Text style={{ color: INK, fontWeight: '700', fontSize: 16, marginTop: 12 }}>No quizzes yet</Text>
              <Text style={{ color: '#8A7558', fontSize: 13, marginTop: 4 }}>Complete a quiz to see your history</Text>
            </View>
          )}
        </ScrollView>
      </View>
    );
  }

  // ─── RESULT SCREEN ───
  if (phase === 'result') {
    return (
      <View style={s.container}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 35 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>

        <ScrollView contentContainerStyle={s.resultScroll} showsVerticalScrollIndicator={false}>
          <Animated.View style={[s.resultCard, { transform: [{ scale: resultScale }] }]}>
            {/* Stamp */}
            <View style={s.resultStamp}>
              <Text style={s.resultStampText}>QUIZ DONE</Text>
            </View>

            {/* Score circle */}
            <View style={s.scoreCircle}>
              <View style={[s.scoreInner, { borderColor: accuracy >= 60 ? GREEN : RED }]}>
                <AnimatedCounter value={score} style={s.scoreNum} />
                <Text style={s.scoreOf}>/ {totalQuestions}</Text>
              </View>
            </View>

            <Text style={s.gradeText}>Grade: <Text style={{ color: accuracy >= 60 ? GREEN : RED }}>{grade}</Text></Text>

            {/* Stats grid */}
            <View style={s.statsGrid}>
              <View style={s.statBox}>
                <Ionicons name="checkmark-circle" size={22} color={GREEN} />
                <AnimatedCounter value={score} style={s.statNum} />
                <Text style={s.statLabel}>Correct</Text>
              </View>
              <View style={s.statBox}>
                <Ionicons name="close-circle" size={22} color={RED} />
                <AnimatedCounter value={totalQuestions - score} style={s.statNum} />
                <Text style={s.statLabel}>Wrong</Text>
              </View>
              <View style={s.statBox}>
                <Ionicons name="analytics" size={22} color={BLUE} />
                <AnimatedCounter value={accuracy} style={s.statNum} suffix="%" />
                <Text style={s.statLabel}>Accuracy</Text>
              </View>
              <View style={s.statBox}>
                <Ionicons name="flash" size={22} color="#EA580C" />
                <AnimatedCounter value={iqEarned} style={s.statNum} />
                <Text style={s.statLabel}>IQ Earned</Text>
              </View>
            </View>

            <DoodleDivider style={{ marginVertical: 16 }} />

            {/* Actions */}
            <TouchableOpacity style={s.retryBtn} onPress={restartQuiz}>
              <Ionicons name="reload" size={18} color={INK} />
              <Text style={s.retryBtnText}>Try Again</Text>
            </TouchableOpacity>

            <TouchableOpacity style={s.changeDomainBtn} onPress={() => { setPhase('select'); setQuestionIdx(0); setAnswers([]); setScore(0); }}>
              <Ionicons name="grid-outline" size={16} color={BLUE} />
              <Text style={s.changeDomainText}>Choose Another Topic</Text>
            </TouchableOpacity>

            <TouchableOpacity style={s.backHomeBtn} onPress={() => navigation.goBack()}>
              <Text style={s.backHomeText}>Back to Feed</Text>
            </TouchableOpacity>
          </Animated.View>
        </ScrollView>
      </View>
    );
  }

  // ─── LOADING SCREEN ───
  if (phase === 'loading') {
    return (
      <View style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
        <View style={s.ruledBg} pointerEvents="none">
          {Array.from({ length: 35 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
          <View style={s.margin} />
        </View>
        <View style={{ alignItems: 'center' }}>
          <View style={{ width: 60, height: 60, borderRadius: 30, borderWidth: 2.5, borderColor: INK, borderStyle: 'dashed', justifyContent: 'center', alignItems: 'center', marginBottom: 16 }}>
            <Ionicons name="bulb" size={28} color={ACCENT} />
          </View>
          <Text style={{ fontSize: 16, fontWeight: '800', color: INK, marginBottom: 6 }}>Generating Questions...</Text>
          <Text style={{ fontSize: 12, color: '#8A7558', fontStyle: 'italic' }}>AI is crafting unique questions for you</Text>
        </View>
      </View>
    );
  }

  // ─── QUIZ QUESTION SCREEN ───
  if (!currentQ) return null;
  return (
    <View style={s.container}>
      <StatusBar barStyle="dark-content" backgroundColor={PAPER} />
      <View style={s.ruledBg} pointerEvents="none">
        {Array.from({ length: 35 }, (_, i) => <View key={i} style={[s.ruled, { top: i * 28 }]} />)}
        <View style={s.margin} />
      </View>

      {/* Header */}
      <View style={s.quizHeader}>
        <TouchableOpacity onPress={() => { Alert.alert('Quit Quiz?', 'Your progress will be lost.', [
          { text: 'Cancel' }, { text: 'Quit', style: 'destructive', onPress: () => navigation.goBack() }
        ]); }} style={s.backBtn}>
          <Ionicons name="close" size={22} color={INK} />
        </TouchableOpacity>
        <View style={s.quizHeaderCenter}>
          <Stamp domain={domain} style={{ transform: [{ rotate: '0deg' }] }} />
          <Text style={s.qProgress}>{questionIdx + 1} / {totalQuestions}</Text>
        </View>
        <View style={s.timerWrap}>
          <Ionicons name="time-outline" size={16} color={timer <= 5 ? RED : INK} />
          <Text style={[s.timerText, timer <= 5 && { color: RED }]}>{timer}s</Text>
        </View>
      </View>

      {/* Timer bar */}
      <View style={s.timerBarBg}>
        <Animated.View style={[s.timerBarFill, {
          width: timerWidth.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] }),
          backgroundColor: timer <= 5 ? RED : timer <= 10 ? '#EA580C' : GREEN,
        }]} />
      </View>

      {/* Progress dots */}
      <View style={s.progressDots}>
        {quiz.questions.map((_, i) => (
          <View key={i} style={[
            s.dot,
            i < questionIdx && answers[i] === quiz.questions[i].correct && s.dotCorrect,
            i < questionIdx && answers[i] !== quiz.questions[i].correct && s.dotWrong,
            i === questionIdx && s.dotCurrent,
          ]} />
        ))}
      </View>

      {/* Question */}
      <ScrollView contentContainerStyle={s.questionScroll} showsVerticalScrollIndicator={false}>
        <Animated.View style={[s.questionCard, { opacity: questionFade, transform: [{ translateY: questionFade.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] }]}>
          <View style={s.qNumBadge}>
            <Text style={s.qNumText}>Q{questionIdx + 1}</Text>
          </View>
          <Text style={s.questionText}>{currentQ?.q}</Text>
        </Animated.View>

        {/* Options */}
        <View style={s.optionsWrap}>
          {currentQ?.options.map((opt, i) => {
            const optStyle = getOptionStyle(i);
            const icon = getOptionIcon(i);
            return (
              <Animated.View key={i} style={{
                opacity: optionAnims[i],
                transform: [{ translateY: optionAnims[i].interpolate({ inputRange: [0, 1], outputRange: [30, 0] }) }],
              }}>
                <PressableCard
                  style={optStyle}
                  onPress={() => handleAnswer(i)}
                >
                  <View style={s.optionLetter}>
                    <Text style={s.optionLetterText}>{String.fromCharCode(65 + i)}</Text>
                  </View>
                  <Text style={s.optionText}>{opt}</Text>
                  {icon && <View style={s.optionIcon}>{icon}</View>}
                </PressableCard>
              </Animated.View>
            );
          })}
        </View>

        {/* Explanation bubble */}
        {explanation !== '' && showCorrect && (
          <View style={s.explanationBubble}>
            <Ionicons name="bulb" size={16} color="#EA580C" />
            <Text style={s.explanationText}>{explanation}</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: PAPER },
  ruledBg: { ...StyleSheet.absoluteFillObject },
  ruled: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(90,150,210,0.10)' },
  margin: { position: 'absolute', left: 44, top: 0, bottom: 0, width: 1.5, backgroundColor: 'rgba(200,55,55,0.12)' },

  // ─── Select Screen ───
  selectScroll: { paddingBottom: 40 },
  selectHeader: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    paddingHorizontal: 20, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 10 : 54,
    paddingBottom: 12,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 19,
    borderWidth: 2, borderColor: INK, backgroundColor: '#FFFCF2',
    justifyContent: 'center', alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  selectTitle: { fontSize: 24, fontWeight: '900', color: INK, letterSpacing: -0.5 },
  selectSubtitle: { fontSize: 12, color: '#8A7558', fontStyle: 'italic', fontFamily: SERIF },

  domainGrid: { paddingHorizontal: 16, gap: 12 },
  domainCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderRadius: 14,
    padding: 18, flexDirection: 'row', alignItems: 'center', gap: 14,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 4 },
    }),
  },
  domainIconWrap: { width: 50, height: 50, borderRadius: 25, justifyContent: 'center', alignItems: 'center' },
  domainName: { fontSize: 16, fontWeight: '800', flex: 1 },
  domainCount: { fontSize: 11, color: '#8A7558', position: 'absolute', right: 18, bottom: 8 },
  domainBadge: {
    paddingHorizontal: 12, paddingVertical: 5, borderRadius: 6, borderWidth: 1.5,
  },
  domainBadgeText: { fontSize: 10, fontWeight: '900', letterSpacing: 2 },

  // ─── Quiz Screen ───
  quizHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 8 : 50,
    paddingBottom: 10,
  },
  quizHeaderCenter: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  qProgress: { fontSize: 14, fontWeight: '800', color: INK, letterSpacing: 1 },
  timerWrap: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  timerText: { fontSize: 14, fontWeight: '800', color: INK },

  timerBarBg: { height: 4, backgroundColor: '#E6D5B8', marginHorizontal: 16, borderRadius: 2, overflow: 'hidden' },
  timerBarFill: { height: '100%', borderRadius: 2 },

  progressDots: { flexDirection: 'row', justifyContent: 'center', gap: 8, paddingVertical: 14 },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#E6D5B8', borderWidth: 1.5, borderColor: '#C4AA78' },
  dotCurrent: { backgroundColor: ACCENT, borderColor: INK, transform: [{ scale: 1.2 }] },
  dotCorrect: { backgroundColor: GREEN, borderColor: GREEN },
  dotWrong: { backgroundColor: RED, borderColor: RED },

  questionScroll: { paddingHorizontal: 16, paddingBottom: 40 },
  questionCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderTopLeftRadius: 4, borderTopRightRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 4,
    padding: 20, marginBottom: 20,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 4 }, shadowOpacity: 0.8, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  qNumBadge: {
    position: 'absolute', top: -12, left: 16,
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK, borderRadius: 4,
    paddingHorizontal: 10, paddingVertical: 3,
  },
  qNumText: { fontSize: 11, fontWeight: '900', color: INK, letterSpacing: 1 },
  questionText: { fontSize: 18, fontWeight: '700', color: INK, lineHeight: 28, marginTop: 8, fontFamily: SERIF },

  optionsWrap: { gap: 10 },
  option: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: '#C4AA78',
    borderRadius: 12, padding: 14,
  },
  optionSelected: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(37,99,235,0.08)', borderWidth: 2, borderColor: BLUE,
    borderRadius: 12, padding: 14,
  },
  optionCorrect: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(5,150,105,0.08)', borderWidth: 2.5, borderColor: GREEN,
    borderRadius: 12, padding: 14,
  },
  optionWrong: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(220,38,38,0.06)', borderWidth: 2.5, borderColor: RED,
    borderRadius: 12, padding: 14,
  },
  optionLetter: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: '#F3EACD', borderWidth: 1.5, borderColor: '#C4AA78',
    justifyContent: 'center', alignItems: 'center',
  },
  optionLetterText: { fontSize: 14, fontWeight: '800', color: INK },
  optionText: { fontSize: 15, fontWeight: '600', color: INK, flex: 1 },
  optionIcon: { marginLeft: 'auto' },

  // ─── Result Screen ───
  resultScroll: { paddingHorizontal: 20, paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight || 40) + 20 : 60, paddingBottom: 40, alignItems: 'center' },
  resultCard: {
    backgroundColor: '#FFFCF2', borderWidth: 2.5, borderColor: INK, width: '100%',
    borderTopLeftRadius: 4, borderTopRightRadius: 20, borderBottomLeftRadius: 20, borderBottomRightRadius: 4,
    padding: 24, alignItems: 'center',
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 4, height: 5 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 10 },
    }),
  },
  resultStamp: {
    position: 'absolute', top: 12, right: 12,
    borderWidth: 2, borderColor: GREEN, borderRadius: 3,
    paddingHorizontal: 10, paddingVertical: 4, opacity: 0.6,
    transform: [{ rotate: '-5deg' }],
  },
  resultStampText: { fontSize: 9, fontWeight: '900', color: GREEN, letterSpacing: 2 },

  scoreCircle: { marginVertical: 20 },
  scoreInner: {
    width: 100, height: 100, borderRadius: 50,
    borderWidth: 4, justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#FFFCF2',
  },
  scoreNum: { fontSize: 36, fontWeight: '900', color: INK },
  scoreOf: { fontSize: 14, color: '#8A7558', fontWeight: '600' },
  gradeText: { fontSize: 18, fontWeight: '800', color: INK, marginBottom: 16 },

  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, width: '100%' },
  statBox: {
    width: '47%', backgroundColor: '#F3EACD', borderRadius: 10, borderWidth: 1.5, borderColor: '#E6D5B8',
    padding: 14, alignItems: 'center', gap: 4,
  },
  statNum: { fontSize: 22, fontWeight: '900', color: INK },
  statLabel: { fontSize: 10, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase' },

  retryBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: ACCENT, borderWidth: 2, borderColor: INK,
    paddingHorizontal: 24, paddingVertical: 12, borderRadius: 10, marginTop: 8,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 3, height: 3 }, shadowOpacity: 1, shadowRadius: 0 },
      android: { elevation: 6 },
    }),
  },
  retryBtnText: { fontSize: 15, fontWeight: '800', color: INK },
  changeDomainBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 14 },
  changeDomainText: { fontSize: 13, fontWeight: '700', color: BLUE },
  backHomeBtn: { marginTop: 10 },
  backHomeText: { fontSize: 13, color: '#8A7558' },

  // ─── Explanation ───
  explanationBubble: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    backgroundColor: '#FFF7ED', borderWidth: 1.5, borderColor: '#EA580C30',
    borderRadius: 10, padding: 12, marginTop: 12,
  },
  explanationText: { fontSize: 13, color: '#4A3520', lineHeight: 19, flex: 1, fontStyle: 'italic' },

  // ─── History Button ───
  historyBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginHorizontal: 20, marginBottom: 16, paddingVertical: 10, paddingHorizontal: 14,
    backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: BLUE + '30',
    borderRadius: 10,
  },
  historyBtnText: { fontSize: 13, fontWeight: '700', color: BLUE, flex: 1 },

  // ─── Your Stats ───
  yourStats: {
    flexDirection: 'row', marginHorizontal: 20, marginBottom: 18,
    backgroundColor: '#FFFCF2', borderWidth: 2, borderColor: INK,
    borderRadius: 12, padding: 14,
    ...Platform.select({
      ios: { shadowColor: INK, shadowOffset: { width: 2, height: 2 }, shadowOpacity: 0.6, shadowRadius: 0 },
      android: { elevation: 3 },
    }),
  },
  yourStatItem: { flex: 1, alignItems: 'center' },
  yourStatNum: { fontSize: 20, fontWeight: '900', color: INK },
  yourStatLabel: { fontSize: 9, fontWeight: '700', color: '#8A7558', letterSpacing: 1, textTransform: 'uppercase', marginTop: 2 },

  // ─── History Card ───
  historyCard: {
    backgroundColor: '#FFFCF2', borderWidth: 1.5, borderColor: '#E6D5B8',
    borderLeftWidth: 4, borderRadius: 10, padding: 14, marginBottom: 10,
  },
  historyIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  historyTitle: { fontSize: 14, fontWeight: '700', color: INK },
  historyDate: { fontSize: 11, color: '#8A7558', marginTop: 2 },
  historyGrade: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  historyGradeText: { fontSize: 14, fontWeight: '900' },
  historyMeta: { fontSize: 12, color: '#8A7558', fontWeight: '600' },
});
