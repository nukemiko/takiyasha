# Takiyasha v0.3.3-2 ![](https://img.shields.io/badge/python-3.8+-green)

[简体中文](README.md) | English

The Takiyasha is an unlocker for DRM protected music file.

**This project was created with the intention of learning and technical research, please follow the [License](LICENSE) when modifying and redistributing.**

The QMC decryption is partly derived from this project: [Unlock Music 音乐解锁](https://github.com/unlock-music/unlock-music)

## Supported encryption format

- Old QMC encrypted files (.qmc*)
- New QMC encrypted files (.mflac/.mflac*/.mgg/.mgg*)
- QQ Music .tm files (.tm*)
- Moo Music format files (.bkc*)
- NCM files (.ncm)
- KGM files (.kgm/.kgma/.vpr)

## What kind of users are suitable to use Takiyasha?

- Users who frequently download and unlock encrypted formats in bulk
- Users who don't care about unlocking speed
    - Python is a slow unlocking process due to the nature of the language
- Developers who want to study algorithms and improve their skills

## Install

- Dependencies:

    - Python version: At least Python 3.8 or above

    - Required Python packages:
        - [click](https://pypi.org/project/click/) - CLI support
        - [mutagen](https://pypi.org/project/mutagen/) - Write metadata to audio file
        - [pycryptodomex](https://pypi.org/project/pycryptodomex/) - Decryption support

- Install Takiyasha from this repository:
    - `pip install -U git+https://github.com/nukemiko/takiyasha`

- Install Takiyasha from the Pypi:
    - `pip install -U takiyasha`

- Install Takiyasha via wheel (.whl) package:
    - [Go to the release page](https://github.com/nukemiko/takiyasha/releases).
    - Choose a version that you need.
    - And follow the instructions to install.

## Usage

Takiyasha provided 3 commands:
- `takiyasha`
- `unlocker`
- `takiyasha-unlocker`

They are only differ in the length of command.

### In the commandline (Terminal / CMD / Powershell, etc.)

- Directly execute the command: 
    - `takiyasha file1.qmcflac file2.mflac ...`
    - `unlocker file3.kgm file4.vpr ...`
- Run the module: `python -m takiyasha file5.mgg file6.ncm ...`

In any case, you can use the `-h/--help` option to get detailed help information.

### Import and use it as a python module

1. Create a Decrypter instance by file encryption type:

    ```python
    from takiyasha import new_decoder

    qmcflac_dec = new_decoder('test.qmcflac')
    mflac_dec = new_decoder('test.mflac')
    ncm_dec = new_decoder('test.ncm')
    noop_dec = new_decoder('test.kv2')  # “test.kv2” is a mp3 file with the extension name “kv2”

    print(qmcflac_dec, mflac_dec, ncm_dec, noop_dec)
    ```
    Output:
    ```
    <QMCFormatDecoder at 0x7fdbf2057760 name='test.qmcflac'>  # QMCv1 encrypted
    <QMCFormatDecoder at 0x7fdbf2ac1090 name='test.mflac'>  # QMCv2 encrypted
    <NCMFormatDecoder at 0x7fdbf15622f0 name='test.ncm'>  # NCM encrypted
    <NoOperationDecoder at 0x7fdbf1563400 name='test.kv2'>  # No work to do
    ```

2. Decrypt and save data to file:

    ```python
    for idx, decoder in enumerate([qmcflac_dec, mflac_dec, ncm_dec, noop_dec]):
        audio_format = decoder.audio_format
        save_filename = f'test{idx}.{audio_format}'

        with open(save_filename, 'wb') as f:
            for block in decoder:
                f.write(block)

        print('Saved:', save_filename)
    ```
    Output:
    ```
    Saved: test0.flac
    Saved: test1.flac
    Saved: test2.flac
    Saved: test3.mp3
    ```
    Use the shell command `file` to verify that the output file is correct:
    ```
    > file test0.flac test1.flac test2.flac
    test0.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 13379940 samples
    test1.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 16585716 samples
    test2.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 10222154 samples
    test3.mp3:  Audio file with ID3 version 2.4.0, contains: MPEG ADTS, layer III, v1, 320 kbps, 44.1 kHz, Stereo
    ```

3. For some encryption formats with embedded metadata (such as NCM), you can embed them to the unlocked file:

    ```python
    from takiyasha import new_tag

    with open('text2.flac', 'rb') as ncmfile:
        tag = new_tag(ncm_decrypted_file)
        # The NCMFormatDecoder object used above already stores the required metadata
        tag.title = ncm_dec.music_title
        tag.artist = ncm_dec.music_artists
        tag.album = ncm_dec.music_album
        tag.comment = ncm_dec.music_identifier
        tag.cover = ncm_dev.music_cover_data

        ncm_decrypted_file.seek(0, 0)
        tag.save(ncm_decrypted_file)
    ```
