# Office Level：家具资产、电影镜头与落地方案

研究日期：2026-10-01。本文把用户提供的三张参考图、A24 的《Backrooms》制作资料和当前 Unity 6 / URP 17.3 项目对齐。电影截图、海报和 Wiki 图片只作为构图与材质研究，不被打包进游戏。

## 1. 参考图拆解

### 当前 Office 原型（参考图 1）

- 三个重复的 1990s 工位，中心线清楚，适合玩家从门口读出房间的尺度。
- 每个工位由薄木色桌面、两侧支撑、厚 CRT、小纸张和蓝灰屏风组成。
- 原始实现是运行时创建的硬边方盒，只能表达布局。现在已补齐 Blender 源文件与 Unity 可导入的 FBX 分件，运行时优先加载真实模型，程序化网格只作为导入失败时的降级路径。
- 本次保留中间追逐通道的位置关系，使用可重复的桌、CRT、办公椅、抽屉和小纸张套件，并把工位错层放到左右两侧。

### 家具堆（参考图 2、3）

- 这些图不是随机垃圾，而是可识别的普通家具被生硬地复制、倾斜、压扁、镜像并互相嵌入：桌、抽屉柜、书架、扶手椅、沙发、电视和台灯仍然能被辨认。
- 因此游戏中应先建立一套可信的普通家具，再创建一个只负责视觉组合的 `memory bleed` / `distorted pile` 层。组合层使用固定 seed，保证每次房间回收后仍能复现同一处异常。
- 中心门线保持空置；家具堆放在后墙和侧墙，不改变现有房间流式边界。若以后要让它成为真正的障碍，需要单独把 prop bounds 接入移动系统。

## 2. Backrooms 与电影研究

Kane Parsons 的电影不是一个可以直接下载的资产包，也没有一个统一的官方 Level canon。A24 官方资料把电影的起点描述为 2019 年匿名上传的房间照片；Parsons 将它扩展成物理存在的迷宫，用细小的柱、灯、墙纸和家具变化让玩家怀疑自己的空间记忆。

- [A24《Backrooms》官方电影页](https://a24films.com/films/backrooms)：电影由 Kane Parsons 导演，故事从家具店地下室出现的异常门洞开始。
- [A24 官方访谈：Thirty Thousand Square Feet with Kane Parsons & James Wan](https://a24films.com/notes/2026/05/thirty-thousand-square-feet-with-kane-parsons-james-wan)：说明原图、迷宫、Blender 预演和“普通空间逐渐不再遵守自己的规则”的方法。
- [A24 官方 Blu-ray 页面](https://shop.a24films.com/products/backrooms-blu-ray)：列出了 `Building the Backrooms`、VFX breakdown 和 prop walkthrough 等制作附录；这些是研究来源，不是可再发行的游戏素材。
- [Curbed：Backrooms production design interview](https://www.curbed.com/article/backrooms-kane-pixels-a24-set-production-design-interview.html)：记录了 30,000 平方英尺实景、350 个 custom troffer、Facebook Marketplace / hotel liquidators 的 1990s 家具，以及柔和粉彩与木饰边。
- [Sony Cinematography：Jeremy Cox 与 Venice 2](https://sony-cinematography.com/dp-jeremy-cox-and-venice-2-ground-the-extradimensional-reality-of-backrooms/)：室内使用 18mm 或更宽的镜头，主要依靠顶部 practical light，空间中的办公室家具要接受同一套环境光。
- [ASC：Backrooms cinematography](https://theasc.com/article/backrooms-cinematography-cox/)：2×4 drop ceiling、实体黄色墙纸和顶部灯具是空间的识别骨架；没有传统的侧面 key 或浅景深来“美化”家具。
- [The Credits / Danny Vermette](https://www.motionpictures.org/2026/06/how-production-designer-danny-vermette-made-backrooms-real-portals-platforms-practical-terror/)：墙纸、地毯和实景迷宫被作为连续的空间指纹设计。
- [制作设计采访转载：家具被带入并改变空间](https://timewarnerent.com/backrooms-designing-the-films-liminal-space-with-production-design/)：家具店的真实家具被放入 Backrooms，部分空间被做成不自然的坡道、爬行缝和高差。这对应本项目的“可辨认家具 + 可追溯变形”规则。

### Shot inventory 与游戏映射

| 电影语言 | 游戏里的原创落地 | 当前实现/后续入口 |
| --- | --- | --- |
| 普通家具店/办公室的广角建立镜头 | 保留三工位、greige 墙、蓝灰地毯和顶部荧光灯；镜头保持 90–100° FOV，不追加夸张鱼眼 | 现有 Office profile 与三工位 socket |
| 门洞/阈值镜头 | 门两侧各留一个正常家具，墙纸接缝在门后出现一次轻微错位 | 现有 streamed room / door threshold |
| 360° 空间揭示 | 先让普通家具成立，再在侧后方出现一件角度或尺度错误的复制品 | `office memory bleed / variant 0–2` |
| 家具嵌入墙或地面 | 保留原材质、把复制品部分埋入墙/地，并给接触处加灰尘或裂缝 decal；不复制电影道具 | 当前嵌入 cabinet、错角 desk，后续可加 decal |
| 垂直/错层空间 | 后续做独立的 ramp、平台和 crawl tunnel，不能直接扩大本房间 bounds | 作为新 `DistortedFurniturePile` 场景套件 |
| 低机位长隧道 | 用顶部 practical light、宽视野和低地平线；家具只在边缘制造尺度参照 | Run / Level ! 变体，不能挤占中心追逐线 |
| 红色追逐段 | 将它标成项目自己的 `Level ! inspired variant`；社区 Wiki 的不同 Level ! 版本不能混称为电影 canon | 当前 Run profile 的红色 exit cue |

## 3. 可直接落地的现成资产

本次没有把电影 still 或电影原始道具拷贝进项目，而是在 Blender 中制作了一套可编辑的原创 Office 模型。以下外部来源仍作为未来 hero asset 的候选；导入前仍要在 Unity 6 / URP 17.3 中检查法线、切线、贴图色彩空间和碰撞。

| 来源 | 可用内容 | 授权与落地判断 |
| --- | --- | --- |
| [Poly Haven furniture](https://polyhaven.com/models/furniture) | 金属办公桌、钢架书架、学校桌、木柜、椅子等；页面有 FBX / glTF / Blender 下载 | [Poly Haven License](https://polyhaven.com/license) 为 CC0，适合作为 hero prop 候选；需保留下载页面和版本记录 |
| [Poly Haven Metal Office Desk](https://polyhaven.com/a/metal_office_desk) | 8K 金属办公桌，带抽屉和磨损，约 7k tris | CC0；适合替换当前一张主桌，之后用旋转/尺度偏差生成复制品 |
| [Poly Haven Steel Frame Shelves](https://polyhaven.com/a/steel_frame_shelves_01) | 8K 钢架书架，约 4k tris | CC0；适合家具堆的可识别轮廓 |
| [OpenGameArt office desk and chair set](https://opengameart.org/content/office-desk-and-chair-set) | 办公桌椅组合 | 页面标为 CC0；落地前确认下载包内每个文件都继承同一许可 |
| [Kenney Furniture Kit](https://kenney.nl/assets/furniture-kit) | 模块化家具原型 | Kenney 的资产页面标为 CC0；适合早期组合预演，电影级 hero prop 需要重新做材质/边缘 |

不建议直接使用电影 still、Kane Pixels/电影模型、A24 标识、Async 品牌、角色模型或电影原始 prop。Backrooms Wiki 的页面和图片通常是 CC BY-SA 3.0；例如 [Level 4](https://backrooms-wiki.wikidot.com/level-4) 可作为社区 canon 的办公室气氛参考，但直接衍生内容需要遵守 [licensing guide](https://backrooms-wiki.wikidot.com/licensing-guide)。本项目只使用空间概念和镜头规则，并保持自己的命名与资产来源记录。

### Shot reference index（只做研究链接）

- [A24 official film page](https://a24films.com/films/backrooms)：官方预告、简介和电影入口。
- [Curbed / New York production still 01](https://pyxis.nymag.com/v1/imgs/4a9/6c7/0376fa5b03b593403a08655907521db295-backroom.rhorizontal.w700.png)：普通空间与家具堆的比例参考。
- [Curbed / New York production still 02](https://pyxis.nymag.com/v1/imgs/3ba/2de/675f8b1ea7f685a45ec28097b16cf13fc3-Still012-CropR.rhorizontal.w700.jpg)：墙纸、柱子和家具错位的构图参考。
- [A24 wallpaper one-sheet](https://atwenty-four.transforms.svdcdn.com/production/images/BACKROOMS_Digi_1-Sheet_Wallpaper_W01_FIN01.jpg?w=2025&auto=compress%2Cformat&fit=crop&dm=1772038079&s=f133331d7807368d2eb03286e31f49a6)：墙纸作为空间指纹的色调参考，不复制到项目。
- [A24 Blu-ray bonus list](https://shop.a24films.com/products/backrooms-blu-ray)：如果需要逐镜头拆解，应从官方 `Building the Backrooms` / prop walkthrough 等附录获得观看权限，而不是抓取或重新发布电影画面。

## 4. 本次项目落地

- `Tools/Blender/generate_office_furniture_assets.py`：用 Blender 4.3 生成并导出十个原创模型资产，同时保存可继续编辑的源文件 `Tools/Blender/Source/OfficeFurnitureKit.blend`。
- `Assets/Resources/Models/Office/`：Unity 可直接导入的 `OfficeDesk.fbx`、`OfficeCRTComputer.fbx`、`OfficeTaskChair.fbx`、`OfficeCubiclePanel.fbx`、`OfficeFilingCabinet.fbx`、`OfficeCopier.fbx`、`OfficeWaterCooler.fbx`、`OfficeVendingMachine.fbx`、`OfficeShelf.fbx`、`OfficePillar.fbx`。电脑资产包含 CRT 外壳、玻璃屏、按键、键盘、鼠标、主机塔、通风口与线缆；vending machine 包含四排商品块。
- `Assets/Scripts/FrontRoomsOfficeFurniture.cs`：可回收房间现在优先实例化上述 FBX，并按材质槽名重新绑定项目 URP 材质；程序化桌、CRT、椅子、抽屉柜、书架、饮水机和 vending machine 仍保留为稳定 fallback。
- `FrontRoomsRoomStream.BuildProfileProps`：Office 分支现在调用家具套件，保留原有 blackout window、window frame 和中心追逐通道。
- `Assets/Resources/Surfaces/Textures/OfficeFurniture_*`：新增 wood、painted metal 和 faded vinyl 的 albedo / normal / mask 贴图。家具材质使用 `FrontRooms/Surface` 的 mesh UV，继续接受 URP 的宏观磨损、SSAO、阴影和后处理；`Tools/lookdev/gen_office_furniture_textures.py` 可在不依赖第三方包的情况下重建这组贴图。
- 变形层使用稳定的 `sequence` hash：一个复制桌、嵌入式 filing cabinet、倒置椅、错位 shelf 和第二个 CRT 会在三个 variant 中改变角度、尺度和偏移，但不会随机破坏门线。

下一步若要继续追求 hero asset 细节，顺序应是：在 `OfficeFurnitureKit.blend` 中细化一个目标资产的 bevel / UV / 贴图 → 重新导出对应 FBX → 在 Unity 中检查材质与阴影 → 再把同一 source asset 复制成正常、镜像、嵌入三种 variant，并为需要阻挡玩家的家具单独接入局部碰撞。
