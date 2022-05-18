# Takiyasha ![](https://img.shields.io/badge/Python-3.8+-red)

Takiyasha 是一个用来解密多种加密音乐文件的工具。

[Github](https://github.com/nukemiko/takiyasha/tree/remaked) | [Notabug](https://notabug.org/MiketsuSmasher/takiyasha/src/remaked)

**本项目是以学习和技术研究的初衷创建的，修改、再分发时请遵循 [License](https://github.com/nukemiko/takiyasha/blob/remaked/LICENSE)。**

Takiyasha 的设计灵感，以及部分解密方案，来源于 [Unlock Music Project - CLI Edition](https://github.com/unlock-music/cli)。

**Takiyasha 对输出数据的可用性（是否可以识别、播放等）不做任何保证。**

## 重要事项

在此分支中，包的结构和行为已经发生了翻天覆地的变化，因此不再兼容为之前的版本编写的工具。

**此分支中的版本，相较于之前版本，命令行调用参数有了重大变化。如果你有正常使用的需求，请谨慎升级。**

如果你不小心更新到了从此分支发布的版本，按照以下步骤回滚至最后一个稳定版本 v0.4.2：

1. 卸载：`pip uninstall takiyasha`
2. 安装 v0.4.2：`pip install -U takiyasha==0.4.2`

## 特性

- 跨平台：使用 Python 3 编写，只要系统中存在 Python 3.8 及以上环境，以及任意包管理器，就能安装并使用
- [x] 支持多种加密音乐文件格式，[点击此处查看详情](#supported_formats)
- [x] 针对主要功能，有完善的代码内文档
- [x] 作为 Python 库使用时，支持解密和反向加密（实验性功能，仅支持部分加密类型）
- [x] 命令行调用方式（仅限解密）
- [x] 自动根据文件内容探测文件的加密类型
- [ ] 自动补充解密后文件的标签信息（包括封面）
- [ ] 多文件并行处理

## <span id="supported_formats">支持的加密文件格式</span>

- QQ 音乐
    - `.qmc*`
    - `.mflac*`
    - `.mgg*`
    - 为以下加密文件提供部分支持：
        - 从版本 18.57 及之后的 QQ 音乐 PC 客户端下载的 `.mflac*`/`.mgg*` 文件
        - 从版本 11.5.5 及之后的 QQ 音乐 Android 客户端下载的 `.mflac*`/`.mgg*` 文件
- 网易云音乐
    - `.ncm`
    - `.uc!` （网易云音乐客户端的加密缓存文件）

## 如何安装

Python 版本需求：大于等于 3.8

需要的依赖项：
- [`pyaes`](https://pypi.org/project/pyaes/)：AES 加解密支持

### 从 Pypi 安装（推荐）

执行命令：`pip install -U takiyasha`

### 从本仓库安装

执行命令：`pip install -U git+https://github.com/nukemiko/takiyasha@remaked`

### 安装最新发布版本

1. 进入[此页面](https://github.com/nukemiko/takiyasha/releases/latest)，下载最新版本
    - 如果要下载其他版本（包括预发布版本），请直接前往[历史发布页面](https://github.com/nukemiko/takiyasha/releases)寻找和下载
    - 从本分支发布的版本全都是预发布版本，只能在[历史发布页面](https://github.com/nukemiko/takiyasha/releases)下找到
2. 下载 Wheel 安装包（扩展名为 `.whl` 的文件）
3. 下载完毕后，执行命令：
    `pip install -U /path/to/package.whl`

## 如何使用

### 命令行环境

简单易用：

`python -m takiyasha 1.ncm 2.qmcflac 3.mflac 4.mgg ...`

如果尝试解密“[仅部分支持](#supported_formats)”的文件：

`python -m takiyasha --lf hell.mflac damn.mgg`

如果不加其他参数，解密成功的文件将会在当前工作目录下产生。

使用 `-h, --help` 获取完整的帮助信息。

### 作为 Python 库使用

示例：

```python
import takiyasha

files = [
    'source.ncm',
    'source.qmcflac',
    'source_dynamic_map.mflac0',
    'source_rc4.mflac',
    'source_unsupported_keyformat.mflac',
    'is_ncm.unknown',
    'source_no_encrypted.flac'
]
for (idx, filename) in enumerate(files, 1):
    try:
        crypter = takiyasha.openfile(filename)  # 打开一个加密文件 filename
        if crypter is None:
            # 如果 crypter 为 None，说明未能根据文件名判断加密文件类型
            # 因此要加上参数 detect_content=True
            print(f"'{filename}'：无法根据文件名探测加密类型，切换到根据内容探测")
            crypter = takiyasha.openfile(filename, detect_content=True)
            if crypter is None:
                print(f"'{filename}'：仍然无法探测到加密类型，尝试使用 QMCv2 后备方案")
                # 'source_unsupported_keyformat.mflac' 是从版本 18.57 的 QQ 音乐 PC 客户端下载的文件，仅提供部分支持
                # 直接打开会引发 UnsupportedFileType 异常，需要使用基异常 TakiyashaException 捕获
                # 然后加上参数 legacy_fallback=True 使用后备方案再次尝试
                crypter = takiyasha.openfile(filename, legacy_fallback=True)
                if crypter is None:
                    # 如果 crypter 仍然为 None，说明此文件非已知加密文件，跳过
                    print(f"'{filename}'：跳过，非已知加密格式")
                    continue
        print(f"'{filename}'：已打开文件，加密类型：{crypter.__class__.__name__}")
    except takiyasha.TakiyashaException:
        continue

    audio_format = takiyasha.sniff_audio_file(crypter)
    if audio_format is None:
        audio_format = 'unknown'

    save_filename = f'target{idx}.{audio_format}'
    with open(save_filename, 'wb') as f:
        print(f"'{filename}' -> '{save_filename}'：打开输出文件并写入")
        crypter.seek(0, 0)
        f.write(crypter.read())
```

输出：

```sh-session
'source.ncm'：已打开文件，加密类型：NCM
'source.ncm' -> 'target1.flac'：打开输出文件并写入
'source.qmcflac'：已打开文件，加密类型：QMCv1
'source.qmcflac' -> 'target2.flac'：打开输出文件并写入
'source_dynamic_map.mflac0'：已打开文件，加密类型：QMCv2
'source_dynamic_map.mflac0' -> 'target3.flac'：打开输出文件并写入
'source_rc4.mflac'：已打开文件，加密类型：QMCv2
'source_rc4.mflac' -> 'target4.flac'：打开输出文件并写入
'source_unsupported_keyformat.mflac'：无法根据文件名探测加密类型，切换到根据内容探测
'source_unsupported_keyformat.mflac'：仍然无法探测到加密类型，尝试使用 QMCv2 后备方案
'source_unsupported_keyformat.mflac'：已打开文件，加密类型：QMCv2
'source_unsupported_keyformat.mflac' -> 'target5.flac'：打开输出文件并写入
'is_ncm.unknown'：无法根据文件名探测加密类型，切换到根据内容探测
'is_ncm.unknown'：已打开文件，加密类型：NCM
'is_ncm.unknown' -> 'target6.flac'：打开输出文件并写入
'source_no_encrypted.flac'：无法根据文件名探测加密类型，切换到根据内容探测
'source_no_encrypted.flac'：仍然无法探测到加密类型，尝试使用 QMCv2 后备方案
'source_no_encrypted.flac'：跳过，非已知加密格式
```

验证输出文件：

```sh-session
target0.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 12560268 samples
target1.flac: FLAC audio bitstream data, 24 bit, stereo, 96 kHz, 19664640 samples
target2.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 10584000 samples
target3.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 6718488 samples
target4.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 11802924 samples
target5.flac: FLAC audio bitstream data, 24 bit, stereo, 44.1 kHz, 11862915 samples
```
