const topics = [
  ['exam-stress','exam stress','exam-er pressure','পরীক্ষার চাপ','Break the workload into one 20–25 minute task, silence notifications, then take a five-minute break. Prioritize the nearest deadline and protect your sleep.'],
  ['concentration','difficulty concentrating','porashonay mon na bosha','পড়াশোনায় মন না বসা','Make the starting step very small: open the material, choose one section, and work for ten minutes. Keep the phone out of reach and seek assessment if concentration problems are severe or persistent.'],
  ['procrastination','procrastination','kaj fele rakha','কাজ ফেলে রাখা','Procrastination often comes from overwhelm or fear, not laziness. Define a two-minute first action and start before waiting for motivation.'],
  ['sleep','sleep problems','ghum-er shomossha','ঘুমের সমস্যা','Keep a consistent wake time, get morning light, reduce late caffeine, and use a quiet screen-free wind-down routine. Persistent insomnia or breathing pauses need medical advice.'],
  ['anxiety','anxiety and worry','dushchinta o tension','দুশ্চিন্তা ও উদ্বেগ','Breathe in gently for four counts and out for six, five times. Ground yourself with what you can see, feel, and hear. Persistent anxiety deserves professional support.'],
  ['panic','panic symptoms','panic ba buk dhorfor','প্যানিক বা বুক ধড়ফড়','Move somewhere safe and breathe slowly without forcing deep breaths. New chest pain, fainting, or severe breathing difficulty requires urgent medical evaluation.'],
  ['low-mood','low mood','mon kharap','মন খারাপ','Start with one basic action such as water, food, daylight, or a short walk, and tell a trusted person. Symptoms lasting two weeks or affecting daily life deserve professional assessment.'],
  ['loneliness','loneliness','eka laga','একাকীত্ব','Choose one low-pressure connection: message a trusted person, sit in a shared space, or join a class activity. You can simply say that you have had a difficult week and need company.'],
  ['family-pressure','family pressure','family-r pressure','পারিবারিক চাপ','Choose a calm time, explain the specific pressure and its effect, and make one concrete request. A trusted relative, teacher, or counsellor can help mediate.'],
  ['financial-stress','financial stress','taka ba tuition-er tension','আর্থিক চাপ','List urgent costs, identify what can wait, and ask the university about instalments, waivers, scholarships, emergency funds, or student work. Avoid risky loans made under pressure.'],
  ['career-anxiety','career anxiety','career niye tension','ক্যারিয়ার নিয়ে দুশ্চিন্তা','Separate what you can control this week from long-term uncertainty. Choose one practical action: update your CV, contact an adviser, or practise one relevant skill.'],
  ['relationship','relationship problems','relationship-er shomossha','সম্পর্কের সমস্যা','Pause impulsive messaging, keep basic routines, and talk with someone calm. Respect consent and boundaries; threats, stalking, or coercion require outside help.'],
  ['breakup','coping with a breakup','breakup-er por mon kharap','ব্রেকআপের পর মন খারাপ','Reduce repeated checking and impulsive contact, stay close to supportive people, and keep sleep and meals regular. Healing is gradual; seek help if functioning or safety deteriorates.'],
  ['harassment','bullying or harassment','bullying ba ragging','বুলিং বা হয়রানি','Move toward safety, preserve evidence when safe, tell a trusted person, and use the university safeguarding process. Do not confront a threatening person alone.'],
  ['grief','grief and loss','shok ba priyojon harano','শোক বা প্রিয়জন হারানো','Grief can affect sleep, appetite, concentration, and emotion. Accept practical help, maintain basic routines, and seek support if distress becomes unmanageable.'],
  ['anger','anger management','rag control','রাগ নিয়ন্ত্রণ','Pause the interaction, create distance from risky objects, cool your body with water and slow breathing, and return only when you can speak without threats.'],
  ['social-media','social media stress','social media-r pressure','সোশ্যাল মিডিয়ার চাপ','Mute stressful accounts, set specific check times, and avoid comparing your private life with other people’s highlights. Replace one scrolling period with sleep, movement, or real connection.'],
  ['homesickness','homesickness','bari-r jonno mon kharap','বাড়ির জন্য মন খারাপ','Keep regular contact with home while building one routine and one connection where you live now. Familiar food, language, prayer, or community activities can create stability.'],
  ['substances','smoking caffeine or substances','cigarette caffeine ba nesha','সিগারেট ক্যাফেইন বা নেশা','Caffeine, nicotine, alcohol, and other substances can worsen sleep and anxiety. Track amount and timing, reduce carefully, and seek medical help for dependence or withdrawal.'],
  ['self-care','daily self care','daily nijer jotno','দৈনন্দিন নিজের যত্ন','Build a simple baseline: regular food and water, daylight, movement, a consistent wake time, one connection, and one manageable task.'],
  ['professional-help','getting professional help','counsellor-er help','পেশাদার সহায়তা','Seek professional support when distress lasts, worsens, disrupts study or relationships, or affects safety. MindMate supports screening and education but does not diagnose or prescribe.'],
  ['phq9','PHQ-9 score','PHQ-9 score-er meaning','PHQ-৯ স্কোর','PHQ-9 is a nine-item depression symptom screening tool for the previous two weeks. It is not a diagnosis, and any response to the self-harm item needs prompt human follow-up.'],
  ['gad7','GAD-7 score','GAD-7 score-er meaning','GAD-৭ স্কোর','GAD-7 is a seven-item anxiety symptom screening tool. The score describes symptom burden but must be interpreted with functioning, context, and duration.'],
  ['pss4','PSS-4 stress score','PSS-4 score-er meaning','PSS-৪ স্ট্রেস স্কোর','PSS-4 is a brief perceived-stress measure for the last month. It helps track stress but is not a diagnostic test.'],
  ['privacy','MindMate privacy','MindMate data privacy','মাইন্ডমেটের গোপনীয়তা','This prototype stores data on the server computer. Real student deployment requires informed consent, encryption, retention and deletion controls, audit logging, restricted roles, and ethics approval.']
];

const enTemplates=['What should I do about {x}?','How can I manage {x}?','Can you help me with {x}?','Give me advice for {x}.','What are practical steps for {x}?','How do students cope with {x}?','I am struggling with {x}.','Please explain how to handle {x}.'];
const blTemplates=['Amar {x}, ki korbo?','{x} kivabe manage korbo?','{x} niye help chai.','{x} komanor upay ki?','Student hisebe {x} handle korbo kivabe?','{x} er jonno practical tips dao.'];
const bnTemplates=['আমার {x}, কী করব?','{x} কীভাবে সামলাব?','{x} নিয়ে সাহায্য চাই।','{x} কমানোর উপায় কী?','শিক্ষার্থী হিসেবে {x} কীভাবে মোকাবিলা করব?','{x} এর জন্য বাস্তব পরামর্শ দিন।'];
export const qaBank=topics.flatMap(([topic,en,bl,bn,answer])=>[
  ...enTemplates.map((t,i)=>({id:`${topic}-en-${i+1}`,topic,language:'en',question:t.replace('{x}',en),answer})),
  ...blTemplates.map((t,i)=>({id:`${topic}-bl-${i+1}`,topic,language:'bl',question:t.replace('{x}',bl),answer})),
  ...bnTemplates.map((t,i)=>({id:`${topic}-bn-${i+1}`,topic,language:'bn',question:t.replace('{x}',bn),answer}))
]);
const normalize=text=>String(text).toLowerCase().normalize('NFKC').replace(/-/g,' ').replace(/[^\p{L}\p{M}\p{N}\s]/gu,' ').replace(/\s+/g,' ').trim();
const stop=new Set(['a','an','the','i','me','my','is','are','do','does','can','could','please','what','how','with','for','about','give','tell','help','should','manage','handle','practical','steps','student','students','struggling','amar','ami','ki','korbo','kivabe','niye','chai','dao','er','jonno','hisebe','upay','komabo','না','কী','আমার','আমি','নিয়ে','জন্য','কীভাবে','করব','চাই','দিন','উপায়']);
const tokenSet=text=>new Set(normalize(text).split(' ').filter(x=>x.length>1&&!stop.has(x)));
const indexed=qaBank.map(item=>({...item,normalized:normalize(item.question),tokens:tokenSet(item.question)}));
const exact=new Map(indexed.map(item=>[item.normalized,item]));
const cache=new Map();
export function findPrewrittenAnswer(query){const key=normalize(query);if(cache.has(key))return cache.get(key);if(exact.has(key)){const hit={...exact.get(key),score:1};cache.set(key,hit);return hit}const q=tokenSet(query);let best=null,bestScore=0;for(const item of indexed){let overlap=0;q.forEach(t=>{if(item.tokens.has(t))overlap++});const score=overlap/Math.max(2,Math.min(q.size,item.tokens.size));if(score>bestScore){bestScore=score;best=item}}const result=bestScore>=.34?{...best,score:bestScore}:null;if(cache.size>1000)cache.clear();cache.set(key,result);return result}
export const qaStats={count:qaBank.length,topics:topics.length,languages:['en','bl','bn']};
export const topicCatalog=topics.map(([id,title])=>({id,title,example:`How can I manage ${title}?`}));
