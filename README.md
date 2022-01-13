# Takiyasha ![](https://img.shields.io/badge/python-3.8+-green)

The Takiyasha is an unlocker for DRM protected music file.

The QMC decryption is partly derived from this project: [Unlock Music 音乐解锁](https://github.com/unlock-music/unlock-music)

## Supported encryption format

- NCM files (.ncm)
- QMCv1 files (.qmc*)
- QMCv2 files (.mflac/.mflac*/.mgg/.mgg*)
- Moo Music format files (.bkc*)

## Usage

### CLI

- Directly execute the module with `python -m`:

  **WARNING: The command line has no function now. Please wait for future updates.**
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

```python
import io

from takiyasha.algorithms.ncm import NCMDecrypter
from takiyasha.algorithms.qmc import QMCDecrypter
from takiyasha.metadata import embed_metadata

# Decrypt a .qmcflac or .mflac file
origin_file_names = ['test.qmcflac', 'test.mflac']
origin_files = [open(name, 'rb') for name in origin_file_names]

for file in origin_files:
    qmc_decrypter = QMCDecrypter.generate(file)
    audiofmt = qmc_decrypter.audio_format  # In these cases, audio format is 'flac'
    # Calculate the time required to decrypt data
    # of the test_size specified size - default is 1048576.
    decrypt_speed = qmc_decrypter.speedtest()
    
    target_file = open('test.' + audiofmt, 'wb')
    decrypted_data = qmc_decrypter.decrypt()  # Directly obtain the audio data
    qmc_decrypter.decrypt(write_to=target_file)  # Write audio data to specified file object

# Decrypt a .ncm file
origin_file = open('test.ncm', 'rb')

ncm_decrypter = NCMDecrypter.generate(origin_file)
audiofmt = ncm_decrypter.audio_format

target_buffer = io.BytesIO()
ncm_decrypter.decrypt(write_to=target_buffer)  # Write audio data to specified file object

# Embed tags for the decrypted data (use NCM decrypted data as the example)
metadata = {
    'title': ncm_decrypter.metadata['musicName'],
    'artist': ncm_decrypter.metadata['artist'][0][0],
    'album': ncm_decrypter.metadata['album'],
    'cover_data': ncm_decrypter.cover_data
}
embed_metadata(target_buffer, **metadata)
with open('test.' + audiofmt, 'wb') as f:
    f.write(target_buffer.read())
```

## Install

- **Required Python interpreter version: 3.8+**

- Dependencies:
    - [click](https://pypi.org/project/click/) - CLI support
    - [mutagen](https://pypi.org/project/mutagen/) - Write metadata to audio file
    - [pycryptodomex](https://pypi.org/project/pycryptodomex/) - Decryption support

- Install as a module using pip: `pip install git+https://github.com/nukemiko/takiyasha`
    - **Warning: Existing repositories are in an unstable state of continuous updates, and the content of modules you download may become outdated at any time.**
