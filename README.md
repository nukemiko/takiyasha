# Takiyasha ![](https://img.shields.io/badge/Python-3.8+-red)

Takiyasha 是一个用来解密多种加密音乐文件的工具。

[Github](https://github.com/nukemiko/takiyasha) | [Notabug](https://notabug.org/MiketsuSmasher/takiyasha)

**本项目是以学习和技术研究的初衷创建的，修改、再分发时请遵循 [License](https://github.com/nukemiko/takiyasha/blob/master/LICENSE)。**

Takiyasha 的设计灵感，以及部分解密方案，来源于 [Unlock Music Project - CLI Edition](https://github.com/unlock-music/cli)。

**Takiyasha 对输出数据的可用性（是否可以识别、播放等）不做任何保证。**

## 重要事项

在 v0.4.2 之后的版本中，包的结构、行为、命令行调用等已经发生了翻天覆地的变化。

如果你曾针对 v0.4.2 或者之前的版本制作过脚本或工具，那么它们已经不再适用于当前版本（v0.6.0.dev1 及之后）。

如果你有使用 v0.4.2 的需求，按照以下步骤回滚：

1. 卸载：`pip uninstall takiyasha`
2. 安装 v0.4.2：`pip install -U takiyasha==0.4.2`

## 特性

- 跨平台：使用 Python 3 编写，只要系统中存在 Python 3.8 及以上环境，以及任意包管理器，就能安装并使用
- [x] <span id="supported_formats">支持的加密音乐文件格式</span>：
    - QQ 音乐
        - `.qmc*`
        - `.mflac*`
        - `.mgg*`
        - 为以下加密文件提供部分支持，但不保证能成功解密：
            - 从版本 18.57 及之后的 QQ 音乐 PC 客户端下载的 `.mflac*`/`.mgg*` 文件
            - 从版本 11.5.5 及之后的 QQ 音乐 Android 客户端下载的 `.mflac*`/`.mgg*` 文件
    - 网易云音乐
        - `.ncm`
        - `.uc!` （网易云音乐客户端的加密缓存文件）
- [x] 作为 Python 库使用时，针对主要功能，有完善的 docstring
- [x] 作为 Python 库使用时，支持解密和实验性的反向加密
- [x] 命令行调用方式（仅限解密，不支持反向加密）
- [x] 自动根据文件内容探测文件的加密类型
- [x] 基于多进程的多文件并行处理（默认行为）
- [x] 自动补充解密后文件的标签信息（包括封面）

## 如何安装

Python 版本需求：大于等于 3.8

需要的依赖项：

- [pyaes](https://pypi.org/project/pyaes) - AES 加解密支持
- [colorama](https://pypi.org/project/colorama) - 命令行输出中的颜色
- [mutagen](https://pypi.org/project/mutagen) - 为输出文件写入标签和封面
- [MusicTagFindUtils](https://pypi.org/project/MusicTagFindUtils) - 从网易云音乐和 QQ 音乐查找输出文件的标签信息和封面
    - 版本号必须大于等于 v0.1.2
- [requests](https://pypi.org/project/requests) - 网络请求库，用于下载封面信息

### 从 Pypi 安装（推荐）

执行命令：`pip install -U takiyasha`

### 从本仓库安装

执行命令：`pip install -U git+https://github.com/nukemiko/takiyasha`

### 从本仓库下载和安装已发布版本

1. 进入[此页面](https://github.com/nukemiko/takiyasha/releases/latest)，下载最新版本
    - 如果要下载其他版本（包括预发布版本），请直接前往[历史发布页面](https://github.com/nukemiko/takiyasha/releases)寻找和下载
2. 下载 Wheel 安装包（扩展名为 `.whl` 的文件）
3. 下载完毕后，执行命令：
    `pip install -U /path/to/package.whl`

## 如何使用

### 命令行环境

简单易用：

`takiyasha 1.ncm 2.qmcflac 3.mflac 4.mgg ...`

使用 `-t, --test`，只查看输入文件信息但不解密：

`takiyasha -vt 1.ncm 2.qmcflac 3.mflac 4.mgg ...`

使用 `-f, --try-fallback` 尝试解密“[仅部分支持](#supported_formats)”的文件：

`takiyasha -f hell.mflac damn.mgg`

如果不加其他参数，解密成功的文件将会在当前工作目录（`pwd` 或 `os.getcwd()` 的值）下产生。

使用 `-h, --help` 获取完整的帮助信息，或者参见[此处](https://github.com/nukemiko/takiyasha/wiki/%E5%9C%A8%E5%91%BD%E4%BB%A4%E8%A1%8C%E4%B8%AD%E4%BD%BF%E7%94%A8)。

如果你的终端（Shell/PowerShell/CMD 等）出现了以下报错，或其他类似错误信息：

（bash）`bash: takiyasha：未找到命令`

（zsh）`zsh: command not found: takiyasha`

（CMD）`'takiyasha' 不是内部或外部命令，也不是可运行的程序或批处理文件。`

（PowerShell）`takiyasha : 无法将“takiyasha”项识别为 cmdlet、函数、脚本文件或可运行程序的名称。请检查名称的拼写，如果包括路径，请确保路径正确，然后再试一次。`

请尝试改用 `python -m takiyasha`。

### 在其他项目中作为 Python 库导入使用

敬请参见 [Wiki 上的相关页面](https://github.com/nukemiko/takiyasha/wiki/%E5%9C%A8%E5%85%B6%E4%BB%96%E9%A1%B9%E7%9B%AE%E4%B8%AD%E4%BD%9C%E4%B8%BA-Python-%E5%BA%93%E5%AF%BC%E5%85%A5%E4%BD%BF%E7%94%A8)。

## 常见问题

敬请参见 [Wiki 上的相关页面](https://github.com/nukemiko/takiyasha/wiki/%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)。

碰上了不常见的问题？[前往 Issues 页面](https://github.com/nukemiko/takiyasha/issues)，查看是否存在相似问题，或者开一个 Issue。
