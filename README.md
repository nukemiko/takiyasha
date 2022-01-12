# Takiyasha

The Takiyasha is an unlocker for DRM protected music file.

The QMC decryption is partly derived from this project: [Unlock Music 音乐解锁](https://github.com/unlock-music/unlock-music)

## Supported encryption format

- NCM (.ncm) file
- QMCv1 (.qmc0/.qmc2/.qmc3/.qmcflac/.qmcogg)
- QMCv2 (.mflac/.mgg/.mflac0/.mgg1/.mggl)
- Some files that require your luck
    - Moo Music format (.bkcmp3/.bkcflac/...)
    - QQMusic Tm format (.tm0/.tm2/.tm3/.tm6)
    - QQMusic oversea / JOOX Music (.ofl_en)

## Usage

### CLI

*Not implemented, coming soon*

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

- Install as a module using pip: `pip install git+https://github.com/nukemiko/takiyasha`
    - **Warning: Existing repositories are in an unstable state of continuous updates, and the content of modules you download may become outdated at any time.**
