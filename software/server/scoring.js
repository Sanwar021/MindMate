export const clamp = (n, min, max) => Math.max(min, Math.min(max, Number(n) || 0));

export function scoreAssessment(payload = {}) {
  const phq = (payload.phq || []).slice(0, 9).map(v => clamp(v, 0, 3));
  const gad = (payload.gad || []).slice(0, 7).map(v => clamp(v, 0, 3));
  const pssRaw = (payload.pss || []).slice(0, 4).map(v => clamp(v, 0, 4));
  while (phq.length < 9) phq.push(0);
  while (gad.length < 7) gad.push(0);
  while (pssRaw.length < 4) pssRaw.push(0);
  const phq9 = phq.reduce((a, b) => a + b, 0);
  const gad7 = gad.reduce((a, b) => a + b, 0);
  const pss4 = pssRaw[0] + (4 - pssRaw[1]) + (4 - pssRaw[2]) + pssRaw[3];
  const concern = phq[8] > 0 || phq9 >= 20 || gad7 >= 15 ? 'Higher concern' : phq9 >= 10 || gad7 >= 10 || pss4 >= 8 ? 'Elevated concern' : 'Lower concern';
  const contributors = [];
  if (Number(payload.sleepHours) < 7) contributors.push('Limited sleep');
  if (Number(payload.academicStress) >= 4) contributors.push('High academic pressure');
  if (Number(payload.financialStress) >= 4) contributors.push('Financial stress');
  if (Number(payload.familyPressure) >= 4) contributors.push('Family pressure');
  if (payload.support === 'isolated') contributors.push('Limited emotional support');
  return { phq9, gad7, pss4, concern, contributors, selfHarmItem: phq[8] };
}

const highRisk = [
  /\b(kill myself|end my life|suicide|want to die|hurt myself|self[- ]?harm|no reason to live)\b/i,
  /(মরে যেতে চাই|আত্মহত্যা|নিজেকে মেরে|বাঁচতে চাই না|নিজের ক্ষতি)/i,
  /\b(morte chai|more jete chai|atmahotya|bach?te chai na|nijeke mere|end kore dite chai)\b/i
];
const distress = /\b(hopeless|overwhelmed|panic|depressed|anxious|stressed|lonely|can't cope|cannot cope)\b|হতাশ|একাকী|দুশ্চিন্তা|চাপ|ভালো লাগে না|stress|tension/i;

export function detectRisk(text = '') {
  const normalized = String(text).trim();
  if (highRisk.some(r => r.test(normalized))) return { level: 'crisis', confidence: 'rule-triggered', reason: 'Possible self-harm or suicide-related language' };
  if (distress.test(normalized)) return { level: 'distress', confidence: 'rule-triggered', reason: 'Distress-related language' };
  return { level: 'routine', confidence: 'rule-triggered', reason: 'No explicit crisis phrase detected' };
}

export function crisisReply(message = '') {
  if (/[ঀ-৿]/.test(message)) return 'আপনি আমাকে বলেছেন—এটার জন্য ধন্যবাদ। আপনার নিরাপত্তা এখন সবার আগে, আর আমি একা আপনাকে নিরাপদ রাখতে পারব না। এখনই বিপদের আশঙ্কা থাকলে ৯৯৯-এ কল করুন বা নিকটস্থ জরুরি বিভাগে যান। কাছের একজন বিশ্বস্ত মানুষকে এখনই জানান ও তার সঙ্গে থাকুন, ক্ষতি করতে ব্যবহার করা যায় এমন জিনিস থেকে দূরে যান, এবং কান পেতে রই (09612-119911), মনের যত্ন (09643-262626), মাইন্ডস্পেস ভেন্ট (09678-678-778), বা বিশ্ববিদ্যালয়ের কাউন্সেলিং সেন্টারে যোগাযোগ করুন। আপনি সাহায্যের জন্য যোগাযোগ করার সময় আমি এখানে আছি—আপনি কি এই মুহূর্তে তাৎক্ষণিক বিপদে আছেন?';
  if (/\b(ami|amar|apni|morte|more|nijeke|bachte|chai|onek|mon|kharap)\b/i.test(message)) return 'Apni amake bolechen—etar jonno dhonnobad. Apnar nirapotta ekhon shobar age, ar ami eka apnake nirapod rakhte parbo na. Ekhon-i bipoder ashonka thakle 999-e call korun ba kacher emergency department-e jan. Kacher ekjon bishshosto manushke ekhon-i janan o tar sathe thakun, nijeke khoti korte bebohar kora jay emon jinish theke dure jan, ebong Kaan Pete Roi (09612-119911), Moner Jotno (09643-262626), Mindspace VENT (09678-678-778), ba university counselling centre-e jogajog korun. Apni help-er jonno jogajog korar shomoy ami ekhane achi—apni ki ei muhurte immediate danger-e achen?';
  return 'I’m really glad you told me. Your safety comes first, and I cannot keep you safe on my own. If you may act soon or are in immediate danger, call 999 or go to the nearest emergency department now. Please contact someone you trust and stay with them, move away from anything you could use to hurt yourself, and call Kaan Pete Roi (09612-119911), Moner Jotno (09643-262626), Mindspace VENT (09678-678-778), or your university counselling centre. I’ll stay here while you reach out—are you in immediate danger right now?';
}
