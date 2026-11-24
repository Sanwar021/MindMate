import { retrieveKnowledge } from './knowledge.js';
import { findPrewrittenAnswer, qaStats } from './qa-bank.js';
const OLLAMA_URL=process.env.OLLAMA_URL||'http://127.0.0.1:11434';
const MODEL=process.env.OLLAMA_MODEL||'qwen2.5:3b';
const generationEnabled=process.env.ENABLE_LOCAL_GENERATION==='true';
const MINDMATE_SYSTEM_PROMPT=`You are MindMate, a supportive mental-health chatbot for Bangladeshi university students. You are an AI, not a therapist or doctor. Never diagnose or suggest medicines. Reply in the student's language: Banglish by default, Bangla script when they use Bangla script, and English when they use English. In Bangla or Banglish, address the student respectfully as "apni". Keep replies warm, calm, non-judgemental and concise (2 to 4 sentences). Reflect what the student said, ask one open question, and suggest one small practical step when it fits. Use student context such as exams, CGPA, thesis, tuition, hall life, family pressure, finances and relationships. Never provide self-harm or suicide method information. Do not invent services or claim to be a therapist.`;
export async function modelStatus(){try{const r=await fetch(`${OLLAMA_URL}/api/tags`,{signal:AbortSignal.timeout(800)});const d=await r.json();return{available:r.ok,model:MODEL,installed:(d.models||[]).some(x=>x.name===MODEL||x.name.startsWith(MODEL+':')),generationEnabled,qaBank:qaStats}}catch{return{available:false,model:MODEL,installed:false,generationEnabled,qaBank:qaStats}}}
const bangla=text=>/[\u0980-\u09FF]/.test(text),banglish=text=>/\b(amar|ami|onek|mon|bhalo|lage|porashona|ghum|tension|ki korbo)\b/i.test(text);
const bnAnswers={sleep:'প্রতিদিন প্রায় একই সময়ে ঘুম থেকে উঠুন, সকালে আলোতে থাকুন, বিকেল বা রাতে ক্যাফেইন এড়িয়ে চলুন এবং ঘুমের আগে শান্ত একটি ছোট রুটিন রাখুন। সমস্যা দীর্ঘস্থায়ী হলে চিকিৎসকের সঙ্গে কথা বলুন।',anxiety:'দুশ্চিন্তার ঢেউ এলে চার গুনে ধীরে শ্বাস নিন এবং ছয় গুনে ছাড়ুন—পাঁচবার। সমস্যা দীর্ঘস্থায়ী হলে যোগ্য পেশাজীবীর সহায়তা নিন।','exam-stress':'পরীক্ষার চাপ কমাতে পরবর্তী ২০–২৫ মিনিটের একটি ছোট কাজ বেছে নিন। ফোনের নোটিফিকেশন বন্ধ রাখুন, তারপর পাঁচ মিনিট বিরতি নিন।','low-mood':'পানি পান, খাবার, দিনের আলো বা অল্প হাঁটার মতো একটি ছোট কাজ দিয়ে শুরু করুন এবং একজন বিশ্বস্ত মানুষকে জানান। দুই সপ্তাহের বেশি থাকলে পেশাদার সহায়তা নিন।'};
const banglishAnswers={sleep:'Protodin motamuti eki shomoy ghum theke uthar cheshta korun, sokaler alo nin, bikel-er por caffeine koman, ebong ghum-er age phone dure rekhe ekta shanto routine banan. Shomossha dirghodin thakle doctor ba counsellor-er sathe kotha bolun.',anxiety:'Dushchinta bere gele 4 count-e shash nin, 6 count-e chere din—5 bar. Tarpor dekha 5ti ebong shona 3ti jinish-er naam bolun. Shomossha dirghosthayi hole professional support nin.','exam-stress':'Puro syllabus ekshathe na bhebe porer 20–25 minuter ekta choto task choose korun. Notification off rakhun, tarpor 5 minute break nin.','low-mood':'Pani, khabar, diner alo ba choto walk-er moto ekta basic step diye shuru korun ebong trusted kauke bolun. Dui shoptaher beshi thakle professional support nin.'};
const source=(id,title)=>[{id,title}];
function greetingReply(message){
  const text=String(message||'').trim();
  if(!/^(hi|hello(?:\s+there)?|hey|good\s+(morning|afternoon|evening)|assalamu\s+alaikum|salam|হাই|হ্যালো|সালাম)[!.?\s]*$/iu.test(text))return null;
  if(bangla(text))return 'হ্যালো! আমি MindMate। আজ আপনার মন কেমন আছে, অথবা কোন বিষয়ে সহায়তা চান?';
  if(/assalamu\s+alaikum|salam/i.test(text))return 'Walaikum assalam! Ami MindMate. Aj apnar mon kemon ache, ba kon bishoye support chan?';
  return 'Hello! I’m MindMate. How are you feeling today, or what would you like support with?';
}
function localized(message,topic,answer){
  if(bangla(message))return bnAnswers[topic]||'বিষয়টি আপনার জন্য কঠিন মনে হচ্ছে। আজ চাপটা একটু কমাতে আপনি কোন একটি ছোট ও বাস্তবসম্মত পদক্ষেপ নিতে পারেন? সমস্যা চলতে থাকলে একজন বিশ্বস্ত মানুষ বা যোগ্য পেশাজীবীর সঙ্গে কথা বলুন।';
  if(banglish(message))return banglishAnswers[topic]||'Bishoyta apnar jonno kothin mone hocche. Aj chaapta ektu komate apni kon ekta choto o practical step nite paren? Shomossha cholte thakle ekjon trusted manush ba qualified professional-er sathe kotha bolun.';
  return answer;
}
function reviewedFallback(message,sources){if(!sources.length)return bangla(message)?'এই প্রশ্নের জন্য আমার কাছে পর্যাপ্ত যাচাই করা তথ্য নেই। রোগ নির্ণয়, ওষুধ বা জরুরি সিদ্ধান্তের জন্য যোগ্য পেশাজীবীর সঙ্গে কথা বলুন।':banglish(message)?'Ei proshner jonno amar kache enough reviewed information nei. Diagnosis, medicine ba emergency decision-er jonno qualified professional-er sathe kotha bolo.':'I do not have enough reviewed information for that question. I can help with student stress, study pressure, sleep, anxiety, low mood, relationships, family or financial pressure, screening, privacy, and MindMate.';return localized(message,sources[0].id,sources.map(s=>s.content).join('\n\n'))}
export async function answerWithKnowledge({message,history=[]}){
  const greeting=greetingReply(message);
  if(greeting)return{reply:greeting,sources:[],engine:'conversation-rule',model:null};
  const ready=findPrewrittenAnswer(message);
  if(ready)return{reply:localized(message,ready.topic,ready.answer),sources:source(ready.topic,ready.topic.replaceAll('-',' ')),engine:'prewritten-qa',model:null,qaId:ready.id,confidence:ready.score};
  const sources=retrieveKnowledge(message);
  if(sources.length||!generationEnabled)return{reply:reviewedFallback(message,sources),sources:sources.map(({id,title})=>({id,title})),engine:'knowledge-retrieval',model:null};
  const status=await modelStatus();if(!status.available||!status.installed)return{reply:reviewedFallback(message,sources),sources:[],engine:'knowledge-retrieval',model:null};
  const system=MINDMATE_SYSTEM_PROMPT;
  const recent=history.slice(-4).map(x=>({role:x.role==='assistant'?'assistant':'user',content:String(x.content).slice(0,800)}));
  try{const r=await fetch(`${OLLAMA_URL}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:MODEL,stream:false,options:{temperature:.2,num_predict:100},messages:[{role:'system',content:system},...recent,{role:'user',content:message}]}),signal:AbortSignal.timeout(8000)});if(!r.ok)throw new Error();const d=await r.json();return{reply:d.message?.content?.trim()||reviewedFallback(message,[]),sources:[],engine:'ollama-fallback',model:MODEL}}catch{return{reply:reviewedFallback(message,[]),sources:[],engine:'knowledge-retrieval',model:null}}
}
