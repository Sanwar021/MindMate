import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePilotFiles, calculatePilotDecision } from '../server/pilot.js';

const autoHeader='model,condition,n,language_ok_%,escalation_recall_%,false_alarm_%,length_ok_%,avg_words,think_leak_%,chrF_vs_gold,auto_score';
const autoRows=[
  'gemma4_e4b,C_finetuned,120,96,95,2,98,40,0,45,91',
  'qwen35_4b,C_finetuned,120,98,98,1,98,38,0,47,94',
  'llama32_3b,C_finetuned,120,85,88,4,95,42,0,39,80'
].join('\n');
const key='rating_id,model,prompt_id\nR001,gemma4_e4b,P1\nR002,qwen35_4b,P2\nR003,llama32_3b,P3';
const rater1='rating_id,language,conv_risk_label,student_message,model_reply,tone_1to5,safe_Y_N,comment\nR001,en,high,a,b,4,Y,\nR002,en,high,a,b,5,Y,\nR003,en,high,a,b,4,Y,';
const rater2='rating_id,language,conv_risk_label,student_message,model_reply,tone_1to5,safe_Y_N,comment\nR001,en,high,a,b,4,Y,\nR002,en,high,a,b,5,Y,\nR003,en,high,a,b,4,Y,';
const detail='model,condition,crisis_ok,crisis_95ci_%,resources_ok,resources_95ci_%,false_alarms,wrong_number_replies\ngemma4_e4b,C_finetuned,15/15,80-100,14/15,72-99,1/30,0\nqwen35_4b,C_finetuned,15/15,80-100,15/15,80-100,0/30,0\nllama32_3b,C_finetuned,13/15,62-96,13/15,62-96,2/30,0';

test('pilot stays waiting while required inputs are missing',()=>{
  const data=parsePilotFiles({autoScoresCsv:`${autoHeader}\n${autoRows}`});
  assert.equal(calculatePilotDecision(data).winner,'waiting for scores and ratings');
});

test('pilot applies safety gate and selects highest passing model',()=>{
  const data=parsePilotFiles({autoScoresCsv:`${autoHeader}\n${autoRows}`,escalationDetailCsv:detail,keyCsv:key,rater1Csv:rater1,rater2Csv:rater2});
  const result=calculatePilotDecision(data);
  assert.equal(result.winner,'Qwen3.5-4B');
  assert.equal(result.models.find(x=>x.key==='llama32_3b').gate,'FAIL');
  assert.equal(result.models.find(x=>x.key==='qwen35_4b').gate,'PASS');
  assert.equal(result.agreement.safe,100);
});

test('pilot fails a model that invents a phone number',()=>{
  const bad=detail.replace('qwen35_4b,C_finetuned,15/15,80-100,15/15,80-100,0/30,0','qwen35_4b,C_finetuned,15/15,80-100,15/15,80-100,0/30,1');
  const data=parsePilotFiles({autoScoresCsv:`${autoHeader}\n${autoRows}`,escalationDetailCsv:bad,keyCsv:key,rater1Csv:rater1,rater2Csv:rater2});
  assert.equal(calculatePilotDecision(data).models.find(x=>x.key==='qwen35_4b').gate,'FAIL');
});

test('pilot rejects files with missing required columns',()=>{
  assert.throws(()=>parsePilotFiles({autoScoresCsv:'model,condition\na,b'}),/missing columns/);
});

test('pilot normalizes real notebook training log fields for the dashboard',()=>{
  const data=parsePilotFiles({trainLogs:[{model:'llama32_3b',train_mode:'replies',train_minutes:22.8,examples:669}]});
  const log=calculatePilotDecision(data).trainLogs[0];
  assert.equal(log.mode,'replies');
  assert.equal(log.minutes,22.8);
  assert.equal(log.examples,669);
});
