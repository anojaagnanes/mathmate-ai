import test from 'node:test';
import assert from 'node:assert/strict';
import {matchesLanguage,selectNarrationVoice,tamilStep} from '../src/lib/teaching-language.ts';

test('Tamil never falls back to a saved English voice',()=>{
 const en={lang:'en-US',voiceURI:'english'},ta={lang:'ta-IN',voiceURI:'tamil'};
 assert.equal(selectNarrationVoice([en,ta],'english','ta'),ta);
 assert.equal(selectNarrationVoice([en],'english','ta'),undefined);
 assert.equal(matchesLanguage('ta_LK','ta'),true);
 assert.equal(selectNarrationVoice([en,ta],'tamil','en'),en);
});
test('Clara is the default English voice when no saved voice matches',()=>{
 const boy={lang:'en-US',voiceURI:'boy',name:'Microsoft David Desktop - English (United States)'};
 const clara={lang:'en-US',voiceURI:'clara',name:'Microsoft Clara Online (Natural) - English (United States)'};
 assert.equal(selectNarrationVoice([boy,clara],'','en'),clara);
 assert.equal(selectNarrationVoice([boy,clara],'boy','en'),boy);
 assert.equal(selectNarrationVoice([boy],'','en'),boy);
 assert.equal(selectNarrationVoice([clara],'','ta'),undefined);
});
test('linear and fraction instructions are localized without changing numbers',()=>{
 assert.match(tamilStep('Subtract 6 from both sides, then collect like terms.'),/6/);
 assert.match(tamilStep('Divide both sides by 2, the nonzero coefficient of x.'),/2.*x/);
 assert.match(tamilStep('Simplify to isolate x.'),/x/);
 assert.doesNotMatch(tamilStep('Add the numerators and keep the common denominator.'),/numerators/);
 assert.match(tamilStep('Unsupported advanced operation'),/தமிழாக்கம் இன்னும் இல்லை/);
 assert.equal(tamilStep('தமிழ் விளக்கம்'),'தமிழ் விளக்கம்');
});
