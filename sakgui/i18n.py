"""Chinese / English UI strings.
界面的中英文文本。"""

_LANG = "zh"

STRINGS = {
    # --- app / navigation / 程序 / 导航
    "app_title": {"zh": "NX Toolkit · Switch 工具箱", "en": "NX Toolkit · Switch toolbox"},
    "app_subtitle": {"zh": "基于 SAK 思路重写的界面", "en": "A rewritten GUI inspired by SAK"},
    "nav_convert": {"zh": "格式互转", "en": "Convert"},
    "nav_merge": {"zh": "合并更新/DLC", "en": "Merge Update/DLC"},
    "nav_split": {"zh": "拆分 / 合并分卷", "en": "Split / Join"},
    "nav_firmware": {"zh": "提取固件", "en": "Firmware"},
    "nav_save": {"zh": "提取存档", "en": "Savegames"},
    "nav_forwarder": {"zh": "NRO 转发器", "en": "NRO Forwarder"},
    "nav_settings": {"zh": "设置", "en": "Settings"},
    "nav_about": {"zh": "关于 / 致谢", "en": "About / Credits"},

    # --- common widgets / 通用控件
    "add_files": {"zh": "添加文件", "en": "Add files"},
    "add_folder": {"zh": "添加文件夹", "en": "Add folder"},
    "remove": {"zh": "移除", "en": "Remove"},
    "clear": {"zh": "清空", "en": "Clear"},
    "browse": {"zh": "浏览…", "en": "Browse…"},
    "start": {"zh": "开始", "en": "Start"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "open_output": {"zh": "打开输出目录", "en": "Open output folder"},
    "output_dir": {"zh": "输出目录", "en": "Output folder"},
    "drop_hint": {"zh": "把文件拖到这里，或点击「添加文件」", "en": "Drop files here or click \"Add files\""},
    "log": {"zh": "日志", "en": "Log"},
    "clear_log": {"zh": "清空日志", "en": "Clear log"},
    "ready": {"zh": "就绪", "en": "Ready"},
    "running": {"zh": "运行中：{0}", "en": "Running: {0}"},
    "done_ok": {"zh": "全部完成", "en": "All done"},
    "done_fail": {"zh": "有任务失败，请查看日志", "en": "Some tasks failed, see log"},
    "cancelled": {"zh": "已取消", "en": "Cancelled"},
    "queue_info": {"zh": "队列：{0} 个任务", "en": "Queue: {0} task(s)"},
    "no_files": {"zh": "请先添加文件。", "en": "Please add some files first."},
    "quit_busy": {"zh": "有任务正在运行，确定取消任务并退出吗？", "en": "A task is running. Cancel it and quit?"},
    "error": {"zh": "错误", "en": "Error"},
    "missing_tool": {"zh": "找不到工具：{0}\n请在「设置」里检查工具目录。", "en": "Tool not found: {0}\nCheck the tools folder in Settings."},
    "missing_keys": {"zh": "找不到密钥文件 prod.keys。\n请在「设置」里指定从你自己的主机导出的密钥。", "en": "prod.keys not found.\nSet the keys dumped from your own console in Settings."},
    "task_ok": {"zh": "[完成] {0}", "en": "[done] {0}"},
    "task_fail": {"zh": "[失败] {0}（退出码 {1}）", "en": "[failed] {0} (exit code {1})"},

    "temp_cleaned": {"zh": "  已清理本任务的临时文件", "en": "  Task temp files removed"},
    "temp_left": {"zh": "  [注意] 临时文件未能删除（可能仍被占用）：{0}", "en": "  [warn] Could not remove temp files (still in use?): {0}"},
    "temp_purged": {"zh": "启动时清理了 {0} 个上次残留的临时任务文件夹", "en": "Removed {0} leftover temp job folder(s) at startup"},
    "temp_hint": {"zh": "临时文件夹（中间文件放这里，任务结束后自动删除；多步转换需要额外空间）",
                  "en": "Temp folder (intermediate files, deleted when each task ends; chained conversions need extra space)"},
    "output_file": {"zh": "  输出：{0}", "en": "  Output: {0}"},
    "output_mismatch": {"zh": "  [注意] 没有生成 {0} 文件，实际生成的是：{1}", "en": "  [warn] No {0} was produced; got: {1}"},
    "xci_needs_base": {"zh": "这是{0}，不含游戏本体，无法单独做成 XCI/XCZ。你可以：\n"
                              "  ① 把「转换为」改成 NSP（或 NSZ），单独输出{0}，可直接安装；\n"
                              "  ② 到「合并更新/DLC」页，和游戏本体一起合并，输出 XCI。",
                       "en": "This is {0} without the base game, so it can't become an XCI/XCZ on its own. You can:\n"
                             "  1) set \"Convert to\" to NSP (or NSZ) to output {0} on its own, ready to install; or\n"
                             "  2) use \"Merge Update/DLC\" with the base game and choose XCI."},
    "kind_update": {"zh": "更新包", "en": "an update"},
    "kind_dlc": {"zh": "DLC", "en": "a DLC"},
    "chain_plan": {"zh": "  需要多步转换：{0}（中间文件放在临时目录，任务结束后删除）",
                   "en": "  Chained conversion: {0} (intermediate files go to the temp folder and are deleted afterwards)"},
    "chain_stage": {"zh": "  [{0}/{1}] {2}：{3} → {4}", "en": "  [{0}/{1}] {2}: {3} → {4}"},
    "chain_tmp": {"zh": "（中间文件，放在临时目录）", "en": " (intermediate, in temp folder)"},
    "merge_inputs": {"zh": "  待合并的文件：", "en": "  Files to merge:"},
    "kind_name_base": {"zh": "本体", "en": "Base"},
    "kind_name_update": {"zh": "更新包", "en": "Update"},
    "kind_name_dlc": {"zh": "DLC", "en": "DLC"},
    "kind_name_unknown": {"zh": "未知（文件名里没有 Title ID）", "en": "Unknown (no title ID in file name)"},
    "merge_no_base": {"zh": "这些文件里没有游戏本体，无法合并成 XCI。你可以：\n"
                            "  ① 把输出格式改成 NSP，把更新包/DLC 合并成一个 NSP；\n"
                            "  ② 加入游戏本体后再合并成 XCI。",
                      "en": "There is no base game among these files, so they can't be merged into an XCI. You can:\n"
                            "  1) switch the output format to NSP to merge the update/DLC into one NSP; or\n"
                            "  2) add the base game and merge to XCI."},
    "merge_decompress": {"zh": "  检测到 {0} 个 NSZ/XCZ 压缩文件，先用 nsz 解压到临时目录再合并（需要额外空间）",
                         "en": "  Found {0} NSZ/XCZ file(s); decompressing them with nsz to the temp folder before merging (needs extra space)"},
    "merge_missing": {"zh": "解压后的文件不全：应有 {0} 个，只找到 {1} 个", "en": "Decompressed files incomplete: expected {0}, found {1}"},
    "merge_start": {"zh": "  开始用 NSC_BUILDER 合并 {0} 个文件 → {1}", "en": "  Merging {0} files with NSC_BUILDER → {1}"},
    "card_tools": {"zh": "工具下载与更新", "en": "Tools download & update"},
    "tools_source": {"zh": "工具来自原版 SAK 的 GitHub 发布包（dezem/SAK），下载到程序目录下的 tools 文件夹；不会下载或覆盖任何密钥文件。",
                     "en": "Tools come from the original SAK release on GitHub (dezem/SAK) and go to the tools folder next to the program; no key files are downloaded or overwritten."},
    "btn_download_tools": {"zh": "下载 / 修复工具", "en": "Download / repair tools"},
    "btn_check_updates": {"zh": "检查更新", "en": "Check for updates"},
    "tools_version": {"zh": "当前工具版本：{0}", "en": "Installed tools: {0}"},
    "unknown": {"zh": "未知", "en": "unknown"},
    "task_download_tools": {"zh": "下载工具（原版 SAK 发布包）", "en": "Download tools (SAK release)"},
    "task_check_updates": {"zh": "检查更新", "en": "Check for updates"},
    "sak_found": {"zh": "找到 SAK {0}（{1}），正在下载…", "en": "Found SAK {0} ({1}), downloading…"},
    "extracting": {"zh": "正在解压…", "en": "Extracting…"},
    "tools_installed": {"zh": "已安装 {0} 个工具文件到 {1}", "en": "Installed {0} tool files into {1}"},
    "tools_uptodate": {"zh": "工具已是最新（SAK {0}）", "en": "Tools are up to date (SAK {0})"},
    "tools_update_avail": {"zh": "工具可更新：{0} → {1}", "en": "Tools update available: {0} → {1}"},
    "app_uptodate": {"zh": "NX Toolkit 已是最新（v{0}）", "en": "NX Toolkit is up to date (v{0})"},
    "app_update_avail": {"zh": "NX Toolkit 有新版本：v{0} → {1}", "en": "NX Toolkit update available: v{0} → {1}"},
    "tools_missing_prompt": {"zh": "没有找到所需的命令行工具（hactoolnet、4nxci、squirrel、hacbrewpack）。\n\n"
                                   "是否现在从原版 SAK 的 GitHub 发布页下载？（约 28 MB，不含密钥）\n"
                                   "也可以稍后在「设置」里手动指定工具目录。",
                             "en": "The required command-line tools (hactoolnet, 4nxci, squirrel, hacbrewpack) were not found.\n\n"
                                   "Download them now from the original SAK release on GitHub? (about 28 MB, no keys)\n"
                                   "You can also set the tools folder in Settings later."},
    "tools_update_prompt": {"zh": "工具有新版本 {0}，现在下载更新吗？", "en": "Tools {0} are available. Download now?"},
    "app_update_prompt": {"zh": "NX Toolkit 有新版本 {0}，打开下载页面吗？", "en": "NX Toolkit {0} is available. Open the download page?"},
    "tools_autodetected": {"zh": "已自动找到工具目录：{0}", "en": "Tools folder found automatically: {0}"},
    "tools_manual": {"zh": "工具齐全，但为手动安装、无法确定版本（最新 SAK 为 {0}）；需要时可点「下载 / 修复工具」",
                     "en": "Tools are complete but installed by hand, version unknown (latest SAK is {0}); use \"Download / repair tools\" if needed"},
    "english_names": {"zh": "合并 / 转换后把输出文件名统一为游戏英文标题（读取游戏内的英文名称）",
                      "en": "Rename merge / convert outputs to the game's English title (read from the game data)"},
    "en_name_done": {"zh": "  已改为英文文件名：{0} → {1}", "en": "  Renamed to English title: {0} → {1}"},
    "en_name_no_title": {"zh": "  [注意] 游戏里没有英文标题，保留原文件名", "en": "  [warn] No English title in the game data; file name kept"},
    "en_name_failed": {"zh": "  [注意] 读取英文标题失败，保留原文件名：{0}", "en": "  [warn] Could not read the English title; file name kept: {0}"},
    "integrity_ok": {"zh": "  完整性检查通过：文件目录登记了 {0} 个文件，覆盖全部数据", "en": "  Integrity check passed: the file index lists {0} files covering all data"},
    "integrity_bad": {"zh": "  [警告] 完整性检查未通过：{0} 的数据有 {1}，但文件目录只登记了 {2}（{3} 个文件{4}）。\n"
                            "  游戏本体或更新很可能没有被登记，这个文件大概率无法运行。\n"
                            "  建议：改用 NSP 作为输入重新合并（本体 NSP + 更新 + DLC），不要用已合并过的 XCI 再加 DLC。",
                      "en": "  [warning] Integrity check failed: {0} holds {1} of data but its file index covers only {2} ({3} files{4}).\n"
                            "  The base game or update is probably missing from the index, so the file will most likely not run.\n"
                            "  Suggestion: merge again from NSP inputs (base NSP + update + DLC) instead of adding DLC to an already merged XCI."},
    "integrity_dup": {"zh": "，且有重复登记", "en": ", with duplicate entries"},
    "integrity_error": {"zh": "  [警告] 无法检查 {0} 的完整性：{1}", "en": "  [warning] Could not check the integrity of {0}: {1}"},
    "integrity_failed": {"zh": "输出文件不完整：{0}（文件已保留，请勿直接使用）", "en": "Output file is incomplete: {0} (kept on disk; do not use it as is)"},
    "card_input": {"zh": "输入文件", "en": "Input"},
    "card_paths": {"zh": "路径", "en": "Paths"},
    "card_meta": {"zh": "信息", "en": "Meta"},
    "card_saves": {"zh": "存档文件", "en": "Save files"},
    "card_merge": {"zh": "本体 + 更新 + DLC", "en": "Base + Update + DLC"},

    # --- convert / 格式互转
    "convert_title": {"zh": "格式互转  XCI · NSP · NSZ · XCZ", "en": "Convert  XCI · NSP · NSZ · XCZ"},
    "convert_desc": {"zh": "添加文件后在下拉框里选择目标格式，程序会按输入类型自动选择工具，需要时串联多步（中间文件放在临时目录，完成后自动清理）。",
                     "en": "Add files, pick the target format in the dropdown. Tools are chosen per input type and chained when needed (intermediate files go to the temp folder and are cleaned up)."},
    "convert_target": {"zh": "转换为", "en": "Convert to"},
    "target.nsp": {"zh": "NSP（可安装包）", "en": "NSP (installable package)"},
    "target.xci": {"zh": "XCI（卡带镜像）", "en": "XCI (cartridge image)"},
    "target.nsz": {"zh": "NSZ（压缩的 NSP）", "en": "NSZ (compressed NSP)"},
    "target.xcz": {"zh": "XCZ（压缩的 XCI）", "en": "XCZ (compressed XCI)"},
    "convert_same": {"zh": "{0} 已经是目标格式，已跳过。", "en": "{0} is already in the target format, skipped."},
    "nsz_options": {"zh": "NSZ / XCZ 压缩选项", "en": "NSZ / XCZ compression"},
    "keep_ncaid": {"zh": "保留 NCA ID（4NXCI --keepncaid）", "en": "Keep NCA IDs (4NXCI --keepncaid)"},
    "rename_out": {"zh": "按游戏名重命名输出（4NXCI -r）", "en": "Rename output by title (4NXCI -r)"},

    # --- merge / 合并
    "merge_title": {"zh": "合并本体 + 更新 + DLC", "en": "Merge base + update + DLC"},
    "merge_desc": {"zh": "把同一游戏的本体、更新、DLC 合并成一个文件（NSC_BUILDER 多内容合并）。",
                   "en": "Combine base game, update and DLC of one title into a single file (NSC_BUILDER multi-content)."},
    "merge_format": {"zh": "输出格式", "en": "Output format"},
    "merge_need2": {"zh": "合并至少需要两个文件（本体 + 更新/DLC）。", "en": "Merging needs at least two files (base + update/DLC)."},

    "level": {"zh": "压缩等级（1–22，默认 18）", "en": "Level (1–22, default 18)"},
    "long_mode": {"zh": "长距离模式 (-L)，更小但更慢更吃内存", "en": "Long distance mode (-L): smaller, slower, more RAM"},
    "mode": {"zh": "压缩方式", "en": "Mode"},
    "mode_auto": {"zh": "自动（NSZ 用 Solid，XCZ 用 Block）", "en": "Auto (Solid for NSZ, Block for XCZ)"},
    "mode_block": {"zh": "Block（可随机读取，多线程）", "en": "Block (random access, multithreaded)"},
    "mode_solid": {"zh": "Solid（压缩率略高）", "en": "Solid (slightly better ratio)"},
    "threads": {"zh": "线程数（0 = 自动）", "en": "Threads (0 = auto)"},
    "quick_verify": {"zh": "压缩后快速校验 (-Q)", "en": "Quick verify after compression (-Q)"},
    "overwrite": {"zh": "覆盖已存在的文件 (-w)", "en": "Overwrite existing files (-w)"},

    # --- split / 拆分
    "split_title": {"zh": "FAT32 分卷 / 合并分卷", "en": "FAT32 split / join"},
    "split_desc": {"zh": "FAT32 单文件上限 4GB。NSP 拆成带存档属性的文件夹（00, 01…），XCI 拆成 .xc0/.xc1…。选择分卷文件夹或 .xc0 可合并回来。",
                   "en": "FAT32 caps files at 4 GB. NSP → archive-bit folder (00, 01…), XCI → .xc0/.xc1…. Pick a split folder or .xc0 to join."},
    "split_mode": {"zh": "操作", "en": "Action"},
    "do_split": {"zh": "拆分", "en": "Split"},
    "do_join": {"zh": "合并分卷", "en": "Join"},
    "split_same_dir": {"zh": "NSP 拆分输出目录不能和源文件同目录（会与原文件重名），请换一个输出目录。",
                       "en": "NSP split output can't be the source folder (name clash). Choose another output folder."},
    "split_small": {"zh": "{0} 小于 4GB，无需拆分，已跳过。", "en": "{0} is under 4 GB, no split needed, skipped."},

    # --- firmware / 固件
    "fw_title": {"zh": "从 XCI 提取系统固件", "en": "Extract firmware from XCI"},
    "fw_desc": {"zh": "提取卡带 update 分区里的固件 NCA（hactoolnet），并根据 fw_nca_mapping.csv 识别版本。",
                "en": "Extract firmware NCAs from the cartridge update partition (hactoolnet) and identify the version via fw_nca_mapping.csv."},
    "fw_version": {"zh": "识别到固件版本：{0}", "en": "Detected firmware version: {0}"},
    "fw_unknown": {"zh": "未能识别固件版本（映射表里没有对应 NCA）。", "en": "Firmware version unknown (no matching NCA in mapping table)."},

    # --- save / 存档
    "save_title": {"zh": "提取存档", "en": "Extract savegames"},
    "save_desc": {"zh": "解包从 USER 分区 /save 复制出来的存档文件（hactoolnet -t save）。每个存档输出到独立子文件夹。",
                  "en": "Unpack save files copied from USER partition /save (hactoolnet -t save). Each save goes to its own subfolder."},

    # --- forwarder / 转发器
    "fwd_title": {"zh": "NRO 转发器（生成 NSP）", "en": "NRO forwarder (build NSP)"},
    "fwd_desc": {"zh": "生成一个在主页显示图标、启动后跳转到 SD 卡上 NRO 的 NSP（hacBrewPack + nx-hbloader 转发器）。",
                 "en": "Build an NSP that shows a home-menu icon and launches an NRO from the SD card (hacBrewPack + nx-hbloader forwarder)."},
    "fwd_nro_local": {"zh": "本地 NRO 文件（用于读取名称和图标，可选）", "en": "Local NRO file (to read name & icon, optional)"},
    "fwd_nro_path": {"zh": "SD 卡上的 NRO 路径", "en": "NRO path on SD card"},
    "fwd_name": {"zh": "名称", "en": "Title"},
    "fwd_publisher": {"zh": "发行者", "en": "Publisher"},
    "fwd_version": {"zh": "显示版本", "en": "Display version"},
    "fwd_icon": {"zh": "图标（任意图片，自动转为 256×256 JPEG）", "en": "Icon (any image, converted to 256×256 JPEG)"},
    "fwd_titleid": {"zh": "Title ID", "en": "Title ID"},
    "fwd_random": {"zh": "随机", "en": "Random"},
    "fwd_screenshot": {"zh": "允许截图", "en": "Allow screenshots"},
    "fwd_video": {"zh": "允许录像", "en": "Allow video capture"},
    "fwd_user": {"zh": "启动时选择用户", "en": "Select user on launch"},
    "fwd_read_nro": {"zh": "已从 NRO 读取：{0}", "en": "Read from NRO: {0}"},
    "fwd_no_icon": {"zh": "请选择图标，或选择带图标的 NRO。", "en": "Choose an icon, or pick an NRO that contains one."},
    "fwd_bad_tid": {"zh": "Title ID 必须是 16 位十六进制。", "en": "Title ID must be 16 hex digits."},
    "fwd_bad_path": {"zh": "SD 路径应以 sdmc:/ 开头并以 .nro 结尾。", "en": "SD path must start with sdmc:/ and end with .nro."},
    "fwd_need_name": {"zh": "请填写名称。", "en": "Please enter a title."},
    "fwd_preview": {"zh": "图标预览", "en": "Icon preview"},

    # --- settings / 设置
    "settings_title": {"zh": "设置", "en": "Settings"},
    "language": {"zh": "界面语言", "en": "Language"},
    "tools_dir": {"zh": "工具目录（含 hactoolnet / 4nxci / squirrel / hacbrewpack 等）", "en": "Tools folder (hactoolnet / 4nxci / squirrel / hacbrewpack …)"},
    "keys_file": {"zh": "密钥文件 prod.keys（来自你自己的主机）", "en": "Keys file prod.keys (from your own console)"},
    "default_output": {"zh": "默认输出目录", "en": "Default output folder"},
    "temp_dir": {"zh": "临时目录", "en": "Temp folder"},
    "tool_status": {"zh": "工具检测", "en": "Tool check"},
    "found": {"zh": "已找到", "en": "found"},
    "not_found": {"zh": "缺失", "en": "missing"},
    "save_settings": {"zh": "保存设置", "en": "Save settings"},
    "saved": {"zh": "设置已保存。", "en": "Settings saved."},
    "lang_busy": {"zh": "任务运行中，语言将在任务结束后切换。", "en": "A task is running; language will switch after it finishes."},

    # --- about / 关于
    "about_title": {"zh": "关于与致谢", "en": "About & credits"},
}


def set_lang(lang: str) -> None:
    global _LANG
    _LANG = lang if lang in ("zh", "en") else "zh"


def lang() -> str:
    return _LANG


def tr(key: str, *args) -> str:
    entry = STRINGS.get(key)
    text = entry.get(_LANG, entry["en"]) if entry else key
    return text.format(*args) if args else text
