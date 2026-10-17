# ちびモンスター けいさんクエスト

4〜6歳向けの計算ゲーム。モンスターを育てて(90秒)ボスを倒す、ローグライク風。
ブラウザだけで動く単体のHTML(素材を埋め込み済み)です。

## 遊び方
`index.html` をブラウザで開く。iPad/iPhone は横向き推奨。GitHub Pages に置けばURLで遊べます。

## 主な仕様
- 子ども2人分のプロフィール(ガチャ・ずかん・コイン・進行が別々)。記録はブラウザの localStorage に保存。
- むずかしさ: ようちえん / しょうがく1ねんせい
- 育成90秒(武器→進化→防具) → ボス戦60秒。ステージ26面(通常13+裏13)
- ドリルでコイン、ガチャ(ハズレなし)で仲間・装備・おまもり・ステッカー
- 問題は読み上げ(Web Speech API)。助詞「は」は「わ」で読ませています
- Safari対策: 画面を離れて戻ったとき、BGM/効果音を復帰(`wake()` と `visibilitychange`)

## 開発
```
python3 tools/build.py   # src/ と assets/ から index.html を生成
```
- `src/game.src.html` ゲーム本体(HTML/CSS/JS)
- `src/atlas.json` 画像シートの切り出し座標
- `assets/` 画像(WebP)・背景・効果音・BGM

## 音源について
BGM・効果音は、購入した素材のため **このリポジトリには含めていません**(無音で動きます)。
音を入れるには `assets/se/*.mp3`(16個)と `assets/bgm/{home,training,boss}.mp3` を置いて `python3 tools/build.py` を実行します。
ファイル名は `tools/build.py` の `SE` リストを参照。

## 素材について
画像はAI生成です。
