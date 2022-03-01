# Takiyasha ![](https://img.shields.io/badge/python-3.8+-green)

Takiyasha 是用来解锁被加密的音乐文件的工具，支持多种加密格式。

**Takiyasha 项目是以学习和技术研究的初衷创建的，修改、再分发时请遵循 [License](https://github.com/nukemiko/takiyasha/blob/master/LICENSE)。**

Takiyasha 解锁部分加密格式文件的能力，来源于此项目：[Unlock Music Project - CLI Edition](https://github.com/unlock-music/cli)

如果你只想快点体验，[查看安装方法](#how_to_install)

也可以看看：[此项目位于 Notabug 上的备份](https://notabug.org/MiketsuSmasher/takiyasha)

## 特性

- Takiyasha 使用 Python 3 编写
- 只要电脑/手机上可以运行 Python 3 和使用 pip，就可以安装和使用 Takiyasha

### 支持的加密格式

- 请在安装后使用 `takiyasha --formats` 查看支持的加密格式。
    - 不支持 Apple Music/Spotify 等平台的加密格式

### 适用群体

- 经常批量下载和解锁加密格式的用户
- 不在乎解锁速度的用户
    - 受限于 Python 的语言特性，解锁过程很慢
- 想要研究算法和提升自己技术水平的开发者

## <span id="how_to_install">如何安装</span>

- 所需运行环境
    - Python 版本：大于或等于 3.8
- 所需依赖
    - Python 包：[click](https://pypi.org/project/click/) - 提供命令行界面
    - Python 包：[mutagen](https://pypi.org/project/mutagen/) - 向输出文件写入歌曲信息
    - Python 包：[pycryptodomex](https://pypi.org/project/pycryptodomex/) - 部分加密格式的解锁支持
    - Python 包：[requests](https://pypi.org/project/requests/) - 为缺失封面的已解锁文件下载封面

### （推荐）从 Pypi 安装

使用命令：`pip install -U takiyasha`

### 通过已发布的 wheel (.whl) 软件包文件安装

- [前往发布页面](https://github.com/nukemiko/takiyasha/releases)
- 找到你需要的版本
    - 当前的最新版本[在这里](https://github.com/nukemiko/takiyasha/releases/latest)
- 按照发布说明进行下载和安装

## 如何使用

### 命令行（CMD/Powershell/Terminal 等）

Takiyasha 提供了 3 个命令入口：
- `takiyasha`
- `unlocker`
- `takiyasha-unlocker`

它们只存在命令长度上的区别。

- 直接执行命令：
    - `takiyasha file1 file2 ...`
    - `unlocker file3 file4 ...`
- 直接运行模块：`python -m takiyasha file5 file6 ...`

无论怎样运行，都可以使用 `-h/--help` 选项获得更多帮助信息。

### 作为 Python 模块导入使用

1. 创建一个 Decoder 对象：

    ```python
    from takiyasha import new_decoder

    qmcflac_dec = new_decoder('test.qmcflac')
    mflac_dec = new_decoder('test.mflac')
    ncm_dec = new_decoder('test.ncm')
    noop_dec = new_decoder('test.kv2')  # “test.kv2”是扩展名为“kv2”的 mp3 文件

    print(qmcflac_dec, mflac_dec, ncm_dec, noop_dec, end='\n')
    ```

    输出:

    ```text
    <QMCFormatDecoder at 0x7fdbf2057760 name='test.qmcflac'>  # QMCv1 加密
    <QMCFormatDecoder at 0x7fdbf2ac1090 name='test.mflac'>  # QMCv2 加密
    <NCMFormatDecoder at 0x7fdbf15622f0 name='test.ncm'>  # NCM 加密
    <NoOperationDecoder at 0x7fdbf1563400 name='test.kv2'>  # 无需解锁操作
    ```

2. 执行解锁操作并保存到文件：

    ```python
    for idx, decoder in enumerate([qmcflac_dec, mflac_dec, ncm_dec, noop_dec]):
        audio_format = decoder.audio_format
        save_filename = f'test{idx}.{audio_format}'

        with open(save_filename, 'wb') as f:
            for block in decoder:
                f.write(block)

        print('Saved:', save_filename)
    ```

    输出：

    ```text
    Saved: test0.flac
    Saved: test1.flac
    Saved: test2.flac
    Saved: test3.mp3
    ```

    使用 `file` 命令验证输出文件是否正确：

    ```text
    > file test0.flac test1.flac test2.flac test3.mp3
    test0.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 13379940 samples
    test1.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 16585716 samples
    test2.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 10222154 samples
    test3.mp3:  Audio file with ID3 version 2.4.0, contains: MPEG ADTS, layer III, v1, 320 kbps, 44.1 kHz, Stereo
    ```

3. 针对一些内嵌封面等元数据的加密格式（例如 NCM），还可将其嵌入解锁后的文件：

    ```python
    from takiyasha import new_tag

    with open('text2.flac', 'rb') as ncmfile:
        tag = new_tag(ncm_decrypted_file)
        # 上文中的 NCMFormatDecoder 对象已经储存了找到的元数据
        tag.title = ncm_dec.music_title
        tag.artist = ncm_dec.music_artists
        tag.album = ncm_dec.music_album
        tag.comment = ncm_dec.music_identifier
        tag.cover = ncm_dec.music_cover_data

        ncm_decrypted_file.seek(0, 0)
        tag.save(ncm_decrypted_file)
    ```
