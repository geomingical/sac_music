# 花蓮地震微地動音樂化 (sac_music)

將 2024-04-03 花蓮 M7.2 地震當天的微地動訊號與氣象資料，轉化為 3 分鐘的音樂作品。

## 試聽

`output/` 資料夾內有 5 種風格的 MP3 與 MIDI 檔案，可直接下載試聽。

## 因子對照表

### 微地動（SAC 波形）→ 旋律與節奏

微地動是音樂的**主角**，控制了你聽到的旋律走向和節奏密度。

| 物理量 | 控制的音樂元素 | 對應方式 |
|--------|--------------|----------|
| **波形包絡線振幅** | 旋律音高 | 振幅小 → 低音（C3 附近）；振幅大 → 高音（Bb4） |
| **波形包絡線振幅** | 旋律力度 | 振幅小 → 輕柔（velocity 30）；振幅大 → 強烈（velocity 120） |
| **STA/LTA 事件偵測** | 鼓組觸發 | 偵測到地震波能量突變時觸發打擊 |
| **事件強度** | 鼓的種類與力度 | 弱事件 → 輕拍；中事件 → 中擊；強事件 → 重擊 |
| **事件密度** | 鼓組節奏疏密 | 安靜時段幾乎無事件；地震時大量事件密集觸發 |

**STA/LTA 觸發器**：Short-Term Average / Long-Term Average，地震學標準的事件偵測演算法。當短期平均能量相對長期平均突然升高（比值 > 5.0），判定為一個地震事件。

### 氣象因子（CSV）→ 背景氛圍

氣象資料是**配角**，提供緩慢變化的情緒底色，每小時更新一次。

| 氣象參數 | 控制的音樂元素 | 對應方式 |
|----------|--------------|----------|
| **氣壓 (StnPres)** | Pad 和弦選擇 | 5 種氣壓區間 → 5 種不同和弦，氣壓高低改變和聲色彩 |
| **風速 (WS)** | Pad 力度 | 風大 → 和弦更響亮；無風 → 幾乎聽不到 |
| **溫度 (Temperature)** | Pad 音域 | 低於 7°C → 和弦降一個八度，聽起來更低沉陰暗 |

### 時間軸 → 敘事結構

24 小時壓縮為 180 秒（3 分鐘），形成三段式故事：

```
時間軸（音樂秒數）
0s ─────────── 55s ──── 60s ────────────── 120s ──────── 180s
│   寧靜前奏    │ 漸入 │     地震爆發        │  餘震消退   │
│               │      │                     │             │
│ 稀疏旋律      │ 鼓漸 │  全力旋律+密集鼓     │ 旋律漸弱    │
│ 輕柔 Pad     │  入  │  正常 Pad           │ Pad 衰減    │
│ 無鼓組        │      │                     │ 淡出        │
│               │      │                     │             │
│ 對應真實時間：  │      │                     │             │
│ 00:00~07:53   │      │ 07:58~15:58         │ 16:00~24:00 │
│ (地震前的平靜)  │      │ (主震+密集餘震)       │ (逐漸平息)   │
```

- **地震發生時刻**：UTC+8 07:58:11 ≈ 音樂第 59.8 秒
- **淡入**：開頭 3 秒
- **淡出**：結尾 5 秒

## 五種風格

| 風格 | 檔名 | BPM | 旋律音色 | Pad 音色 | 打擊樂器 | 調性 |
|------|------|-----|---------|---------|---------|------|
| Dark Ambient | `dark_ambient_hualien` | 90 | 鋼琴 | Warm Pad | Kick/Snare/Hihat | C 小調五聲 |
| Ethereal | `ethereal_hualien` | 72 | 鐘琴 | 弦樂合奏 | 三角鐵 | D 大調五聲 |
| Cinematic | `cinematic_hualien` | 85 | 弦樂合奏 | 法國號 | 定音鼓/大鼓 | A 小調 |
| Lo-fi Chill | `lofi_chill_hualien` | 70 | 電鋼琴 Rhodes | Warm Pad | 刷鈸/輕鼓 | Eb 大調五聲 |
| Glitch | `glitch_hualien` | 110 | 鋸齒波合成器 | New Age Pad | 電子鼓+拍手 | C 全音階 |

所有風格共享相同的核心邏輯：微地動控制旋律/節奏、氣象控制氛圍、三段式敘事弧線。差異在於音色、調性、速度和打擊樂器的選擇。

## 資料來源

### 地震波形

- **測站**：TQ07（臺灣寬頻地震觀測網）
- **分量**：HHZ（高增益、高取樣率、垂直分量）
- **取樣率**：100 Hz
- **時間範圍**：2024-04-03 全天（UTC+8 00:00–24:00）
- **格式**：SAC (Seismic Analysis Code)
- **來源**：[GEOFON GFZ — TQ Network](https://geofon.gfz.de/waveform/archive/network.php?ncode=TQ)
- **引用**：GEOFON Data Centre (1993): GEOFON Seismic Network. Deutsches GeoForschungsZentrum GFZ. https://doi.org/10.14470/TR560404

### 氣象資料

- **測站**：C0H9C0（中央氣象署自動氣象站）
- **時間解析度**：逐時
- **參數**：氣壓、溫度、相對溼度、風速、風向、陣風、降水量
- **來源**：[中央氣象署觀測資料查詢系統 (CODiS)](https://codis.cwa.gov.tw/)

### 音色庫

- **SoundFont**：[GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS)（S. Christian Collins, 免費開源）

## 自行生成

如需從原始資料重新生成音樂，需自備以下檔案（因體積過大未納入版本控制）：

- `TQ07_HHZ_20240403_UTC8.sac` — 可透過 `download_TQ07.py` 從 GEOFON 下載
- `C0H9C0-2024-04-03.csv` — 可從 CODiS 查詢系統下載
- `soundfonts/GeneralUser-GS.sf2` — 可從 [GitHub](https://github.com/mrbumpy409/GeneralUser-GS) 下載

```bash
# 安裝依賴（需要 conda seismo 環境）
conda run -n seismo pip install obspy numpy scipy pretty_midi pyfluidsynth soundfile

# 生成所有 5 種風格
conda run -n seismo python3 seismic_music.py
```

輸出至 `output/` 資料夾（每種風格各一個 `.mid` 和 `.wav`）。

## 授權

音樂輸出基於公開地球科學資料生成，可自由使用。原始地震資料受 [GEOFON 資料政策](https://geofon.gfz.de/waveform/archive/datapolicy.php) 約束。
