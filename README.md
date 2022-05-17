# Takiyasha ![](https://img.shields.io/badge/Python-3.8+-blue)

Takiyasha 是一个用来解密多种加密音乐文件的工具。

[Github](https://github.com/nukemiko/takiyasha/tree/remaked) | [Notabug](https://notabug.org/MiketsuSmasher/takiyasha/src/remaked)

**本项目是以学习和技术研究的初衷创建的，修改、再分发时请遵循 [License](https://github.com/nukemiko/takiyasha/blob/remaked/LICENSE)。**

Takiyasha 的设计灵感，以及部分解密方案，来源于 [Unlock Music Project - CLI Edition](https://github.com/unlock-music/cli)。

## 特性

- 跨平台：使用 Python 3 编写，只要系统中存在 Python 3.8 及以上环境，以及任意包管理器，就能安装并使用
- 支持多种加密音乐文件格式，[点击此处查看详情](#supported_formats)
- 对于开发者：
    - 完善的文档
    - 可任意读写已打开的加密音乐文件

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

### 从 Pypi 安装（推荐）

执行命令：`pip install -U takiyasha`

### 从本仓库安装

由于此版本的代码位于一个分支上，此方法目前不可用。

### 安装最新发布版本

1. 进入[此页面](https://github.com/nukemiko/takiyasha/releases/latest)，下载最新版本
    - 如果要下载其他版本，请直接[前往发布页](https://github.com/nukemiko/takiyasha/releases)
2. 下载 Wheel 安装包（扩展名为 `.whl` 的文件）
3. 下载完毕后，执行命令：
    `pip install -U /path/to/package.whl`

## 如何使用

### 命令行环境

暂不支持。

### 作为 Python 库调用

一个简单的示例（请确保自己的屏幕足够宽）：

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
