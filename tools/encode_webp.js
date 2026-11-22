#!/usr/bin/env node
// PNG -> WebP(libwebp経由のsharp)。同じ見た目で PIL より軽くなる設定:
//   smartSubsample(色のにじみを抑える) + alphaQuality 70(輪郭のやわらかい透明は少し粗くても見えない) + effort 6
// 使い方: node tools/encode_webp.js in.png out.webp [quality=80] [alphaQuality=70]
const sharp = require('sharp'), fs = require('fs');
const [, , inp, out, q = '80', aq = '70'] = process.argv;
sharp(inp).webp({ quality: +q, alphaQuality: +aq, effort: 6, smartSubsample: true }).toBuffer()
  .then(b => { fs.writeFileSync(out, b); console.log(b.length); })
  .catch(e => { console.error(e.message); process.exit(1); });
