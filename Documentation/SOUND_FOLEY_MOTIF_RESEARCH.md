# FrontRooms 拟音系统与 Motif 研究

2026-10-02 · 研究稿，落地方案待 Red 确认。没有改任何游戏代码。

## 0. 结论

1. **门不同步的根因不是素材，是结构。** 现在每个声音都有自己的时钟（一段固定长度的音频，或者一个固定计时器），而不是读取画面上那个运动本身的时钟。一个"开门"事件对应一整段录音，所以门只要不按录音的节奏动（半开、提前停、被撞开），声音就一定错。
2. **3A 的拟音逻辑是"游戏只报告发生了什么和动得多快，声音资产决定听起来怎样"。** 一个物体被拆成多个模块（开始 / 持续 / 停止 / 冲击），由状态变化触发、由连续参数（角度、角速度、距离）驱动。这就是你要的"模组化"：同一套门模块可以覆盖半开、全开、慢开、摔门、被 Relay 撞开。
3. **FrontRooms 的声音 DNA 已经藏在游戏里：** 120 Hz 的镇流器嗡鸣是调性，标题走廊的移动速度正好是 92 BPM（每个房间精确 16 拍）。Motif 可以完全从这两样东西里长出来，然后渗进门、钥匙、玻璃、Relay、被抓这些音效。

试听草稿在 `Verification/audio/motif-sketches/`（见第 4.5 节）。

## 1. 现状诊断：为什么"经不起推敲"

### 1.1 门：声音比动作长 3–6 倍

| | 动画 | 声音 |
|---|---|---|
| 地图里的门（玩家开/关） | 0.55 s，smoothstep，转 95°（`FrontRoomsMapWorld.cs:912`） | 播放整段 `door-creak.wav`：**3.16 s**，几乎全程等响（`FrontRooms3DGame.cs:560`） |
| 标题走廊的双开门 | 0.9 s，smoothstep，转 88°（`FrontRoomsRoomStream.cs:48`） | 门闩 + 3.16 s 吱呀 + 0.72 s 门体运动，**三层同时从 0 开始**；运动层在 0.58 s 就"落定"，比门真正停下早 0.32 s（`FrontRoomsRoomStream.cs:1556`） |
| 关门 | 同样的 0.55 s 曲线 | 和开门播**同一段**吱呀；`Doors.slam` 写了没接 |
| Relay 最后撞开门 | 0.18 s 甩开 | `DoorBroken` 事件**没有订阅**，最响的一下没有声音 |

其他时间问题：
- **门闩和门体同时响。** 真实顺序是：压把手 → 门闩脱开（约 80 ms）→ 门才开始转。
- **门停下的方式也不对。** smoothstep 让门以零速度停下，所以关门永远不会"撞上门框"，也就没有理由出现落锁声。这需要动画和声音一起改。
- **对象不对。** 门的设计是"刷漆层压板 + 拉手 + 三片合页 + 踢脚板 + 顶部闭门器"（`BACKROOMS_DOOR_RESEARCH.md`），这是一扇商业办公门。现在的录音是 "Creaking Door #2"，一扇老木门的鬼屋式吱呀。商业门真正的声音是：拉手弹簧、门闩咔嗒、闭门器液压的嘶声、门扇带起的风、门底扫条摩擦，关上时锁舌撞进锁扣。

### 1.2 脚步：两个时钟在打架

- **Relay 追逐时，腿和声音在漂移。** 骨骼步态是 `gaitRate 11.5 × speedScale 1.15` = 每步 0.24 s，而脚步声计时器是每 0.29 s 一步（`FrontRooms3DGame.cs:707`）。看到的落脚比听到的快约 18%。
- **Relay 撞门是有声无形。** 动作只是把手臂固定在 −42° 再加整体抖动，没有出拳的动作；声音却每 0.5 s 一下。
- **玩家脚步是固定计时器**（走 0.5 s、跑 0.3 s）。所以贴墙滑动、体力耗尽减速时，步频不会跟着变。

### 1.3 共同的根因

| 根因 | 后果 |
|---|---|
| 声音自带时钟（片段长度 / 计时器） | 动作一变化就不同步 |
| 一个事件 = 一整段音频 | 半开、中途停、被撞开都无法表达 |
| 选素材时只看"这类声音"，不看"这个物体" | 木门吱呀配给了商业门 |

## 2. 3A 的拟音逻辑是怎么搭的

### 2.1 分类沿用电影
电影拟音分三类，游戏基本照搬，再加几类：
- **Feet：** 脚步、跑、落地。
- **Moves：** 衣服和身体的摩擦。
- **Specifics：** 道具，比如钥匙、门把手。

游戏常额外分出 **Creature**（怪物身体）、**Mechanisms**（门、窗、电梯、灯）、**Ambience**（环境）。分类决定了素材怎么录、混音怎么分组。

### 2.2 中间件的通用词汇（Wwise / FMOD 都是这一套）

| 概念 | 意思 | FrontRooms 里的例子 |
|---|---|---|
| **Event** | 游戏只说"发生了什么" | `Door.Unlatch`、`Foot.Plant` |
| **Switch** | 按物体区分的离散选择 | 地面材质、角色、门的类型 |
| **State** | 全局离散状态 | Title / Explore / Hunt / Chase / Caught |
| **RTPC / Parameter** | 连续参数 | 门角度、角速度、距离、紧张度 |
| **Random Container** | 多个变体随机、避免连续重复 | 6 个落锁变体 |
| **Switch Container** | 按 Switch 选子集 | 地毯 / 地毯砖 / 金属门槛条 |
| **Blend Container** | 按参数交叉淡化多层 | 门速度：慢吱呀 ↔ 快风声 |
| **Start / Loop / Stop**（FMOD 叫 sustain point） | 机构类声音的标准结构：起、持续（随参数变）、收 | 门、电梯、拉杆 |
| **Bus / Snapshot / Voice limit** | 混音分组、状态快照、同时发声上限 | 脚步最多 4 个声部 |

Wwise 的一个要点：材质用 **Switch**（每个物体各自的），不要用 **State**（全局的）。Blend Container 可以用参数控制交叉淡化，也可以让播放位置跟着参数走，常用来做门和拉杆这类交互物。

### 2.3 三种同步（核心）
1. **接触事件：** 在运动的某个瞬间触发，比如脚落地帧、门闩脱开、门撞上门框。业界共识是用动画事件（落脚帧）代替计时器，因为计时器会随速度变化漂移。
2. **连续参数：** 声音每帧读取运动的量。Andy Farnell 的 *Designing Sound* 用 stick-slip（粘滑摩擦）模型做吱呀门：推力越大，粘滞越久，吱呀的音高越低，木门的共振用一组带通滤波器表示。所以吱呀是"运动的函数"，不是一段录音。
3. **结束状态：** 运动结束时按撞击速度选强度。BeamNG 的门锁系统是现成的参照：
   - 关门强度参数 0–1 选择轻 / 中 / 重三档素材，每档 3–4 个变体随机；
   - 同一个参数还把音量线性 +4 dB、音高 +3 半音；
   - 再按距离和朝向加滤波。

### 2.4 分工
游戏代码只负责**发布参数、发出事件**；"听起来怎样"全在声音数据里。换素材、加层、调曲线都不用动游戏代码。这是 3A 管线能模块化、能并行开发的原因，也正好接上你的 Level Designer 计划：房间是数据，声音也是数据。

## 3. 落地方案（待确认）

### 3.1 选型

| | A. 自建轻量层（推荐） | B. FMOD Studio |
|---|---|---|
| 是什么 | 在 Unity 里用 ScriptableObject 实现上面那套词汇：Event / Switch / Parameter / 容器 / Start-Loop-Stop | 行业标准中间件，有独立的编辑器 |
| WebGL | 滤波和混响在启动时**烘焙**进片段（干声 / 隔墙 / 远处），运行时只做音量交叉淡化，Mac 和 Web 听起来一致 | 自带 DSP，Web 版也能实时滤波和混响 |
| 成本 | 不用装新工具，agent 能直接写，和现有的程序化音频兼容 | 要装 FMOD Studio、接入插件、构建 bank；现在这些代码生成的声音要改成导入素材 |
| 作品集价值 | 中 | 高（简历上写 FMOD） |

我推荐 **A**，而且数据结构完全按 Wwise / FMOD 的概念命名，以后需要时可以平移到 FMOD。

### 3.2 数据模型（草案）

```
SoundEvent (ScriptableObject)
  layers[]: SoundLayer
    container: Single | Random(avoidRepeat) | Switch(key) | Blend(param)
    clips[] / children[]
    volume, pitch: base ± random, plus a curve per parameter
    start: immediate | delay | on beat (title only)
  segment: OneShot | StartLoopStop(loopParam, releaseMs)
  spatial: preset (player foley / relay / mechanism / ui)
  bus: Ambience | Hum | Foley.Player | Relay | Mechanism | Subjective | Motif | UI
  voiceLimit, cooldown, priority
```

`FoleyEmitter` 组件挂在会发声的物体上。它只做两件事：每帧发布参数（如 `openness`、`angularVelocity`），以及在状态变化时发出事件。

### 3.3 门模块：回答"半开、全开"的问题

门每帧发布的参数：`openness` 0–1、`angularVelocity`（有正负）、`latched`、`locked`、`damage` 0–1。

| 模块 | 触发条件 | 内容 | 参数怎么用 |
|---|---|---|---|
| `Door.Handle` | 玩家按 E | 拉手被压下的弹簧声 | — |
| `Door.Unlatch` | 门闩脱开（比按 E 晚约 80 ms） | 锁舌回缩的咔嗒 | 随机 4 个变体 |
| `Door.Swing`（Loop） | \|ω\| 超过阈值 | 闭门器液压声 + 门扇带风 + 粘滑吱呀颗粒 | 音量和音高跟 \|ω\|；吱呀只在中低速出现，快速时变成风声 |
| `Door.StopLimit` | 门转到 95° 极限，且 \|ω\| > 阈值 | 闭门器缓冲器（backcheck）的闷响 | 按撞击速度选轻 / 中 / 重档（BeamNG 做法） |
| `Door.StopMid` | 门停在半开位置（0.05 < openness < 0.95，\|ω\| 降到阈值以下） | 极轻的合页"咔"，或不发声 | Swing 循环在 80–120 ms 内释放 |
| `Door.LatchStrike` | openness 降到 0.02 以下，正在关 | 锁舌撞进锁扣 + 门扇拍门框 + 气压"噗" | 关门速度选档：轻扣 / 正常 / 摔门 |
| `Door.Locked` | 没钥匙时按 E | 拉手撞上锁住的锁舌，门晃一下 | 不触发 Swing |
| `Door.Blow` | Relay 每一下撞击，**对齐它出拳的那一帧** | 撞击层（必有）+ 门框震（damage > 0.3）+ 木头裂（damage > 0.6） | `damage` 逐下增加 |
| `Door.Break` | 门被撞开 | 锁舌被撕开的声音 | 门甩开时**自动**触发最重档的 `StopLimit` |

**半开的例子：** 玩家把门推到 45° 后松手：
1. `Handle`；
2. 80 ms 后 `Unlatch`；
3. `Swing` 随速度起来又落下；
4. 速度降到阈值以下，触发 `StopMid` 的轻响，Swing 释放。

之后从半开继续推：不会再有 `Unlatch`（门闩已经开了），直接 `Swing`。关门时 openness 到 0，触发 `LatchStrike`。任何轨迹都是对的，因为声音是从运动本身读出来的。

**动画需要配合的地方：**
- 开门前保留约 80–110 ms 的"脱闩停顿"。
- 关门曲线改成加速撞上门框（ease-in），而不是 smoothstep 缓停。
- 开到极限时可以加一点回弹。
- 标题走廊的双开门是两个声源，分别放在两侧合页（±1.12 m），两扇之间错开 20–40 ms。
- 标题里的门是自己打开的，合理的声音是自动门机构：继电器咔嗒 + 电机。这正好接上 Relay 和 motif。

**声学上：** `openness` 同时决定这扇门的隔声程度。Relay 的脚步隔着半开的门，比隔着关死的门清楚。

### 3.4 脚步模块
- **触发时机：**
  - Relay 从骨骼步态的相位生成落脚事件：每半个周期一次，左右交替。这样声音和腿用同一个时钟，不可能漂移。
  - 玩家按移动距离触发（步幅约 1.6 m，对应现在的步频），实际速度一变，步频就跟着变。
- **Switch：** 角色 × 地面（地毯 / Office 地毯砖 / 门洞的金属门槛条）× 步态（走 / 跑 / 急停 / 转身擦地）。
- **分层：** 脚跟、脚尖（跑）、地面纹理、衣服（Moves）。Relay 额外加它的签名层。
- **远近：** 近、中、远三个预烘焙版本按距离交叉淡化。

### 3.5 其他模块
- **玻璃：** 参数是按住 E 的进度 0–1。
  - 按住时：应力循环随进度升高。
  - 进度到 0.35 和 0.7：各一次裂纹事件。
  - 进度到 1.0：碎裂，分冲击、碎片、落地尾音、房间反射四层。
  - 中途松手：应力"回弹"的一声。
- **钥匙：** 钥匙圈的声音（Specifics），不是 UI 提示音。
- **灯：** 每盏灯发布 `level`。启辉、闪烁、熄灭都是事件，嗡鸣的音量跟着 `level` 变。
- **Relay 身体：** 状态用 Switch，接触用事件，距离、遮挡、紧张度用参数。

### 3.6 同步规则和自动测试
- **接触事件误差不超过 1 帧（约 17 ms）。** Mac 版建议把 DSP 缓冲从 1024 调成 Best latency。
- **循环层必须在运动停止后 120 ms 内释放：** 声音永远不比动作长。
- **自动测试：** autopilot 跑一局，记录每个动画接触时刻和对应的声音触发时刻，输出偏差报告。现有的音频验证只测了游戏里根本不播的旧片段。

## 4. Motif 研究与提案

### 4.1 研究要点
- **Sonic DNA：** 品牌声音由调性/音阶、乐器调色板、节奏签名、旋律 motif 组成。2–5 秒的音频 logo 从这套 DNA 里派生，再做多个变体去适配不同场景。
- **Netflix "ta-dum"：** 声音设计师 Lon Bender 做的。底子是一个拟音：婚戒敲木头床头柜。上面叠了一层重低音，结尾是一段倒放的吉他。也就是说，品牌声音可以从一个物体的声音里长出来。
- **Rez：** 所有音效（射击、爆炸）都按节拍和调性量化，跟音乐同步。音效本身就是音乐。
- **Journey：** 作曲 Austin Wintory 和声音设计 Steve Johnson 三年同步工作，玩家的"呼喊"同时是交互音效和音乐。
- **Silent Hill：** 怪物靠近时口袋收音机发出杂音。Yamaoka 认为音乐太"解释"了，于是用一个故事里真实存在的设备做预警。
- **Dead Space：** "fear emitters" 挂在敌人和物体上，靠近时恐惧值上升，四层立体声音乐按恐惧值实时混合。
- **Jaws** 的两音 motif：听到动机就等于怪物在场，不需要看见。

### 4.2 FrontRooms 的声音 DNA
- **调性：120 Hz。**
  - 美国 60 Hz 电网下，镇流器铁芯的磁致伸缩每个周期伸缩两次，所以荧光灯的嗡鸣是 120 Hz。现在代码里的 60 Hz 基频是错的。
  - 所有音高都取 120 Hz 的谐波（60 Hz 网格上的第 n 个），这样 motif 就**在嗡鸣里面**，而不是盖在它上面。
  - 换算成十二平均律，相当于 A4 = 427.6 Hz，比标准音低约半个半音。
- **速度：92 BPM。** 标题走廊每个房间 12 m，相机速度 1.15 m/s，每个房间 10.4348 s，**正好是 92 BPM 的 16 拍（4 小节）**。每一扇门都可以落在小节线上。

### 4.3 提案 A："Threshold" motif（推荐）
- **音：** 第 8、9、11 谐波，即 480 – 540 – 660 Hz。
- **音程：**
  - 先上一个全音（204 音分）。
  - 再跳到第 11 谐波：比纯四度高 51 音分，正好卡在四度和三全音**之间**，"夹在两个音之间"。阈限空间对应一个阈限音程。
- **节奏：** 短 – 短 – 长，就是一扇门的节奏：继电器/门闩 – 磁力锁脱开 – 门转到最快。
- **永不解决：** 游戏没有结局，难度一直升，motif 也从不回到主音。

**变体表（motif 怎样渗进音效）：**

| 场景 | 变体 |
|---|---|
| 标题走廊每扇门 | 门就是乐器：继电器咔嗒 = 第 1 音；磁力锁脱开 = 第 2 音；门转到最快 = 第 3 音。下一扇门"回答"时，第 3 音改落到第 7 谐波（420 Hz，自然七度） |
| 门的吱呀 | 粘滑吱呀的音高从第 9 谐波滑到第 11 谐波：吱呀本身在"唱"那个音程 |
| 捡到钥匙 | 钥匙圈声音 + 第 1、2 音（高八度），**第 3 音被扣住** |
| 用钥匙开门 | 第 3 音在门转到最快时落下，补完 motif |
| Relay | 倒置（11 – 9 – 8）、低一个八度、带 1.4 Hz 拍频的失谐。嗡鸣先熄，继电器咔嗒 |
| 打碎玻璃 | 三个音 ×4 变成玻璃共振，motif 被打碎 |
| 被抓 | 三个音一起滑进 120 Hz 的嗡鸣（和"灯"合一），然后硬切到完全寂静，再出现微弱的耳鸣 |
| 难度升级（tier） | 整个 motif 乘 9/8 上移，音程不变，"一直在升" |

### 4.4 提案 B：只有节奏
没有旋律。motif 是 3-3-2 的节奏：故障镇流器按这个节奏让嗡鸣断续，继电器咔嗒落在重音上。更克制，但辨识度比 A 低。也可以 A 给世界、B 给 Relay。

### 4.5 试听草稿（合成的示意稿，不是最终声音）
放在 `Verification/audio/motif-sketches/`，生成脚本是 `Tools/audio/motif_sketch.py`（纯 Python）。
- `01_title_loop_A_threshold_motif.wav`：两个标题房间，20.87 s，**可以无缝循环**，−20 LUFS。
  - 1.3 s：第一扇门，480 → 540 → 660。
  - 11.7 s：第二扇门回答，480 → 540 → 420。
  - 每小节的第 1、3 拍有极轻的继电器滴答。
- `02_motif_family_in_foley.wav`：21.5 s，按顺序演示：
  - 0.6 s：玩家开门，吱呀滑 9 → 11。
  - 3.0 s：钥匙，8 – 9。
  - 5.0 s：用钥匙开门，11 落下。
  - 8.0 s：Relay。
  - 12.4 s：玻璃。
  - 15.4 s：被抓，16.35 s 硬切。
- `03_title_loop_B_rhythm_only.wav`：提案 B，可循环，−20 LUFS。

### 4.6 标题循环的技术做法
- **一个"指挥"时钟：** 用 `AudioSettings.dspTime`。标题相机的位置由它算出，门在拍点上触发，motif 用 `PlayScheduled` 排程（WebGL 也支持）。现在相机位置是逐帧累加 `dt`，长时间挂在标题会和音频时钟慢慢漂开。
- **生成式，不是一个固定文件：**
  - 嗡鸣和底噪用长度互质的几层循环。
  - motif 由门事件触发，每 4 个房间换一次变体（A、A′、A、B）。
  - 这样挂多久都不会听出重复。
- **交接：** 按空格时输入立即生效，不等拍点；收尾的音按下一个八分音符排程（最多晚 326 ms）。进入游戏后，motif 退成偶发的提示，嗡鸣留下来当底。

## 5. 需要你决定
1. 选型：自建轻量层（A），还是 FMOD（B）？
2. Motif：提案 A、提案 B，还是 A 给世界、B 给 Relay？
3. 标题走廊的门设定为"自动门"（继电器 + 电机开门），可以吗？
4. 素材：先用 CC0 素材库，还是你去录商业门、地毯、荧光灯？

实施时会动到 `FrontRoomsRoomStream.cs`（视觉对话负责）和 `FrontRoomsMapWorld.cs` / `FrontRooms3DGame.cs`（地图对话负责）。动手前要先跟它们对好接口。

## 6. 更新（2026-10-02 晚）

**Red 的决定：**
- **中间件用 FMOD。** 第 3 节的数据模型和门模块直接对应 FMOD 的概念：Event、parameter sheet、sustain point、snapshot、bus。
  - 本机还没装 FMOD Studio 和 FMOD for Unity，两者都需要 Red 登录 fmod.com 下载。
  - 往 Unity 工程里加插件前，要先和视觉对话、地图对话协调。
- **第 4 节的 motif A、B 不满意。** 改为在 Logic Pro 里生成可编辑的多轨编曲。

**Logic 工程：** `AudioSource/Logic/source/FrontRooms_Motifs_v1.logicx`，由 `Tools/audio/compose_motifs.py` 生成。92 BPM，每个标题房间 4 小节；标记写在时间线上，三个候选依次排列：

| 候选 | 小节 | 核心 | 配器（全部用本机已安装的音色） |
|---|---|---|---|
| M1 ATTENTION | 1–8 | 大楼广播提示音 1-5-3-2，门声落在本该是主音的位置；每隔一个房间，最后一个铃低半音 | Delicate Bells 提示音、Deluxe Classic（Rhodes）、Simple Foundation 贝斯、Mystic Vibes、Authentic Strings、SoCal 鼓组 |
| M2 ENDLESS | 21–28 | 钢琴：5 上行小六度到 3，再叹息落到 2；嗡鸣的 B 是持续低音，旋律顶音每半个房间上移一级 | Studio Grand、Space Strings、Distant Air、Pulse Bass、80s Wave Bells |
| M3 RELAY | 41–48 | 3+3+2 模拟合成器固定音型，重音拼出 B–C–A；主旋律 5–♭6–5，再走 3–♭2–1 | Sync Lead 琶音、Pulse Bass、Analog Horns、Classic Pad、SoCal 鼓组 |

- **每个候选后面都有 4 个变体 cue：** KEY、UNLOCKED、RELAY、CAUGHT，演示同一个 motif 怎样进入音效。
- **两条占位音频：** 120 Hz 嗡鸣、门与拟音，与 MIDI 从第 1 小节对齐。
- **调音：** 在游戏里，音乐要在 FMOD 中整体降 −47 音分，才能和真实的 120 Hz 嗡鸣同音。
- **音色限制：** 真实的颤音琴、马林巴和管弦乐需要 Logic 下载 4 个缺失的音色包（约 1.5 GB），由 Red 决定是否下载。

## 7. 声音库换成真实录音（2026-10-02 夜）

### 7.1 来源
- **录音：** 20 条 Freesound 录音（18 条 CC0，2 条 CC-BY），加上工程里原有的 BigSoundBank 门吱呀声（CC0）。
- **署名：** 需要署名的两条写在 `AUDIO_LICENSES.md`。
- **原件：** 原件不改，放在 `AudioSource/Recorded/`。
- **潮湿地毯：** 网上没有现成的"潮湿地毯脚步"，所以用四种素材分层拼出来：干地毯脚步、湿布挤压、粘脚剥离、泡水的鞋。

### 7.2 制作流程（`Tools/audio/recorded_library.py`）
- **切片：**
  - 按能量自动切出脚步，脚跟和脚尖算一步。
  - 每片只留一个事件：主击打必须在前 120 ms 内，下一步开始之前截断。
  - 信噪比要求：主层 ≥ 30 dB，垫在下面的层 ≥ 18 dB。
- **规格：**
  - 单声道，48 kHz / 24-bit。
  - 主击打离文件开头 ≤ 4 ms；结尾 20–50 ms 余弦淡出。
  - 同一组文件对齐短时响度；常规峰值 −3 dBFS，任何文件不超过 −1 dBFS。
- **处理：**
  - 脚步主体在 120 Hz 和 240 Hz 各做一个窄陷波，避开嗡鸣。
  - 两条欧洲（50 Hz 电网）房间底噪，陷掉 50/100/150/200/300 Hz，不和 120 Hz 嗡鸣打拍。
  - Relay 的脚步是硬底皮鞋走地毯，降 2–4 个半音（磁带式变速）。
- **循环：**
  - 嗡鸣：先测出 240 Hz 分音的精确基频（120.02 Hz），按相位对齐接缝（相关系数 0.979）。
  - 空气底噪：用等功率交叉淡化。
- **溯源：** 每个文件来自哪条录音的第几秒，都记在 `AudioSource/FMOD_Library/LIBRARY.json`。
- **在 FMOD 里的位置：** 真实录音在 `Recorded/` 资源文件夹；不再使用的合成占位已自动删除。

### 7.3 潮湿地毯的分层逻辑

| 层 | 素材 | 频段 / 时间 | 随 Dampness 变化 |
|---|---|---|---|
| Body 主体 | taure、hannagreen、conleec 的地毯脚步 | 全频；Carpet 是厚垫地毯，CarpetTile 是胶粘地毯块（更亮） | 不变 |
| Moist 湿 | 湿布挤压 | 300 Hz–2 kHz，80–240 ms | 0 时静音；0.4 时 −14 dB；1 时 −3 dB |
| Peel 粘脚 | 湿布的高频噼啪 | 2–5 kHz，比脚跟晚 50–150 ms | 0.5 时 −16 dB；1 时 −6 dB |
| Squish 泡水 | bewagne 的湿鞋录音 | 宽频 | 只在 > 0.75 时出现（潮湿 ≠ 咕叽） |
| Cloth 衣物 | 跑步时外套的摩擦 | 1.5 kHz 以上 | 跑步时最响 |

- **Dampness 怎么来：** 地图还没有水的数据，先按区域给值：
  - 低矮 0.55、标准 0.4、高大 0.3、办公 0.15。
  - 以后地图加水洼，让 `DampnessAt` 返回 0.8–1 就行。
- **鞋子带水：** 鞋子会带着湿度，离开湿处后约 30 秒才慢慢变干。
- **Relay：** 同样跟随 Dampness，用的是降调后的湿层。

### 7.4 混音（FMOD 离线渲染实测，短时最大响度）

| 元素 | 响度 |
|---|---|
| 玩家脚步（Level 0，走） | −29.4 LUFS |
| Relay，3 m | −25.3（比玩家自己的脚步响 4 dB） |
| Relay，10 m | −36.7；隔墙时 −46.8（减 10 dB，并且变闷） |
| 嗡鸣 | −36.8；Tension 拉满时 −34.2 |
| 近处一盏灯（1.5 m） | −33.4 |
| 空气底噪 | −44.1 |

- **限幅器：** 主总线加了限幅器，Relay 贴脸冲刺时峰值不超过 0 dBFS。
- **首轮修正：** 第一轮实测发现三个问题：
  - Relay 比玩家脚步还轻 6.5 dB；
  - 隔墙几乎不减音量；
  - 一盏近处的灯比脚步还响。
  这三处都已修正。

### 7.5 仍是合成占位的部分（37 个文件）
- **还没有录音的：**
  - Metal 脚步；
  - Relay 的低频存在感、咔哒声、状态提示音；
  - 呼吸、心跳、耳鸣；
  - 灯管爆裂；
  - 闭门器液压声、快速关门的气压声、自动门电机；
  - 玻璃受力的持续声。
- **下一批要录（按优先级）：**
  1. 自己录湿地毯，干、喷湿、泡水三遍；
  2. 美国的荧光灯；
  3. 学校的商用门；
  4. 自动门电机。

### 7.6 检查方法
- **核对 bank：** `python3 Tools/audio/fmod_check.py contract`。
  - 不开 Unity，直接用 FMOD 运行库读取 bank。
  - 核对代码用到的 28 个事件、3 个全局参数、4 条总线。
  - 加过反例测试：不存在的参数会报错。
- **离线渲染：** `python3 Tools/audio/fmod_check.py render` 把 14 个游戏片段渲染到 `Tools/audio/build/renders/`，包括：
  - 脚步：干 / 潮湿 / 泡水 / 跑步 / 地毯块；
  - Relay 从拐角外走近；
  - 开门再关门；Relay 破门；
  - 房间里 Tension 上升；玻璃碎裂；灯管启动；捡钥匙。
- **Unity 内检查：** `FrontRooms/Audio/Verify FMOD banks against code` 已加上新参数。
  - 今晚的批处理被关卡设计器对话正在写的编辑器脚本挡住了（编译错误不在音频代码里）。
  - 等它能编译了再跑一次。

## Sources
- Foley 三分类（Feet / Moves / Specifics）：https://filmdaft.com/what-is-a-foley-artist-definition-role-process-and-tools-in-film/
- Farnell, *Designing Sound*，Creaking Door 练习：https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/8375/designing_sound.zip/practical09.html
- 粘滑吱呀的 SuperCollider 实现：https://en.wikibooks.org/wiki/Designing_Sound_in_SuperCollider/Creaking_door
- BeamNG 门锁音频系统：https://beamng.com/game/news/blog/latch-audio-system
- 动画驱动的脚步与计时器漂移：https://bugnet.io/blog/how-to-fix-footsteps-out-of-sync-with-animation
- BFS Foley System（动画驱动、脚跟/脚尖分开检测）：https://www.fab.com/listings/8b84641b-31fd-4ee9-8882-1844a706dce9
- Wwise 材质 Switch 与脚步：https://blog.audiokinetic.com/footsteps-material-management-using-wwise-unreal-engine-4-unity-3d/
- Wwise Blend Container 与 RTPC（社区问答）：https://audiokinetic.com/qa/12217/playing-parts-of-a-sound-based-on-rtpc-value
- FMOD Studio 参数：https://www.fmod.com/docs/2.03/studio/parameters.html
- Unity Web 音频限制：https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-audio.html
- Dead Space 的 fear emitters：https://designingsound.org/2009/06/all-about-the-sound-of-dead-space/
- Silent Hill 的收音机杂音：https://www.gosugamers.net/entertainment/news/77521-halloween-gaming-an-ode-to-silent-hill-s-unsung-hero-creepy-radio-static
- Alien: Isolation 的声音设计：https://pcgamer.com/the-audio-of-alien-isolation
- Netflix ta-dum：https://www.istitutomarangoni.com/en/maze35/design/where-did-the-netflix-tudum-sound-come-from
- Rez 的音效量化：https://gamedeveloper.com/audio/oral-history-of-i-rez-i-recounts-a-marriage-of-game-and-music
- Journey 的声音与音乐：https://destructoid.com/?p=126775
- INSIDE（Martin Stig Andersen）：https://www.killscreen.com/mad-science-behind-insides-soundtrack/
- Sonic DNA：https://ampsoundbranding.com/sonic-dna
- 荧光灯 120 Hz 嗡鸣（磁致伸缩）：http://hyperphysics.gsu.edu/hbase/Solids/magstrict.html
