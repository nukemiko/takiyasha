# Takiyasha ![](https://img.shields.io/badge/Python-3.8+-red)

Takiyasha 是一个用来解密多种加密音乐文件的命令行工具，相当于 [LibTakiyasha](https://github.com/nukemiko/libtakiyasha) 的前端。

**本项目是以学习和技术研究的初衷创建的，修改、再分发时请遵循 [License](LICENSE)。**

**Takiyasha 对输出数据的可用性（是否可以识别、播放等）不做任何保证。**

## 各个版本的变化

### （当前）版本 1.0.0

从此版本开始：

-   **解密不再是开箱即用的。你需要根据提示，提供正确的解密所需的密钥。**
    -   要输入密钥，你需要按照特定的格式，输入对应的命令行选项或设置对应的环境变量；也可以将密钥写入配置文件，一次配置，长期使用。
    -   到哪里寻找密钥？
        -   如果加密文件是你自己制造的，你自己应该知道密钥；
        -   否则，请从内容提供者处获取，或者在它们的应用程序中寻找，或者寻求同类项目和他人的帮助。（作者是不会向你直接提供此类密钥的）
-   并行任务模式的运行方式可能会产生变化（多进程 -> 异步？）
-   对使用 V2 密钥加密的 QMCv2 加密文件的支持，这类文件通常来源于版本 18.57 及之后的 QQ 音乐 PC 客户端

本 README 后续所有内容都是基于此版本的。

### [版本 0.7.0](https://github.com/nukemiko/takiyasha/releases/tag/0.7.0)

从此版本开始：

-   命令行部分和算法部分分离得更为彻底：
    -   此仓库仅存储命令行部分 `takiyasha`；
    -   [算法部分 `libtakiyasha`](https://github.com/nukemiko/libtakiyasha) 存储在一个独立仓库中，作为 `takiaysha` 包的依赖存在。

### [版本 v0.6.1](https://github.com/nukemiko/takiyasha/releases/tag/v0.6.1-1)

从此版本开始：

-   直到 [v0.6.3](https://github.com/nukemiko/takiyasha/releases/tag/v0.6.3)，命令行部分和算法部分被拆分为 2 个模块：`takiyasha` 和 `libtakiyasha`，但仍然存在于同一个包内，可以同时安装。

### [版本 v0.6.0.dev1](https://github.com/nukemiko/takiyasha/releases/tag/v0.6.0.dev1)

从此版本开始，直到 v0.6.0.dev5，相较于 v0.4.2，包的结构、行为、命令行调用等已经发生了翻天覆地的变化。

关于这些变化的详细信息，请参见[此处](https://github.com/nukemiko/takiyasha/releases/tag/v0.6.0.dev1)。

## 特性

-   跨平台：使用 Python 3 编写，只要系统中存在 Python 3.8 及以上环境，以及任意包管理器，就能安装并使用
-   [x] <span id="supported_formats">支持的加密音乐文件格式</span>：
    -   QQ 音乐加密文件 `.qmc*`、`.mflac*`、`.mgg*`
        -   为以下加密文件提供部分支持，但不保证能成功解密：
            -   从版本 11.5.5 及之后的 QQ 音乐 Android 客户端下载的 `.mflac*`/`.mgg*` 文件
    -   网易云音乐加密文件 `.ncm`
    -   酷我音乐加密文件 `.kwm`
    -   酷狗音乐加密文件 `.kgm`、`.vpr`
-   [x] 命令行调用方式
-   [x] 自动根据文件内容探测文件的加密类型
-   [x] 多文件并行处理
-   [ ] 自动补充解密后文件的标签信息（包括封面）

## 如何安装

Python 版本需求：大于等于 3.8

需要的依赖项：

-   [colorama](https://pypi.org/project/colorama) - 命令行输出中的颜色
-   [requests](https://pypi.org/project/requests) - 网络请求库，用于检查更新
-   [libtakiaysha](https://pypi.org/project/libtakiyasha) - Takiaysha 的算法部分

### 从 PyPI 安装

~~执行命令：`pip install -U takiyasha`~~

此分支的版本尚未在 PyPI 上发布。

### 从本分支安装

执行命令：`pip install -U git+https://github.com/nukemiko/takiyasha@1.x`

安装的版本取决于安装时本分支的状态。

### 从本仓库下载和安装已发布版本

_暂无_

## 如何使用

### 命令行环境

_暂无_

## 常见问题

_未完待续_
