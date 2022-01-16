# Takiyasha v0.2.0 ![](https://img.shields.io/badge/python-3.8+-green)

The Takiyasha is an unlocker for DRM protected music file.

The QMC decryption is partly derived from this project: [Unlock Music 音乐解锁](https://github.com/unlock-music/unlock-music)

## Supported encryption format

- NCM files (.ncm)
- QMCv1 files (.qmc*)
- QMCv2 files (.mflac/.mflac*/.mgg/.mgg*)
- Moo Music format files (.bkc*)

## Install

- Dependencies:

    - Python version: At least Python 3.8 or above

    - Required Python packages:
        - [click](https://pypi.org/project/click/) - CLI support
        - [mutagen](https://pypi.org/project/mutagen/) - Write metadata to audio file
        - [pycryptodomex](https://pypi.org/project/pycryptodomex/) - Decryption support

- Install Takiyasha from this repository: `pip install -U git+https://github.com/nukemiko/takiyasha`

    **WARNING: Existing repositories are in an unstable state of continuous updates, and the content of modules you download may become outdated at any time. If you need to use a certain version continuously, please select the version on the [release page](https://github.com/nukemiko/takiyasha/releases) and install it as follows.**

- Install Takiyasha via wheel (.whl) package: [Go to the release page](https://github.com/nukemiko/takiyasha/releases), choose a version, and follow the instructions to install.

## Usage

### In Terminal / CMD / Powershell

- Directly execute the command: `takiyasha [OPTIONS] [/PATH/TO/INPUT]...`
- Run the module: `python -m takiyasha [OPTIONS] [/PATH/TO/INPUT]...`

    ```
    Argument:
        [PATHS/TO/INPUT]          Paths to input file or directory.
    
    Options:
        -o, --output PATH         Path to output file or dir.  [default: (current directory)]
        -r, --recursive           Also unlock supported files in subdirectories
                                  during unlocking.  [default: False]
        -n, --without-metadata    Do not embed metadata found in the source file
                                  into the unlocked file.  [default: False]
        -q, --quiet               Don't print OK for each unlocked file.  [default: False]
        --exts, --supported-exts  Show supported file extensions and exit.
        -V, --version             Show the version information and exit.
        -h, --help                Show this message and exit.
    ```

### Import and use it as a python module

- General usage

    1. Create a Decrypter instance by file encryption type

        ```python
        from takiyasha import new_decrypter
        
        qmcflac_dec = new_decrypter('test.qmcflac')
        mflac_dec = new_decrypter('test.mflac')
        ncm_dec = new_decrypter('test.ncm')

        print(qmcflac_dec, mflac_dec, ncm_dec)
        ```
        Output:
        ```
        <takiyasha.algorithms.qmc.QMCDecrypter object at 0x7f013116f670>
        <takiyasha.algorithms.qmc.QMCDecrypter object at 0x7f01311c0b80>
        <takiyasha.algorithms.ncm.NCMDecrypter object at 0x7f01311c0fd0>
        ```

    2. Decrypt and save data to file

        ```python
        for idx, decrypter in enumerate([qmcflac_dec, mflac_dec, ncm_dec]):
            audio_format = decrypter.audio_format
            save_filename = f'test{idx}.{audio_format}'

            with open(save_filename, 'wb') as f:
                decrypter.reset_buffer_offset()
                f.write(decrypter.read())

                print(save_filename)
        ```
        Output:
        ```
        test0.flac
        test1.flac
        test2.flac
        ```
        Use the shell command `file` to verify that the output file is correct:
        ```
        > file test0.flac test1.flac test2.flac
        test0.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 14232044 samples
        test1.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 11501280 samples
        test2.flac: FLAC audio bitstream data, 16 bit, stereo, 44.1 kHz, 9907800 samples
        ```
