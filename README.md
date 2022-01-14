# Takiyasha ![](https://img.shields.io/badge/python-3.8+-green)

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

- Install as a module using pip: `pip install -U git+https://github.com/nukemiko/takiyasha`

    **WARNING: Existing repositories are in an unstable state of continuous updates, and the content of modules you download may become outdated at any time.**

## Usage

### CLI

- Directly execute the module with `python -m`:

    **WARNING: The command line has no function now, and the output need to update. Please wait for future version.**

    ```
    Usage: python -m takiyasha [OPTIONS] <PATHS TO INPUT...>
    
    Options:
      -o, --output <PATH>             Path to output file or dir.  [default: (current directory)]
      -r, --recursive                 If there is a directory in <PATHS TO
                                      INPUT...>, recursively process the supported
                                      files in the directory.
                                      
                                      Enabled by default when there is only one
                                      directory in <PATHS TO INPUT...>.  [default:
                                      (False)]
      --supported-exts, --supported-formats
                                      Show supported file extensions and exit.
      -V, --version
      -h, --help                      Show this message and exit.
    ```

### As a python module

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
